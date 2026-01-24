-- Voroojak Database Schema
-- Run this in your Supabase SQL Editor: https://app.supabase.com/project/_/sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Table: allowed_users
-- Purpose: Whitelist users who can access the bot
-- =============================================================================
CREATE TABLE IF NOT EXISTS allowed_users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- Table: user_settings
-- Purpose: Store user preferences for AI model and reasoning
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES allowed_users(telegram_id) ON DELETE CASCADE,
    selected_model TEXT DEFAULT 'gpt-5-mini',
    reasoning_effort TEXT DEFAULT 'medium',
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (reasoning_effort IN ('low', 'medium', 'high'))
);

-- =============================================================================
-- Table: chat_history
-- Purpose: Store conversation context for each user
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES allowed_users(telegram_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (role IN ('user', 'assistant'))
);

-- =============================================================================
-- Indexes for Performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_created ON chat_history(user_id, created_at);

-- =============================================================================
-- Sample Data: Add yourself as the first user
-- Replace YOUR_TELEGRAM_ID with the ID from @userinfobot
-- =============================================================================
-- INSERT INTO allowed_users (telegram_id, username) 
-- VALUES (YOUR_TELEGRAM_ID, '@your_username');

-- =============================================================================
-- Useful Queries
-- =============================================================================

-- View all allowed users
-- SELECT * FROM allowed_users;

-- View a user's settings
-- SELECT * FROM user_settings WHERE user_id = YOUR_TELEGRAM_ID;

-- View recent chat history
-- SELECT * FROM chat_history WHERE user_id = YOUR_TELEGRAM_ID ORDER BY created_at DESC LIMIT 20;

-- Clear a user's chat history
-- DELETE FROM chat_history WHERE user_id = YOUR_TELEGRAM_ID;

-- Remove a user's access
-- UPDATE allowed_users SET is_active = FALSE WHERE telegram_id = YOUR_TELEGRAM_ID;
