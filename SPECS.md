# Specification: Voroojak (The Clever Rascal)
**Version:** 1.0  
**Description:** A serverless Telegram AI bot providing a "Power User" interface for OpenAI models with session persistence, model switching, and reasoning control.

---

## 1. Tech Stack
- **Language:** Python 3.10+
- **API Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)
- **AI Engine:** OpenAI (GPT-4o, o3-mini, and reasoning models)
- **Deployment:** Vercel (Serverless Functions)
- **Bot Library:** `python-telegram-bot` (using Webhooks)

---

## 2. Database Schema (Supabase)

### Table: `allowed_users`
*Used for whitelisting and access control.*
- `telegram_id` (int8, Primary Key): The unique Telegram ID of the user.
- `username` (text, nullable): The Telegram handle for administrative tracking.
- `is_active` (boolean, default: true): Toggle to revoke access without deletion.

### Table: `user_settings`
*Persists user preferences across sessions.*
- `user_id` (int8, Primary Key, FK to `allowed_users.telegram_id`): Links to the user.
- `selected_model` (text, default: 'gpt-4o'): The current OpenAI model choice.
- `reasoning_effort` (text, default: 'medium'): Value for the `reasoning_effort` parameter (low, medium, high).

### Table: `chat_history`
*Stores the context for the current active session.*
- `id` (uuid, Primary Key, default: uuid_generate_v4())
- `user_id` (int8, FK to `allowed_users.telegram_id`): Links message to user.
- `role` (text): Must be 'user' or 'assistant'.
- `content` (text): The text content of the message.
- `created_at` (timestamp, default: now()): Used for chronological retrieval.

---

## 3. Core Application Logic

### A. Access Control Middleware
1. On every incoming webhook request, extract the `user_id`.
2. Query `allowed_users` where `telegram_id = user_id` and `is_active = true`.
3. If no record is found, respond with a polite "Unauthorized" message and terminate the process.

### B. Conversation Management
1. **Context Retrieval:** Before calling the AI, fetch the latest 15-20 messages from `chat_history` for the current user, ordered by `created_at`.
2. **AI Execution:** - Send the history + new message to OpenAI.
   - Apply `selected_model` and `reasoning_effort` (if the model supports it) from the `user_settings` table.
   - Include "Web Search" via OpenAI Function Calling (if required by the prompt).
3. **Storage:** Save both the user’s prompt and the assistant’s response to `chat_history`.

### C. Session "New Chat" Logic
1. When the `/newchat` command or button is triggered, perform: 
   `DELETE FROM chat_history WHERE user_id = {current_user_id}`.
2. Send a confirmation message to the user that the "memory" has been wiped.

---

## 4. User Interface & Commands

### Commands
- `/start`: Check access and introduce the bot.
- `/newchat`: Wipe the current session history.
- `/settings`: Display the UI to change model/reasoning.

### Keyboards (Inline Buttons)
- **Model Selector:** A grid of buttons to switch between models (e.g., `[ GPT-4o ]`, `[ o3-mini ]`).
- **Reasoning Level:** A toggle for `[ Low ]`, `[ Med ]`, `[ High ]`.
- **Action:** Clicking a button updates the `user_settings` table in real-time and refreshes the keyboard UI to show the "Active" state.

---

## 5. Deployment & Configuration

### Environment Variables
- `TELEGRAM_TOKEN`: The API token from BotFather.
- `OPENAI_API_KEY`: Official OpenAI API key.
- `SUPABASE_URL`: Your project URL.
- `SUPABASE_KEY`: Your service role or anon key.
- `WEBHOOK_URL`: The Vercel deployment URL (e.g., `https://your-app.vercel.app/api/webhook`).

### Vercel Configuration (`vercel.json`)
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/main.py" }
  ]
}