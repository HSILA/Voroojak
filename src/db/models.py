"""Pydantic models for database entities."""

from datetime import datetime
from typing import Literal
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


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    id: UUID | None = None
    user_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime | None = None


class ChatHistory(BaseModel):
    """Collection of messages for context."""

    messages: list[ChatMessage] = Field(default_factory=list)

    def to_openai_format(self) -> list[dict[str, str]]:
        """Convert to OpenAI API message format."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
