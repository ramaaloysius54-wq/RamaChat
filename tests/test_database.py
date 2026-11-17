from pathlib import Path
from database.local_cache import LocalCache

def test_cache(tmp_path: Path):
    c = LocalCache(tmp_path / "test.db")
    c.upsert_conversation({"id": "c1", "conversation_name": "Dana", "last_message": "Hi", "last_time": "9:31 AM", "unread_count": 1, "is_online": True})
    assert len(c.get_conversations()) == 1
