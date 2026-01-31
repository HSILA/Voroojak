"""Vercel serverless function for Telegram webhook."""

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.bot.handlers import (
    handle_callback_query,
    handle_message,
    handle_photo,
    handle_document,
    newchat_command,
    settings_command,
    start_command,
)
from src.config import settings

# Initialize FastAPI app
app = FastAPI(title="Voroojak Webhook")

# Initialize Telegram bot application
telegram_app = Application.builder().token(settings.telegram_token).build()

# Register handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("settings", settings_command))
telegram_app.add_handler(CommandHandler("newchat", newchat_command))
telegram_app.add_handler(CallbackQueryHandler(handle_callback_query))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
telegram_app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "bot": "voroojak"}


@app.post("/api/webhook")
async def webhook(request: Request):
    """Handle incoming Telegram webhook updates."""
    try:
        # Parse update from Telegram
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        
        # Process update
        await telegram_app.process_update(update)
        
        return Response(status_code=200)
    
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return Response(status_code=500)


# Initialize bot on startup
@app.on_event("startup")
async def startup():
    """Initialize bot application on startup."""
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(url=settings.webhook_url)
    print(f"✅ Webhook set to: {settings.webhook_url}")


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await telegram_app.shutdown()
