import json
import threading
from config.supabase_config import SUPABASE_ANON_KEY, SUPABASE_URL
from utils.logger import get_logger

logger = get_logger("RealtimeService")

class RealtimeService:
    def __init__(self):
        self._ws = None
        self._active_channels = set()
        self._callbacks = {}
        self._running = False

    def subscribe_conversation(self, conversation_id: str, on_event: callable) -> None:
        topic = f"realtime:public:messages:conversation_id=eq.{conversation_id}"
        self._callbacks[conversation_id] = on_event
        if topic in self._active_channels:
            return
        self._active_channels.add(topic)
        if not self._running and SUPABASE_URL and SUPABASE_ANON_KEY:
            self._start_socket()

    def unsubscribe_conversation(self, conversation_id: str) -> None:
        topic = f"realtime:public:messages:conversation_id=eq.{conversation_id}"
        self._active_channels.discard(topic)
        self._callbacks.pop(conversation_id, None)

    def _start_socket(self) -> None:
        try:
            import websocket
            ws_url = SUPABASE_URL.replace("https://", "wss://") + f"/realtime/v1/websocket?apikey={SUPABASE_ANON_KEY}&vsn=1.0.0"
            self._running = True
            self._ws = websocket.WebSocketApp(ws_url)
            threading.Thread(target=self._ws.run_forever, daemon=True).start()
        except Exception as exc:
            logger.warning(f"Realtime socket belum aktif: {exc}")
