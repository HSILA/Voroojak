# 🎨 Reply Keyboard (Tile Buttons) Guide

## What You'll See

When you start the bot with `/start`, beautiful tile buttons appear at the bottom:

```
┌─────────────────────────────────────┐
│  🎯 Welcome to Voroojak, @user!     │
│                                     │
│  I'm your AI assistant powered by   │
│  OpenAI models.                     │
│                                     │
│  Use the buttons below...           │
├─────────────────────────────────────┤
│  Type a message...            [🎤]  │
├─────────────────────────────────────┤
│  ⚙️ Settings      │  🗑️ New Chat   │  <- These are persistent tile buttons!
└─────────────────────────────────────┘
```

## 🆚 Difference: Tile Buttons vs Inline Buttons

### **Tile Buttons (Reply Keyboard)**
- ✓ Stay **permanently visible** at bottom
- ✓ **Replace the keyboard** - just tap
- ✓ Look like **part of the UI**
- ✓ Perfect for **main actions**

**Example:**
```
┌─────────────────────────────┐
│  ⚙️ Settings  │ 🗑️ New Chat │  <- Always visible
└─────────────────────────────┘
```

### **Inline Buttons**
- ✓ Appear **inside messages**
- ✓ **Disappear** when you scroll
- ✓ Perfect for **confirmations** and **settings**

**Example:**
```
┌─────────────────────────────┐
│  Are you sure?              │
│  ┌────────┬────────┐        │
│  │ ✅ Yes │ ❌ No  │        │  <- Inside the message
│  └────────┴────────┘        │
└─────────────────────────────┘
```

## 🎯 How It Works in Your Bot

### **1. User Flow**

```
User opens bot
     ↓
Sends /start
     ↓
Bot shows welcome + tile buttons appear
     ↓
User clicks "⚙️ Settings" (tile button)
     ↓
Bot detects button text and shows settings (inline buttons)
     ↓
User clicks model (inline button)
     ↓
Settings updated, message edited
     ↓
Tile buttons still visible at bottom!
```

### **2. Current Implementation**

**Tile Buttons (Always visible):**
- `⚙️ Settings` → Opens settings with inline buttons
- `🗑️ New Chat` → Shows confirmation with inline buttons

**Inline Buttons (Context-specific):**
- Model selection: `GPT-5.2 Chat`, `GPT-5 Mini`, `GPT-4.1`
- Reasoning levels: `🔵 Low`, `🟢 Medium`, `🔴 High` (only for reasoning models)
- Confirmations: `✅ Yes`, `❌ Cancel`

## 🔧 Customizing Tile Buttons

Want more buttons? Edit `src/bot/keyboards.py`:

```python
def build_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton("⚙️ Settings"),
            KeyboardButton("🗑️ New Chat"),
        ],
        [
            KeyboardButton("📊 Stats"),        # Add a new row
            KeyboardButton("❓ Help"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,    # Makes buttons fit nicely
        persistent=True,         # Keeps them visible
    )
```

Then handle the new buttons in `src/bot/handlers.py`:

```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ...
    
    # Handle tile button clicks
    if user_message == "⚙️ Settings":
        await settings_command(update, context)
        return
    elif user_message == "🗑️ New Chat":
        await newchat_command(update, context)
        return
    elif user_message == "📊 Stats":          # New handler
        await show_stats(update, context)
        return
    elif user_message == "❓ Help":           # New handler
        await show_help(update, context)
        return
    
    # Otherwise, send to AI...
```

## 💡 Best Practices

### **Use Tile Buttons For:**
- ✅ **Main actions** users do frequently
- ✅ **Top-level navigation**
- ✅ Commands you want **always accessible**

### **Use Inline Buttons For:**
- ✅ **Confirmations** ("Are you sure?")
- ✅ **Settings** (model selection, options)
- ✅ **Temporary choices** that change per message

## 🎨 Emojis for Buttons

Good emoji choices:
- ⚙️ Settings
- 🗑️ Delete/Clear
- 📊 Stats/Analytics
- ❓ Help
- 🔄 Refresh
- 📝 New/Create
- 🏠 Home
- 💬 Chat
- 🔍 Search

## ✅ What You Have Now

**Tile Buttons (Persistent):**
```
┌─────────────────────────────┐
│  ⚙️ Settings  │ 🗑️ New Chat │
└─────────────────────────────┘
```

**Inline Buttons (When clicking Settings):**
```
┌─────────────────────────────┐
│  ✓ GPT-5.2 Chat │ GPT-5 Mini│
│  GPT-4.1                    │
│  ─── Reasoning Level ───    │
│  🔵 Low │ ✓ 🟢 Med │ 🔴 High│
└─────────────────────────────┘
```

**Inline Buttons (When clicking New Chat):**
```
┌─────────────────────────────┐
│  ✅ Yes, clear history      │
│  ❌ Cancel                  │
└─────────────────────────────┘
```

Perfect combination of **always-visible actions** and **context-specific choices**! 🎯
