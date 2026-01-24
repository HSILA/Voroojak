# Setting Up Telegram Bot Menu Button

## 🎯 What is the Menu Button?

The **Menu Button** is the button that appears next to the text input in Telegram:

```
┌─────────────────────────────────────┐
│  Voroojak                           │
├─────────────────────────────────────┤
│                                     │
│  [Bot messages appear here]         │
│                                     │
├─────────────────────────────────────┤
│  [☰ Menu]  Type a message...  [🎤]  │  <- This ☰ is the Menu Button
└─────────────────────────────────────┘
```

When users click **☰ Menu**, they see your bot's commands instead of typing `/start`, `/settings`, etc.

---

## 📝 How to Set Up Menu Commands

### **Option 1: Via BotFather (Recommended)**

1. **Open BotFather** in Telegram (`@BotFather`)

2. **Send** `/mybots`

3. **Select** your bot (e.g., `voroojak_bot`)

4. **Click** "Edit Bot" → "Edit Commands"

5. **Paste** the following:
   ```
   start - Initialize the bot and check access
   settings - Change AI model and reasoning level
   newchat - Start a new conversation (clear history)
   ```

6. **Done!** The menu button will now show these commands

---

### **Option 2: Via Telegram API**

Run this command in your terminal:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "start", "description": "Initialize the bot and check access"},
      {"command": "settings", "description": "Change AI model and reasoning level"},
      {"command": "newchat", "description": "Start a new conversation"}
    ]
  }'
```

**Expected response:**
```json
{
  "ok": true,
  "result": true
}
```

---

## 🎨 How Users See It

After setup, when users click the **☰ Menu** button:

```
┌─────────────────────────────┐
│  Commands                   │
├─────────────────────────────┤
│  /start                     │
│  Initialize the bot and...  │
├─────────────────────────────┤
│  /settings                  │
│  Change AI model and...     │
├─────────────────────────────┤
│  /newchat                   │
│  Start a new conversation   │
└─────────────────────────────┘
```

Users can click a command instead of typing it!

---

## ✅ Verify Setup

Send any message to your bot and check if the **☰ Menu** button appears. Click it to see your commands listed.

---

## 💡 Pro Tips

1. **Keep descriptions short** - They're truncated in the menu
2. **Order matters** - Put most-used commands first
3. **Update anytime** - Just run the command again with new descriptions
4. **Language support** - You can set different commands per language (advanced)

---

## 🔍 Check Current Commands

```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/getMyCommands"
```
