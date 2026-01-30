
from typing import Any
from openai import OpenAI
from openai.types.chat import ChatCompletion

class ChatCompletionBackend:
    """Backend for standard Chat Completions API."""
    
    def __init__(self, client: OpenAI):
        self.client = client

    def generate(
        self,
        model: str,
        messages: list[dict[str, Any]],
        reasoning_effort: str | None = None,
        supports_reasoning: bool = False
    ) -> str:
        """Generate response using Chat Completions API.
        
        Args:
            model: Model identifier.
            messages: List of messages in standard format.
            reasoning_effort: 'low', 'medium', 'high', or None.
            supports_reasoning: Whether the model supports the reasoning_effort param.
            
        Returns:
            Generated text content.
        """
        params = {
            "model": model,
            "messages": messages,
        }
        
        # Add reasoning_effort only if supported/requested
        if supports_reasoning and reasoning_effort:
            params["reasoning_effort"] = reasoning_effort
            
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content or ""
