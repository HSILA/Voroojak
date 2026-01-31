
import base64

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
    set_pending_image,
    get_pending_image,
    clear_pending_image,
    get_active_vector_store,
    set_active_vector_store,
)
from src.services.file_service import create_vector_store_from_file
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
        
        # Validation: gpt-5.2-chat-latest does not support "high" reasoning
        # If user switches to this model while on "high", auto-downgrade to "medium"
        current_settings = get_user_settings(user_id)
        msg_extra = ""
        
        if model == "gpt-5.2-chat-latest" and current_settings.reasoning_effort == "high":
            update_user_settings(user_id, selected_model=model, reasoning_effort="medium")
            msg_extra = "\n⚠️ <i>Reasoning set to medium (High not supported)</i>"
        else:
            update_user_settings(user_id, selected_model=model)
        
        # Refresh keyboard & text
        settings = get_user_settings(user_id)
        keyboard = build_settings_keyboard(settings.selected_model, settings.reasoning_effort)
        
        await query.edit_message_text(
            f"✅ Model changed to <b>{model}</b>{msg_extra}\n\n"
            "⚙️ <b>Settings</b>\n"
            f"🤖 Model: <code>{settings.selected_model}</code>\n"
            f"🧠 Reasoning: <code>{settings.reasoning_effort}</code>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif data.startswith("reasoning:"):
        level = data.split(":")[1]
        settings = get_user_settings(user_id)
        
        update_user_settings(user_id, reasoning_effort=level)
        
        # Refresh keyboard
        # Re-fetch settings after update
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
        try:
            deleted_count = delete_chat_history(user_id)
            # Clear document context
            set_active_vector_store(user_id, None)
            
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
        except Exception as e:
            print(f"Error in newchat:confirm: {e}")
            await query.edit_message_text(
                f"❌ Error clearing history: {e}",
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
        
        image_base64 = None
        
        # Check for pending detached image
        pending_image_id = get_pending_image(user_id)
        if pending_image_id:
            try:
                # Retrieve and download the pending image
                file = await context.bot.get_file(pending_image_id)
                photo_bytes = await file.download_as_bytearray()
                image_base64 = base64.b64encode(photo_bytes).decode("utf-8")
                
                # Clear pending image state
                clear_pending_image(user_id)
                
            except Exception as e:
                print(f"Failed to retrieve pending image: {e}")
                # Log error but continue with text only
        
        # Check for active file context (vector store)
        vector_store_id = get_active_vector_store(user_id)
        
        # Get history BEFORE saving new message to avoid context duplication
        history = get_chat_history(user_id, limit=30)
        
        # Save user message immediately to mark as processed
        # If we attached an image, mark it in the text for history context
        log_content = f"[📷 Attached Image] {user_message}" if image_base64 else user_message
        if vector_store_id:
             log_content += " [📄 File Context Active]"
        
        save_message(user_id, "user", log_content, message_id=message_id, image_data=image_base64)
        
        # Generate AI response (Now in standard Markdown)
        ai_response = generate_response(
            history, 
            user_message, 
            settings, 
            image_base64=image_base64,
            vector_store_id=vector_store_id
        )
        
        # Save assistant response
        save_message(user_id, "assistant", ai_response)
        
        # Convert Markdown -> Telegram HTML
        html_response = markdown_to_telegram_html(ai_response)
        
        # Helper to send message (handles retry/fallback)
        async def _send_chunk(text_chunk, as_html=True):
            try:
                if as_html:
                    await update.message.reply_text(markdown_to_telegram_html(text_chunk), parse_mode="HTML")
                else:
                    await update.message.reply_text(text_chunk)
            except Exception as e:
                # If HTML fails or other error, fallback to plain text
                print(f"Chunk send failed (HTML={as_html}): {e}")
                if as_html:
                    # Retry as plain text
                    await update.message.reply_text(text_chunk)

        # Check length (Telegram limit is 4096, using 4000 for safety)
        if len(html_response) <= 4000:
            try:
                await update.message.reply_text(html_response, parse_mode="HTML")
            except Exception as e:
                print(f"HTML send failed: {e}")
                await update.message.reply_text(ai_response)
        else:
            # Message too long: Split standard Markdown by paragraphs to preserve formatting safety
            # We split the SOURCE markdown (ai_response), then convert chunks to HTML
            chunks = []
            current_chunk = ""
            
            # Split by double newline to respect paragraphs
            paragraphs = ai_response.split("\n\n")
            
            for p in paragraphs:
                # +2 for the double newline we removed
                if len(current_chunk) + len(p) + 2 < 4000:
                    current_chunk += p + "\n\n"
                else:
                    # Current chunk full, append to list
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # If single paragraph is HUGE, force split it
                    if len(p) > 4000:
                        # Simple connection for massive blocks (e.g. code)
                        for i in range(0, len(p), 4000):
                            chunks.append(p[i:i+4000])
                        current_chunk = ""
                    else:
                        current_chunk = p + "\n\n"
            
            if current_chunk:
                chunks.append(current_chunk)
                
            # Send all chunks
            for chunk in chunks:
                if chunk.strip():
                    await _send_chunk(chunk)
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error generating response:\n\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )


# Static prompt when user sends image without caption
IMAGE_WITHOUT_CAPTION_PROMPT = (
    "📷 I received your image!\n\n"
    "Please send your question about this image in the next message.\n\n"
    "💡 <b>Tip:</b> When sending an image, add a caption with your question for best results."
)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages - process images with optional caption for AI analysis."""
    user_id = update.effective_user.id
    
    # Check access
    if not check_user_access(user_id):
        await update.message.reply_text(
            "⛔️ You don't have access to this bot."
        )
        return
    
    # Get caption (question about the image)
    caption = update.message.caption
    
    # If no caption, save file_id and prompt user
    if not caption:
        # Get pending image file ID
        file_id = update.message.photo[-1].file_id
        
        # Save to user settings so we remember it for the next text message
        set_pending_image(user_id, file_id)
        
        await update.message.reply_text(
            IMAGE_WITHOUT_CAPTION_PROMPT,
            parse_mode="HTML"
        )
        return
    
    # Send typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Check for duplicate messages (idempotency)
        message_id = update.message.message_id
        if is_message_processed(user_id, message_id):
            print(f"Skipping duplicate photo message {message_id} for user {user_id}")
            return
        
        # Clear any pending image since a new one is provided
        clear_pending_image(user_id)
        
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        
        # Download photo to memory
        file = await photo.get_file()
        photo_bytes = await file.download_as_bytearray()
        
        # Convert to base64
        image_base64 = base64.b64encode(photo_bytes).decode("utf-8")
        
        # Get user settings
        settings = get_user_settings(user_id)
        
        # Get history BEFORE saving new message
        history = get_chat_history(user_id, limit=30)
        
        # Save user message (caption only, image is ephemeral)
        save_message(user_id, "user", f"[📷 Image] {caption}", message_id=message_id, image_data=image_base64)
        
        # Generate AI response with image
        ai_response = generate_response(
            history,
            caption,
            settings,
            image_base64=image_base64
        )
        
        # Save assistant response
        save_message(user_id, "assistant", ai_response)
        
        # Convert Markdown -> Telegram HTML
        html_response = markdown_to_telegram_html(ai_response)
        
        # Send response
        try:
            await update.message.reply_text(html_response, parse_mode="HTML")
        except Exception as e:
            print(f"HTML send failed: {e}")
            await update.message.reply_text(ai_response)
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error processing image:\n\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads - specifically PDFs."""
    user_id = update.effective_user.id
    
    if not check_user_access(user_id):
        return

    document = update.message.document
    file_name = document.file_name
    mime_type = document.mime_type
    
    # Check if PDF (or update to support more later)
    if mime_type != "application/pdf":
         await update.message.reply_text(
            "📂 <b>Format Not Supported</b>\n\n"
            "I currently support <b>PDF</b> files for document analysis.\n"
            "Please upload a PDF document.",
            parse_mode="HTML"
        )
         return

    status_msg = await update.message.reply_text(
        "⏳ <b>Processing PDF...</b>\n\n"
        "Uploading and indexing your document. This may take a moment...",
        parse_mode="HTML"
    )
    
    try:
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()
        
        # Create Vector Store (async)
        vector_store_id = await create_vector_store_from_file(bytes(file_bytes), file_name)
        
        # Update user state
        set_active_vector_store(user_id, vector_store_id)
        
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=status_msg.message_id,
            text=f"✅ <b>File Ready!</b>\n\n"
                 f"I've analyzed <code>{file_name}</code>.\n"
                 f"You can now ask me questions about this document.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await context.bot.edit_message_text(
             chat_id=update.message.chat_id,
             message_id=status_msg.message_id,
             text=f"❌ Error processing file:\n\n<code>{str(e)}</code>",
             parse_mode="HTML"
        )
