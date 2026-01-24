"""Database operations using Supabase client."""

from .client import get_supabase_client
from .models import AllowedUser, ChatHistory, ChatMessage, UserSettings


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


def get_chat_history(user_id: int, limit: int = 20) -> ChatHistory:
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
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    messages = [ChatMessage(**msg) for msg in response.data]
    return ChatHistory(messages=messages)


def save_message(user_id: int, role: str, content: str) -> ChatMessage:
    """Save a message to chat history.
    
    Args:
        user_id: Telegram user ID.
        role: Message role ('user' or 'assistant').
        content: Message text content.
        
    Returns:
        Saved message record.
    """
    client = get_supabase_client()
    data = {"user_id": user_id, "role": role, "content": content}
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
