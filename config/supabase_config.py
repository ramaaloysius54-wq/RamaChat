import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
WHATSAPP_OTP_PROVIDER = os.getenv("WHATSAPP_OTP_PROVIDER", "supabase_edge_whatsapp")
WHATSAPP_OTP_API_URL = os.getenv(
    "WHATSAPP_OTP_API_URL",
    f"{SUPABASE_URL}/functions/v1/whatsapp-otp" if SUPABASE_URL else ""
)
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

STORAGE_BUCKETS = {
    "avatars": "avatars",
    "chat_images": "chat-images",
    "chat_files": "chat-files",
    "statuses": "statuses",
}

def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_URL.startswith("https://"))
