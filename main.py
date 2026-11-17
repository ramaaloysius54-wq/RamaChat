import uuid
from datetime import datetime, timezone
from kivy.core.window import Window
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from database.local_cache import LocalCache
from screens.conversation import ConversationScreen
from screens.home import HomeScreen
from screens.login import LoginScreen
from screens.onboarding import OnboardingScreen
from screens.otp import OTPScreen
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.contact_service import ContactService
from services.realtime_service import RealtimeService
from services.status_service import StatusService
from services.storage_service import StorageService
from utils.helpers import format_chat_time
from utils.permissions import request_android_permissions

if platform not in ("android", "ios"):
    Window.size = (390, 820)

class RamaChatApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "RamaChat"
        self.cache = LocalCache()
        self.auth_service = AuthService()
        self.chat_service = ChatService()
        self.realtime_service = RealtimeService()
        self.storage_service = StorageService()
        self.contact_service = ContactService()
        self.status_service = StatusService()
        self.pending_phone = ""
        self._seed_initial_local_cache()

    def build(self):
        request_android_permissions()
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.sm = MDScreenManager()
        self.sm.app = self
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(ConversationScreen(name="conversation"))
        self.sm.add_widget(OnboardingScreen(name="onboarding"))
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(OTPScreen(name="otp"))
        return self.sm

    def switch_screen(self, screen_name: str):
        self.sm.current = screen_name

    def _seed_initial_local_cache(self):
        if self.cache.get_conversations():
            return
        initial_chats = [
            {"id": "conv-jane", "conversation_name": "Jane", "last_message": "Hey, just checking in about the meeting later... is there anyway t..", "last_time": "5:31 PM", "unread_count": 1, "is_online": True, "updated_at": "2026-01-01T17:31:00Z"},
            {"id": "conv-dana", "conversation_name": "Dana Kingston", "last_message": "That's great! Well done!", "last_time": "1:31 PM", "unread_count": 0, "is_online": True, "updated_at": "2026-01-01T13:31:00Z"},
            {"id": "conv-james", "conversation_name": "James", "last_message": "The task is already done. Let me know if there's anything that I ca...", "last_time": "1:06 PM", "unread_count": 0, "is_online": True, "updated_at": "2026-01-01T13:06:00Z"},
            {"id": "conv-kate", "conversation_name": "Kate", "last_message": "Thanks for the update! Let me check this.", "last_time": "12:31 PM", "unread_count": 0, "is_online": False, "updated_at": "2026-01-01T12:31:00Z"},
            {"id": "conv-mike", "conversation_name": "Mike", "last_message": "Thanks for the help!", "last_time": "11:45 AM", "unread_count": 0, "is_online": True, "updated_at": "2026-01-01T11:45:00Z"},
            {"id": "conv-alice", "conversation_name": "Alice", "last_message": "Good morning! I was wondering if you have the file for the meetin...", "last_time": "11:00 AM", "unread_count": 0, "is_online": True, "updated_at": "2026-01-01T11:00:00Z"},
            {"id": "conv-mer", "conversation_name": "Mer", "last_message": "Let me check that later. Thank you!", "last_time": "10:15 AM", "unread_count": 0, "is_online": False, "updated_at": "2026-01-01T10:15:00Z"},
        ]
        for c in initial_chats:
            self.cache.upsert_conversation(c)

        initial_msgs = [
            ("m1", "conv-dana", "partner", "Hello 😊", "2026-01-01T09:31:00Z"),
            ("m2", "conv-dana", "me", "Hi, there! How are you?", "2026-01-01T09:35:00Z"),
            ("m3", "conv-dana", "partner", "I'm doing great! Working on new tasks today. And I was wondering if you can help me with something", "2026-01-01T09:38:00Z"),
            ("m4", "conv-dana", "me", "Yeah, sure! I can help you anytime", "2026-01-01T10:00:00Z"),
            ("m5", "conv-dana", "partner", "▌║▌║│▌║▌│║▌║│▌║ (Voice Note 0:18)", "2026-01-01T10:20:00Z"),
        ]
        for mid, cid, sender, content, ts in initial_msgs:
            self.cache.cache_message({"id": mid, "conversation_id": cid, "sender_id": sender, "message_type": "text", "content": content, "created_at": ts})

    def get_conversation_list(self) -> list[dict]:
        return [
            {
                "id": c["id"],
                "name": c["conversation_name"],
                "last_message": c["last_message"],
                "timestamp": c["last_time"],
                "unread_count": c["unread_count"],
                "is_online": bool(c["is_online"]),
            }
            for c in self.cache.get_conversations()
        ]

    def open_conversation(self, conv: dict):
        conv_screen = self.sm.get_screen("conversation")
        conv_screen.conversation_id = conv["id"]
        conv_screen.partner_name = conv["name"]
        conv_screen.partner_status = f"Last seen online at {conv['timestamp']}"
        self.switch_screen("conversation")

    def get_messages_for_conversation(self, conversation_id: str) -> list[dict]:
        return [
            {
                "id": r["id"],
                "content": r["content"],
                "timestamp": format_chat_time(r["created_at"]) or "10:00 AM",
                "is_sender": r["sender_id"] == "me",
            }
            for r in self.cache.get_messages(conversation_id)
        ]

    def send_chat_message(self, conversation_id: str, content: str) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        msg_id = str(uuid.uuid4())
        self.cache.cache_message({"id": msg_id, "conversation_id": conversation_id, "sender_id": "me", "message_type": "text", "content": content, "created_at": now_iso})
        return {"id": msg_id, "content": content, "timestamp": format_chat_time(now_iso)}

if __name__ == "__main__":
    RamaChatApp().run()
