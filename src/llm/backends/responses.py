
from typing import Any
from openai import OpenAI

class ResponsesBackend:
    """Backend for the experimental Responses API."""
    
    def __init__(self, client: OpenAI):
        self.client = client

    def generate(
        self,
        model: str,
        input_messages: list[dict[str, Any]],
        instructions: str,
        reasoning_effort: str | None = None,
        enable_web_search: bool = False,
        vector_store_id: str | None = None
    ) -> str:
        """Generate response using Responses API.
        
        Args:
            model: Model identifier.
            input_messages: List of messages in 'input_text'/'input_image' format.
            instructions: System instructions.
            reasoning_effort: Reasoning effort level if applicable.
            enable_web_search: Whether to enable web search tool.
            vector_store_id: ID of vector store for file search.
            
        Returns:
            Generated text content.
        """
        if not hasattr(self.client, 'responses'):
             raise AttributeError("OpenAI client does not support 'responses' API")
             
        params = {
            "model": model,
            "input": input_messages,
            "instructions": instructions,
        }
        
        # Configure Tools
        tools = []
        if enable_web_search:
            tools.append({"type": "web_search"})
            
        if vector_store_id:
            tools.append({
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            })
            
        if tools:
            params["tools"] = tools
            
        # Configure Reasoning
        if reasoning_effort:
            params["reasoning"] = {"effort": reasoning_effort}
            
        response = self.client.responses.create(**params)
        return response.output_text
