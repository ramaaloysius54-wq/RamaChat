CACHE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cached_conversations (
    id TEXT PRIMARY KEY,
    conversation_type TEXT,
    conversation_name TEXT,
    group_avatar TEXT,
    last_message TEXT,
    last_time TEXT,
    unread_count INTEGER DEFAULT 0,
    is_online INTEGER DEFAULT 0,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS cached_messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    sender_id TEXT,
    message_type TEXT,
    content TEXT,
    attachment_url TEXT,
    attachment_name TEXT,
    attachment_size INTEGER,
    reply_to TEXT,
    created_at TEXT,
    edited_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS app_preferences (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""
