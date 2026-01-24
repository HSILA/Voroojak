# Voroojak 🤖

A serverless Telegram AI bot providing a power-user interface for OpenAI models with session persistence, model switching, and reasoning control.

## Tech Stack

- **Runtime:** Python 3.10+
- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)
- **AI:** OpenAI (GPT-5.2, GPT-5 Mini, GPT-4.1)
- **Deployment:** Vercel (Serverless)
- **Bot:** python-telegram-bot (Webhooks)

## Features

✨ **Beautiful UI** - Persistent tile buttons for easy access  
🤖 **Smart Model Selection** - Switch between GPT-5.2, GPT-5 Mini, and GPT-4.1  
🧠 **Reasoning Control** - Adjust reasoning effort for supported models  
💾 **Session Persistence** - Chat history saved in Supabase  
🔒 **Access Control** - Whitelist-based user management  
⚡ **Serverless** - Zero maintenance, auto-scaling

## Setup

### 1. Install Dependencies

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Set Up Database

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Copy the SQL from `scripts/setup_database.py` and run it in the SQL Editor
3. Add your Telegram ID to the whitelist:
   ```sql
   INSERT INTO allowed_users (telegram_id, username) 
   VALUES (YOUR_TELEGRAM_ID, '@your_username');
   ```

### 4. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the token to `.env`

### 5. Deploy to Vercel

```bash
bun x vercel --prod
```

### 6. Set Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook"
```

## Project Structure

```
Voroojak/
├── api/                    # Vercel serverless functions
├── src/
│   ├── bot/               # Telegram handlers
│   ├── db/                # Database operations
│   ├── services/          # External integrations
│   └── config.py          # Settings
├── scripts/               # Setup utilities
└── pyproject.toml         # Dependencies
```

## Commands

- `/start` - Initialize bot and show tile buttons
- `/newchat` - Clear conversation history
- `/settings` - Configure model & reasoning

**Or use the beautiful tile buttons at the bottom:**  
`⚙️ Settings` | `✨ New Chat Session`

## License

MIT
