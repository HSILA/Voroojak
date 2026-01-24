"""OpenAI service for chat completions using the new Responses API."""

from openai import OpenAI, BadRequestError

from src.config import settings
from src.db.models import ChatHistory, UserSettings

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)

# Models that support reasoning_effort parameter
REASONING_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini"}

# Models that support web search tool
WEB_SEARCH_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini", "gpt-4.1"}


def generate_response(
    history: ChatHistory,
    user_message: str,
    user_settings: UserSettings,
) -> str:
    """Generate a response from OpenAI based on conversation history.
    
    Args:
        history: Previous conversation context.
        user_message: New message from the user.
        user_settings: User's model and reasoning preferences.
        
    Returns:
        Generated response text.
    """
    # Build input messages array (history + new message)
    messages = history.to_openai_format()
    messages.append({"role": "user", "content": user_message})
    
    # Get current date for temporal context
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Standard system instructions - Managed to be cost-effective
    instructions = (
        f"You are a helpful Telegram bot. Today's date is {current_date}. "
        "You can use standard Markdown for formatting such as **bold**, *italic*, `code`, and [links](url).\n\n"
        "CRITICAL TOOL USAGE RULES:\n"
        "1. ONLY use the 'web_search' tool if the user explicitly asks you to search the web, "
        "get latest info, or find live data.\n"
        "2. If a user asks about something outside your knowledge cutoff but does NOT explicitly "
        "request a search, DO NOT search automatically. Instead, inform the user about your "
        "cutoff and ASK if they would like you to perform a web search.\n"
        "3. Be concise and cost-efficient."
    )
    
    # Base parameters for Responses API
    params = {
        "model": user_settings.selected_model,
        "input": messages,
        "instructions": instructions,
        "tools": [{"type": "web_search"}]  # Enable native web search for ALL models
    }
    
    # Add reasoning_effort ONLY for models that support it
    if user_settings.selected_model in REASONING_MODELS:
        # Responses API uses a 'reasoning' dictionary
        params["reasoning"] = {"effort": user_settings.reasoning_effort}
    
    try:
        # Try using the newer Responses API (native search support)
        if hasattr(client, 'responses'):
            response = client.responses.create(**params)
            return response.output_text
            
        else:
            # Fallback for older SDKs
            print("⚠️ Responses API not found, falling back to Chat Completions.")
            raise AttributeError("Responses API missing")

    except (BadRequestError, AttributeError) as e:
        print(f"⚠️ Responses API failed ({e}), falling back to Chat Completions without search.")
        
        # Fallback to standard Chat Completions (No Web Search)
        # We must re-format arguments: 'input' -> 'messages', 'instructions' -> system message
        fallback_messages = [{"role": "system", "content": instructions}] + messages
        
        chat_params = {
            "model": user_settings.selected_model,
            "messages": fallback_messages,
        }
        
        if user_settings.selected_model in REASONING_MODELS:
            chat_params["reasoning_effort"] = user_settings.reasoning_effort
            
        response = client.chat.completions.create(**chat_params)
        return response.choices[0].message.content
