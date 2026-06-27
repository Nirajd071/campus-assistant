-- Campus Assistant Database Schema
-- Aligned with the backend API (server.js) read/write expectations.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- FAQ Categories
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faq_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- FAQ Items (Multilingual)
--   The backend reads/writes `intent` and `confidence_threshold`, so they
--   are part of the schema.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID REFERENCES faq_categories(id),
    question_en TEXT,
    question_hi TEXT,
    question_bn TEXT,
    question_ta TEXT,
    question_mr TEXT,
    answer_en TEXT,
    answer_hi TEXT,
    answer_bn TEXT,
    answer_ta TEXT,
    answer_mr TEXT,
    keywords TEXT[],
    intent VARCHAR(100),
    confidence_threshold FLOAT DEFAULT 0.8,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Conversations (lightweight analytics log written by POST /chat)
--   Matches the columns the backend inserts on every chat turn.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255),
    user_message TEXT,
    bot_response TEXT,
    language VARCHAR(10),
    intent VARCHAR(100),
    confidence FLOAT,
    platform VARCHAR(50),
    "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Conversation sessions (used by POST /api/conversations and analytics)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(10),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Conversation messages (used by POST /api/conversations and analytics)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES conversation_sessions(id),
    message_type VARCHAR(50),
    content TEXT,
    language VARCHAR(10),
    intent VARCHAR(100),
    confidence FLOAT,
    response_time_ms INTEGER,
    escalated_to_human BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Analytics (daily metrics) - columns match calculateDailyMetrics()
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE UNIQUE NOT NULL,
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    language_distribution JSONB,
    intent_distribution JSONB,
    avg_response_time_ms FLOAT DEFAULT 0,
    escalation_rate FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Indexes for performance
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_faqs_keywords ON faqs USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_faqs_intent ON faqs(intent);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_token ON conversation_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_id ON conversation_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);
