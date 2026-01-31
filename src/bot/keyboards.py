
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Available models
MODELS = [
    ("GPT-5.2 Chat", "gpt-5.2-chat-latest"),
    ("GPT-5 Mini", "gpt-5-mini"),
    ("GPT-4.1", "gpt-4.1"),
]

# Models that support reasoning_effort parameter
REASONING_MODELS = {"gpt-5.2-chat-latest", "gpt-5-mini"}

# Reasoning levels
REASONING_LEVELS = [
    ("🔵 Low", "low"),
    ("🟢 Medium", "medium"),
    ("🔴 High", "high"),
]


def build_main_keyboard() -> ReplyKeyboardMarkup:
    """Build the main reply keyboard with persistent tile buttons.
    
    These buttons appear at the bottom of the chat and stay visible.
    
    Returns:
        Reply keyboard markup.
    """
    keyboard = [
        [
            KeyboardButton("⚙️ Settings"),
            KeyboardButton("✨ New Chat Session"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Makes buttons smaller/adaptive
    )


def build_settings_keyboard(selected_model: str, reasoning_effort: str) -> InlineKeyboardMarkup:
    """Build the settings keyboard with current selections highlighted.
    
    Args:
        selected_model: Currently selected model.
        reasoning_effort: Current reasoning effort level.
        
    Returns:
        Inline keyboard markup.
    """
    keyboard = []
    
    # Model selection (2 buttons per row)
    model_row = []
    for label, model_id in MODELS:
        # Add checkmark if selected
        text = f"✓ {label}" if model_id == selected_model else label
        model_row.append(InlineKeyboardButton(text, callback_data=f"model:{model_id}"))
        
        # Create new row after every 2 buttons
        if len(model_row) == 2:
            keyboard.append(model_row)
            model_row = []
    
    # Add remaining models if odd number
    if model_row:
        keyboard.append(model_row)
    
    # Only show reasoning options if current model supports it
    if selected_model in REASONING_MODELS:
        # Reasoning level selection (3 buttons in one row)
        reasoning_row = []
        for label, level in REASONING_LEVELS:
            # Skip "high" for models that don't support it (e.g. gpt-5.2)
            if level == "high" and selected_model == "gpt-5.2-chat-latest":
                continue
                
            text = f"✓ {label}" if level == reasoning_effort else label
            reasoning_row.append(InlineKeyboardButton(text, callback_data=f"reasoning:{level}"))
        
        keyboard.append(reasoning_row)
    else:
        # Show info that model doesn't support reasoning
        keyboard.append([
            InlineKeyboardButton("ℹ️ No reasoning controls available", callback_data="noop")
        ])
    
    return InlineKeyboardMarkup(keyboard)


def build_newchat_keyboard() -> InlineKeyboardMarkup:
    """Build a confirmation keyboard for /newchat command.
    
    Returns:
        Inline keyboard markup with confirm/cancel buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, clear history", callback_data="newchat:confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="newchat:cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
