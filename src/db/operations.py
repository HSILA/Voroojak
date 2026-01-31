
from datetime import datetime, timedelta, timezone
from typing import Literal

from .client import get_supabase_client
from .models import AllowedUser, ChatHistory, ChatMessage, UserSettings

# Time in minutes before a pending image is considered "stale" and ignored
PENDING_IMAGE_TIMEOUT_MINUTES = 60


def check_user_access(telegram_id: int) -> bool:
    """Check if user is whitelisted and active.
    
    Args:
        telegram_id: Telegram user ID to check.
        
    Returns:
        True if user has access, False otherwise.
    """
    client = get_supabase_client()
    response = (
        client.table("allowed_users")
        .select("telegram_id")
        .eq("telegram_id", telegram_id)
        .eq("is_active", True)
        .execute()
    )
    return len(response.data) > 0


def create_allowed_user(telegram_id: int, username: str | None = None) -> AllowedUser:
    """Add a user to the whitelist.
    
    Args:
        telegram_id: Telegram user ID.
        username: Optional Telegram username.
        
    Returns:
        Created user record.
    """
    client = get_supabase_client()
    data = {"telegram_id": telegram_id, "username": username, "is_active": True}
    response = client.table("allowed_users").insert(data).execute()
    return AllowedUser(**response.data[0])


def get_user_settings(user_id: int) -> UserSettings:
    """Get user settings, creating defaults if not exists.
    
    Args:
        user_id: Telegram user ID.
        
    Returns:
        User settings object.
    """
    client = get_supabase_client()
    response = client.table("user_settings").select("*").eq("user_id", user_id).execute()

    if response.data:
        return UserSettings(**response.data[0])

    # Create default settings
    # Create default settings
    default_settings = {"user_id": user_id, "selected_model": "gpt-5-mini", "reasoning_effort": "medium"}
    response = client.table("user_settings").insert(default_settings).execute()
    return UserSettings(**response.data[0])


def update_user_settings(
    user_id: int, selected_model: str | None = None, reasoning_effort: str | None = None
) -> UserSettings:
    """Update user settings.
    
    Args:
        user_id: Telegram user ID.
        selected_model: New model selection (optional).
        reasoning_effort: New reasoning level (optional).
        
    Returns:
        Updated settings.
    """
    client = get_supabase_client()
    updates = {}
    if selected_model:
        updates["selected_model"] = selected_model
    if reasoning_effort:
        updates["reasoning_effort"] = reasoning_effort

    response = (
        client.table("user_settings").update(updates).eq("user_id", user_id).execute()
    )
    return UserSettings(**response.data[0])


def set_pending_image(user_id: int, file_id: str) -> None:
    """Set a pending image for the user's conversation state."""
    client = get_supabase_client()
    
    # Check if row exists to preserve other fields
    existing = client.table("conversation_state").select("*").eq("user_id", user_id).execute()
    
    data = {"user_id": user_id, "pending_image_id": file_id, "updated_at": "now()"}
    
    # If exists, merge (though upsert with ignore_duplicates=False usually works if we provide all keys, 
    # but here we might only provide partial updates if we aren't careful. 
    # To be safe, we just upsert. If active_vector_store_id exists, it might be overwritten if we don't include it.
    if existing.data:
        # Preserve existing active_vector_store_id
        current = existing.data[0]
        if current.get("active_vector_store_id"):
            data["active_vector_store_id"] = current["active_vector_store_id"]

    client.table("conversation_state").upsert(data).execute()


