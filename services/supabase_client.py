from config.supabase_config import SUPABASE_ANON_KEY, SUPABASE_URL, is_configured
from utils.logger import get_logger

logger = get_logger("SupabaseClient")

class SupabaseManager:
    _instance = None

    @classmethod
    def get_client(cls):
        if cls._instance is not None:
            return cls._instance
        if not is_configured():
            return None
        try:
            from supabase import create_client
            cls._instance = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            return cls._instance
        except Exception as exc:
            logger.error(f"Gagal inisialisasi Supabase: {exc}")
            return None
