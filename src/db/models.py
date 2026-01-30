
from datetime import datetime
from typing import Literal, Any
from uuid import UUID

from pydantic import BaseModel, Field


class AllowedUser(BaseModel):
    """User whitelist entry."""

    telegram_id: int
    username: str | None = None
    is_active: bool = True


class UserSettings(BaseModel):
    """User preferences for AI interaction."""

    user_id: int
    selected_model: str = "gpt-5-mini"
    reasoning_effort: Literal["low", "medium", "high"] = "medium"


class ConversationState(BaseModel):
    """Ephemeral state for the conversation flow."""
    
    user_id: int
    pending_image_id: str | None = None
    updated_at: datetime | None = None


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    id: UUID | None = None
    user_id: int
    role: Literal["user", "assistant"]
    content: str
    image_data: str | None = None
    message_id: int | None = None
    created_at: datetime | None = None


class ChatHistory(BaseModel):
    """Collection of messages for context."""

    messages: list[ChatMessage] = Field(default_factory=list)
