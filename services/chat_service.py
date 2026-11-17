from datetime import datetime, timezone
from services.supabase_client import SupabaseManager

class ChatService:
    def __init__(self):
        self.client = SupabaseManager.get_client()

    def fetch_conversations(self, user_id: str) -> list[dict]:
        if not self.client:
            return []
        try:
            res = self.client.table("conversation_members").select("conversation_id, conversations(*)").eq("user_id", user_id).execute()
            return [r["conversations"] for r in (res.data or []) if r.get("conversations")]
        except Exception:
            return []

    def fetch_messages(self, conversation_id: str, limit: int = 40, offset: int = 0) -> list[dict]:
        if not self.client:
            return []
        try:
            res = self.client.table("messages").select("*").eq("conversation_id", conversation_id).is_("deleted_at", "null").order("created_at", desc=False).range(offset, offset + limit - 1).execute()
            return res.data or []
        except Exception:
            return []

    def send_message(self, conversation_id: str, sender_id: str, content: str, message_type: str = "text", attachment_url: str | None = None, attachment_name: str | None = None, attachment_size: int | None = None, reply_to: str | None = None) -> dict | None:
        if not self.client:
            return None
        payload = {
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "message_type": message_type,
            "content": content,
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
            "attachment_size": attachment_size,
            "reply_to": reply_to,
        }
        res = self.client.table("messages").insert(payload).execute()
        return res.data[0] if res.data else None
