"""Telegram bot command and message handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from src.db import (
    check_user_access,
    delete_chat_history,
    get_chat_history,
    get_user_settings,
    is_message_processed,
    save_message,
    update_user_settings,
)
from src.services.openai_service import generate_response
from src.utils import markdown_to_telegram_html

from .keyboards import build_main_keyboard, build_newchat_keyboard, build_settings_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - check access and introduce the bot."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Check whitelist
    if not check_user_access(user_id):
        await update.message.reply_text(
            "⛔️ Sorry, you don't have access to this bot.\n\n"
            "This is a private bot. Contact the administrator for access."
        )
        return
    
    welcome_message = (
        f"🎯 <b>Welcome to Voroojak, @{username}!</b>\n\n"
        "I'm your AI assistant powered by OpenAI models.\n\n"
        "Use the buttons below or commands:\n"
        "• ⚙️ Settings - Change model & reasoning\n"
        "• ✨ New Chat - Clear conversation history\n\n"
        "Just send me a message to start chatting!"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="HTML",
        reply_markup=build_main_keyboard()
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command - display settings keyboard."""
    user_id = update.effective_user.id
    
    # Check access
    if not check_user_access(user_id):
        return
    
    # Get current settings
    settings = get_user_settings(user_id)
    
    message_text = (
        "⚙️ <b>Settings</b>\n\n"
        f"<b>Current Configuration:</b>\n"
        f"🤖 Model: <code>{settings.selected_model}</code>\n"
        f"🧠 Reasoning: <code>{settings.reasoning_effort}</code>"
    )
    
    keyboard = build_settings_keyboard(settings.selected_model, settings.reasoning_effort)
    
    await update.message.reply_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def newchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /newchat command - confirm before clearing history."""
    user_id = update.effective_user.id
    
    # Check access
    if not check_user_access(user_id):
        return
    
    keyboard = build_newchat_keyboard()
    
    await update.message.reply_text(
        "✨ <b>Start a fresh conversation?</b>\n\n"
        "This will clear your chat history. The bot won't have access to "
        "previous messages in the new session.\n\n"
        "💡 Your history is stored in the database, but won't be used for AI context.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks from inline keyboards."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Acknowledge the callback
    await query.answer()
    
    # Check access
    if not check_user_access(user_id):
        return
    
    # Parse callback data
    data = query.data
    
    if data == "noop":
        return
    
    elif data.startswith("model:"):
        model = data.split(":")[1]
        update_user_settings(user_id, selected_model=model)
        
        # Refresh keyboard & text
        settings = get_user_settings(user_id)
        keyboard = build_settings_keyboard(settings.selected_model, settings.reasoning_effort)
        
        await query.edit_message_text(
            f"✅ Model changed to <b>{model}</b>\n\n"
            "⚙️ <b>Settings</b>\n"
            f"🤖 Model: <code>{settings.selected_model}</code>\n"
            f"🧠 Reasoning: <code>{settings.reasoning_effort}</code>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif data.startswith("reasoning:"):
        level = data.split(":")[1]
        update_user_settings(user_id, reasoning_effort=level)
        
        # Refresh keyboard
        settings = get_user_settings(user_id)
        keyboard = build_settings_keyboard(settings.selected_model, settings.reasoning_effort)
        
        await query.edit_message_text(
            f"✅ Reasoning level changed to <b>{level}</b>\n\n"
            "⚙️ <b>Settings</b>\n"
            f"🤖 Model: <code>{settings.selected_model}</code>\n"
            f"🧠 Reasoning: <code>{settings.reasoning_effort}</code>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif data == "newchat:confirm":
        deleted_count = delete_chat_history(user_id)
        
        if deleted_count > 0:
            await query.edit_message_text(
                f"✅ <b>History cleared!</b>\n\n"
                f"Deleted {deleted_count} message{'s' if deleted_count != 1 else ''}.\n"
                f"You can now start a fresh conversation.",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                "✨ <b>Fresh start!</b>\n\n"
                "No previous history found. You're all set!",
                parse_mode="HTML"
            )
    
    elif data == "newchat:cancel":
        await query.edit_message_text("❌ Cancelled. Your chat history is preserved.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages - detect button clicks or send to AI."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Check access
    if not check_user_access(user_id):
        await update.message.reply_text(
            "⛔️ You don't have access to this bot."
        )
        return
    
    # Handle tile button clicks
    if user_message == "⚙️ Settings":
        await settings_command(update, context)
        return
    elif user_message == "✨ New Chat Session":
        await newchat_command(update, context)
        return
    
    # Send typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Check for duplicate messages (idempotency)
        message_id = update.message.message_id
        if is_message_processed(user_id, message_id):
            print(f"Skipping duplicate message {message_id} for user {user_id}")
            return
            
        # Get user settings
        settings = get_user_settings(user_id)
        
        # Get history BEFORE saving new message to avoid context duplication
        history = get_chat_history(user_id, limit=20)
        
        # Save user message immediately to mark as processed
        save_message(user_id, "user", user_message, message_id=message_id)
        
        # Generate AI response (Now in standard Markdown)
        ai_response = generate_response(history, user_message, settings)
        
        # Save assistant response
        save_message(user_id, "assistant", ai_response)
        
        # Convert Markdown -> Telegram HTML
        # This handles **bold**, [links], list items, etc. reliably
        html_response = markdown_to_telegram_html(ai_response)
        
        # Send response with HTML parse mode
        try:
            await update.message.reply_text(html_response, parse_mode="HTML")
        except Exception as e:
            # If conversion or parsing fails (edge case), fallback to plain text
            print(f"HTML send failed: {e}")
            await update.message.reply_text(ai_response) # Send raw text
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error generating response:\n\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )
