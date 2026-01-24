"""Database layer using Supabase."""

from .client import get_supabase_client
from .operations import (
    check_user_access,
    create_allowed_user,
    delete_chat_history,
    get_chat_history,
    get_user_settings,
    is_message_processed,
    save_message,
    update_user_settings,
)

__all__ = [
    "get_supabase_client",
    "check_user_access",
    "create_allowed_user",
    "get_user_settings",
    "update_user_settings",
    "get_chat_history",
    "is_message_processed",
    "save_message",
    "delete_chat_history",
]
