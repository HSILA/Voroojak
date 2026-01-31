
from src.db.models import ChatHistory, UserSettings
from src.llm.engine import engine

# Re-export constants for compatibility if needed, though they are now in engine
REASONING_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini"}
WEB_SEARCH_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini", "gpt-4.1"}

# Provide direct access to the client object for rare cases where raw access is needed
client = engine.client 

def generate_response(
    history: ChatHistory,
    user_message: str,
    user_settings: UserSettings,
    image_base64: str | None = None,
    vector_store_id: str | None = None,
) -> str:
    """Generate a response using the centralized LLM Engine.
    
    Args:
        history: Previous conversation context.
        user_message: New message from the user.
        user_settings: User's model and reasoning preferences.
        image_base64: Optional base64-encoded image data.
        vector_store_id: Optional vector store for file search.
        
    Returns:
        Generated response text.
    """
    return engine.generate_response(
        history=history,
        user_message=user_message,
        user_settings=user_settings,
        image_base64=image_base64,
        vector_store_id=vector_store_id
    )