def get_pending_image(user_id: int) -> str | None:
    """Get pending image ID if exists and is recent (< 60 mins)."""
    client = get_supabase_client()
    
    response = (
        client.table("conversation_state")
        .select("pending_image_id, updated_at")
        .eq("user_id", user_id)
        .execute()
    )
    
    if not response.data:
        return None
    
    row = response.data[0]
    pending_id = row.get("pending_image_id")
    updated_at_str = row.get("updated_at")
    
    if not pending_id or not updated_at_str:
        return None
        
    # Check for expiration
    try:
        # Supabase returns ISO strings
        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
        
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        time_diff = datetime.now(timezone.utc) - updated_at
        
        if time_diff > timedelta(minutes=PENDING_IMAGE_TIMEOUT_MINUTES):
            # Too old! Clean it up
            clear_pending_image(user_id)
            return None
            
    except ValueError:
        return None
        
    return pending_id


def clear_pending_image(user_id: int) -> None:
    """Clear the pending image state."""
    client = get_supabase_client()
    # Update to None instead of delete to preserve vector_store_id
    client.table("conversation_state").update({"pending_image_id": None}).eq("user_id", user_id).execute()


def set_active_vector_store(user_id: int, vector_store_id: str | None) -> None:
    """Set the active vector store for the user."""
    client = get_supabase_client()
    
    # Fetch existing to preserve pending_image_id
    existing = client.table("conversation_state").select("*").eq("user_id", user_id).execute()
    data = {"user_id": user_id, "active_vector_store_id": vector_store_id, "updated_at": "now()"}
    
    if existing.data:
        current = existing.data[0]
        if current.get("pending_image_id"):
            data["pending_image_id"] = current["pending_image_id"]
            
    client.table("conversation_state").upsert(data).execute()


def get_active_vector_store(user_id: int) -> str | None:
    """Get the active vector store ID."""
    client = get_supabase_client()
    response = (
        client.table("conversation_state")
        .select("active_vector_store_id")
        .eq("user_id", user_id)
        .execute()
    )
    if response.data and response.data[0].get("active_vector_store_id"):
        return response.data[0]["active_vector_store_id"]
    return None


def get_chat_history(user_id: int, limit: int = 30) -> ChatHistory:
    """Retrieve recent chat history for context.
    
    Args:
        user_id: Telegram user ID.
        limit: Maximum number of messages to retrieve.
        
    Returns:
        Chat history object.
    """
    client = get_supabase_client()
    response = (
        client.table("chat_history")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    # Reverse to restore chronological order (oldest to newest)
    history_data = list(reversed(response.data))
    messages = [ChatMessage(**msg) for msg in history_data]
    return ChatHistory(messages=messages)


def is_message_processed(user_id: int, message_id: int) -> bool:
    """Check if a message has already been processed.
    
    Args:
        user_id: Telegram user ID.
        message_id: Telegram message ID.
        
    Returns:
        True if message exists, False otherwise.
    """
    client = get_supabase_client()
    response = (
        client.table("chat_history")
        .select("id")
        .eq("user_id", user_id)
        .eq("message_id", message_id)
        .execute()
    )
    return len(response.data) > 0


def save_message(
    user_id: int, 
    role: str, 
    content: str, 
    message_id: int | None = None,
    image_data: str | None = None
) -> ChatMessage:
    """Save a message to chat history.
    
    Args:
        user_id: Telegram user ID.
        role: Message role ('user' or 'assistant').
        content: Message text content.
        message_id: Optional Telegram message ID for deduplication (only for user messages).
        image_data: Optional Base64 image data to persist.
        
    Returns:
        Saved message record.
    """
    client = get_supabase_client()
    data = {"user_id": user_id, "role": role, "content": content}
    if message_id is not None:
        data["message_id"] = message_id
    if image_data is not None:
        data["image_data"] = image_data
        
    response = client.table("chat_history").insert(data).execute()
    return ChatMessage(**response.data[0])


def delete_chat_history(user_id: int) -> int:
    """Clear all chat history for a user.
    
    Args:
        user_id: Telegram user ID.
        
    Returns:
        Number of deleted records.
    """
    client = get_supabase_client()
    response = client.table("chat_history").delete().eq("user_id", user_id).execute()
    return len(response.data)
