import sqlite3
from pathlib import Path
from config.settings import BASE_DIR
from database.migrations import CACHE_SCHEMA_SQL

class LocalCache:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (BASE_DIR / "database" / "ramachat_cache.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(CACHE_SCHEMA_SQL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def upsert_conversation(self, conv: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cached_conversations
                (id, conversation_type, conversation_name, group_avatar, last_message, last_time, unread_count, is_online, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    conversation_name=excluded.conversation_name,
                    group_avatar=excluded.group_avatar,
                    last_message=excluded.last_message,
                    last_time=excluded.last_time,
                    unread_count=excluded.unread_count,
                    is_online=excluded.is_online,
                    updated_at=excluded.updated_at
                """,
                (
                    conv.get("id"),
                    conv.get("conversation_type", "direct"),
                    conv.get("conversation_name", ""),
                    conv.get("group_avatar", ""),
                    conv.get("last_message", ""),
                    conv.get("last_time", ""),
                    int(conv.get("unread_count", 0)),
                    1 if conv.get("is_online") else 0,
                    conv.get("updated_at", ""),
                ),
            )

    def get_conversations(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM cached_conversations ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def cache_message(self, msg: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cached_messages
                (id, conversation_id, sender_id, message_type, content, attachment_url, attachment_name, attachment_size, reply_to, created_at, edited_at, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg.get("id"),
                    msg.get("conversation_id"),
                    msg.get("sender_id"),
                    msg.get("message_type", "text"),
                    msg.get("content", ""),
                    msg.get("attachment_url"),
                    msg.get("attachment_name"),
                    msg.get("attachment_size"),
                    msg.get("reply_to"),
                    msg.get("created_at"),
                    msg.get("edited_at"),
                    msg.get("deleted_at"),
                ),
            )

    def get_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM cached_messages WHERE conversation_id = ? AND deleted_at IS NULL ORDER BY created_at ASC LIMIT ? OFFSET ?",
                (conversation_id, limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]
