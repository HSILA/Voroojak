
from typing import Any
from uuid import UUID

from src.db.models import ChatHistory, ChatMessage


def to_responses_format(
    history: ChatHistory,
    current_message: str,
    image_base64: str | None = None
) -> list[dict[str, Any]]:
    """Convert chat history to OpenAI Responses API format (input_text/input_image)."""
    formatted_messages = []
    
    # Process history
    for msg in history.messages:
        content: Any = msg.content
        if msg.image_data:
            # Reconstruct multi-part message with vision
            content = [
                {"type": "input_text", "text": msg.content},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{msg.image_data}",
                },
            ]
            formatted_messages.append({"role": msg.role, "content": content})
        else:
            formatted_messages.append({"role": msg.role, "content": msg.content})
            
    # Append current message
    current_content: Any = current_message
    if image_base64:
        current_content = [
            {"type": "input_text", "text": current_message},
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{image_base64}",
            },
        ]
        formatted_messages.append({"role": "user", "content": current_content})
    else:
        formatted_messages.append({"role": "user", "content": current_message})
        
    return formatted_messages


def to_chat_completion_format(
    messages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Convert Responses API format messages to Standard Chat Completion format.
    
    Converts 'input_text' -> 'text' and 'input_image' -> 'image_url' (dict).
    """
    import copy
    
    standard_messages = []
    for msg in messages:
        msg_copy = copy.deepcopy(msg)
        content = msg_copy["content"]
        
        if isinstance(content, list):
            new_content = []
            for item in content:
                item_type = item.get("type")
                if item_type == "input_text":
                    new_content.append({
                        "type": "text", 
                        "text": item["text"]
                    })
                elif item_type == "input_image":
                    # Chat Completions expects image_url as a dict wrapper
                    new_content.append({
                        "type": "image_url",
                        "image_url": {"url": item["image_url"]} 
                    })
                else:
                    # Keep existing if already in correct format or unknown
                    new_content.append(item)
            msg_copy["content"] = new_content
            
        standard_messages.append(msg_copy)
        
    return standard_messages
