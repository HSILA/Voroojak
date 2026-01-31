
from datetime import datetime
from openai import OpenAI
from src.config import settings
from src.db.models import ChatHistory, UserSettings

from .formatters import to_responses_format, to_chat_completion_format
from .backends.responses import ResponsesBackend
from .backends.chat_completion import ChatCompletionBackend


# Configuration
REASONING_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini"}
WEB_SEARCH_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini", "gpt-4.1"}

class LLMEngine:
    """Orchestrates LLM calls, handling routing, formatting, and fallbacks."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self._responses_backend = ResponsesBackend(self.client)
        self._chat_backend = ChatCompletionBackend(self.client)

    def generate_response(
        self,
        history: ChatHistory,
        user_message: str,
        user_settings: UserSettings,
        image_base64: str | None = None,
    ) -> str:
        """High-level method to generate a response for a user chat session.
        
        Handles:
        1. Context Formatting
        2. System Instructions
        3. Backend Selection (Responses API vs Standard)
        4. Fallback Logic
        """
        
        # 1. Prepare Base Context (Responses Format)
        messages_responses_fmt = to_responses_format(history, user_message, image_base64)
        
        # 2. Prepare System Instructions
        current_date = datetime.now().strftime("%Y-%m-%d")
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

        model = user_settings.selected_model
        reasoning_effort = user_settings.reasoning_effort if model in REASONING_MODELS else None
        
        # 3. Execution
        try:
            return self._responses_backend.generate(
                model=model,
                input_messages=messages_responses_fmt,
                instructions=instructions,
                reasoning_effort=reasoning_effort,
                enable_web_search=(model in WEB_SEARCH_MODELS)
            )
        except Exception as e:
            return f"System Error: {str(e)}"
    
    def generate_simple(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """Simple generation helper for internal tasks (e.g. titling)."""
        return self._chat_backend.generate(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )

# Global Instance
engine = LLMEngine()
