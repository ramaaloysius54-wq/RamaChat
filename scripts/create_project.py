import argparse
import os
import py_compile
import shutil
import struct
import zlib
from pathlib import Path

BASE_DIR = Path.cwd() / "RamaChat"

FILES = {}

FILES[".env.example"] = """SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-publishable-anon-key

# Endpoint Edge Function / Server-side Gateway untuk WhatsApp OTP
# Jangan pernah menaruh API Secret WhatsApp Provider atau SUPABASE_SERVICE_ROLE_KEY di APK!
WHATSAPP_OTP_PROVIDER=meta_cloud_api
WHATSAPP_OTP_API_URL=https://your-project-id.supabase.co/functions/v1/whatsapp-otp

FIREBASE_PROJECT_ID=ramachat-android
"""

FILES[".gitignore"] = """__pycache__/
*.py[cod]
*$py.class
.env
.buildozer/
bin/
*.apk
*.aab
*.db
*.sqlite3
.pytest_cache/
.venv/
venv/
"""

FILES["requirements.txt"] = """kivy==2.3.0
kivymd==1.2.0
pillow>=10.0.0
httpx>=0.27.0
websocket-client>=1.8.0
plyer>=2.1.0
supabase>=2.6.0
python-dotenv>=1.0.1
pytest>=8.0.0
"""

FILES["config/__init__.py"] = ""

FILES["config/settings.py"] = """import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = "RamaChat"
PACKAGE_NAME = "com.rama.ramachat"
APP_VERSION = "1.0.0"

COLORS = {
    "primary": "#2878F0",
    "background": "#F7F9FC",
    "surface": "#FFFFFF",
    "bubble_sent": "#2878F0",
    "bubble_received": "#EAEFF5",
    "text_primary": "#202938",
    "text_secondary": "#8A94A6",
    "online_green": "#2ECC71",
    "danger": "#E74C3C",
}

MAX_IMAGE_SIZE_MB = 10
MAX_FILE_SIZE_MB = 50
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOC_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".zip"}
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "application/zip"
}

OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
"""

FILES["config/supabase_config.py"] = """import os

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
"""

FILES["supabase/schema.sql"] = """CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    full_name TEXT NOT NULL DEFAULT '',
    phone_number TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    bio TEXT DEFAULT 'Available on RamaChat',
    is_verified BOOLEAN DEFAULT FALSE,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    fcm_token TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_type TEXT NOT NULL CHECK (conversation_type IN ('direct', 'group')) DEFAULT 'direct',
    conversation_name TEXT,
    group_avatar TEXT,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'member')) DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (conversation_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    message_type TEXT NOT NULL CHECK (message_type IN ('text', 'image', 'file', 'audio', 'system')) DEFAULT 'text',
    content TEXT,
    attachment_url TEXT,
    attachment_name TEXT,
    attachment_size BIGINT CHECK (attachment_size IS NULL OR attachment_size >= 0),
    reactions JSONB NOT NULL DEFAULT '{}'::jsonb,
    reply_to UUID REFERENCES public.messages(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.message_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    delivered_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    UNIQUE (message_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    contact_user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, contact_user_id),
    CHECK (user_id <> contact_user_id)
);

CREATE TABLE IF NOT EXISTS public.statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    media_url TEXT NOT NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('image', 'video')),
    caption TEXT,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.status_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status_id UUID NOT NULL REFERENCES public.statuses(id) ON DELETE CASCADE,
    viewer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (status_id, viewer_id)
);

CREATE TABLE IF NOT EXISTS public.blocked_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    blocked_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (blocker_id, blocked_id),
    CHECK (blocker_id <> blocked_id)
);

CREATE INDEX IF NOT EXISTS idx_profiles_phone ON public.profiles(phone_number);
CREATE INDEX IF NOT EXISTS idx_conv_members_user ON public.conversation_members(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_members_conv ON public.conversation_members(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON public.messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_receipts_message ON public.message_receipts(message_id);
CREATE INDEX IF NOT EXISTS idx_statuses_user_expires ON public.statuses(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_blocked_pair ON public.blocked_users(blocker_id, blocked_id);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_conversations_updated_at ON public.conversations;
CREATE TRIGGER trg_conversations_updated_at
BEFORE UPDATE ON public.conversations
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;
ALTER PUBLICATION supabase_realtime ADD TABLE public.message_receipts;
ALTER PUBLICATION supabase_realtime ADD TABLE public.profiles;
"""

FILES["supabase/migrations/001_initial_schema.sql"] = FILES["supabase/schema.sql"]

FILES["supabase/policies.sql"] = """ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.statuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.status_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocked_users ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.is_conversation_member(conv_id UUID, uid UUID)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.conversation_members
        WHERE conversation_id = conv_id AND user_id = uid
    );
$$;

CREATE OR REPLACE FUNCTION public.is_conversation_admin(conv_id UUID, uid UUID)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.conversation_members
        WHERE conversation_id = conv_id AND user_id = uid AND role = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION public.is_blocked(user_a UUID, user_b UUID)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.blocked_users
        WHERE (blocker_id = user_a AND blocked_id = user_b)
           OR (blocker_id = user_b AND blocked_id = user_a)
    );
$$;

CREATE POLICY "Read non-blocked profiles" ON public.profiles FOR SELECT TO authenticated USING (NOT public.is_blocked(auth.uid(), id));
CREATE POLICY "Insert own profile" ON public.profiles FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);
CREATE POLICY "Update own profile" ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE POLICY "Select conversations for members" ON public.conversations FOR SELECT TO authenticated USING (public.is_conversation_member(id, auth.uid()) OR created_by = auth.uid());
CREATE POLICY "Create conversations" ON public.conversations FOR INSERT TO authenticated WITH CHECK (created_by = auth.uid());
CREATE POLICY "Update group conversations by admin" ON public.conversations FOR UPDATE TO authenticated USING (public.is_conversation_admin(id, auth.uid()));
CREATE POLICY "Delete group conversations by admin" ON public.conversations FOR DELETE TO authenticated USING (public.is_conversation_admin(id, auth.uid()));

CREATE POLICY "Select members in shared conversations" ON public.conversation_members FOR SELECT TO authenticated USING (public.is_conversation_member(conversation_id, auth.uid()));
CREATE POLICY "Insert creator or admin adds member" ON public.conversation_members FOR INSERT TO authenticated WITH CHECK (user_id = auth.uid() OR public.is_conversation_admin(conversation_id, auth.uid()));
CREATE POLICY "Leave conversation or admin removes member" ON public.conversation_members FOR DELETE TO authenticated USING (user_id = auth.uid() OR public.is_conversation_admin(conversation_id, auth.uid()));

CREATE POLICY "Members can read messages" ON public.messages FOR SELECT TO authenticated USING (public.is_conversation_member(conversation_id, auth.uid()));
CREATE POLICY "Members can send own messages" ON public.messages FOR INSERT TO authenticated WITH CHECK (sender_id = auth.uid() AND public.is_conversation_member(conversation_id, auth.uid()));
CREATE POLICY "Senders can edit own messages" ON public.messages FOR UPDATE TO authenticated USING (sender_id = auth.uid()) WITH CHECK (sender_id = auth.uid());
CREATE POLICY "Senders can delete own messages" ON public.messages FOR DELETE TO authenticated USING (sender_id = auth.uid());

CREATE POLICY "Members can read receipts" ON public.message_receipts FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM public.messages m WHERE m.id = message_id AND public.is_conversation_member(m.conversation_id, auth.uid())));
CREATE POLICY "Users manage own receipts" ON public.message_receipts FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users manage own contacts" ON public.contacts FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "View active statuses" ON public.statuses FOR SELECT TO authenticated USING (expires_at > NOW() AND NOT public.is_blocked(auth.uid(), user_id));
CREATE POLICY "Manage own statuses" ON public.statuses FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "Read status views" ON public.status_views FOR SELECT TO authenticated USING (viewer_id = auth.uid() OR EXISTS (SELECT 1 FROM public.statuses s WHERE s.id = status_id AND s.user_id = auth.uid()));
CREATE POLICY "Insert own status view" ON public.status_views FOR INSERT TO authenticated WITH CHECK (viewer_id = auth.uid());

CREATE POLICY "Manage own block list" ON public.blocked_users FOR ALL TO authenticated USING (blocker_id = auth.uid()) WITH CHECK (blocker_id = auth.uid());
"""

FILES["supabase/storage.sql"] = """INSERT INTO storage.buckets (id, name, public, file_size_limit)
VALUES
    ('avatars', 'avatars', false, 5242880),
    ('chat-images', 'chat-images', false, 10485760),
    ('chat-files', 'chat-files', false, 52428800),
    ('statuses', 'statuses', false, 20971520)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Authenticated users view avatars" ON storage.objects FOR SELECT TO authenticated USING (bucket_id = 'avatars');
CREATE POLICY "Users upload own avatar" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);
CREATE POLICY "Users update own avatar" ON storage.objects FOR UPDATE TO authenticated USING (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);
CREATE POLICY "Users delete own avatar" ON storage.objects FOR DELETE TO authenticated USING (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Conversation members access chat media" ON storage.objects FOR SELECT TO authenticated USING (bucket_id IN ('chat-images', 'chat-files') AND public.is_conversation_member(((storage.foldername(name))[1])::uuid, auth.uid()));
CREATE POLICY "Conversation members upload chat media" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id IN ('chat-images', 'chat-files') AND public.is_conversation_member(((storage.foldername(name))[1])::uuid, auth.uid()) AND (storage.foldername(name))[2] = auth.uid()::text);

CREATE POLICY "Authorized contacts read status media" ON storage.objects FOR SELECT TO authenticated USING (bucket_id = 'statuses');
CREATE POLICY "Users upload own status media" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'statuses' AND (storage.foldername(name))[1] = auth.uid()::text);
"""

FILES["supabase/seed.sql"] = "SELECT 'Supabase schema ready for RamaChat' AS status;\n"

FILES["utils/__init__.py"] = ""

FILES["utils/logger.py"] = """import logging
import sys

def get_logger(name: str = "RamaChat") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
    return logger
"""

FILES["utils/validators.py"] = """import mimetypes
import re
from pathlib import Path
from config.settings import (
    ALLOWED_DOC_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_MB,
    MAX_IMAGE_SIZE_MB,
    OTP_LENGTH,
)

PHONE_E164_REGEX = re.compile(r"^\\+[1-9]\\d{7,14}$")

def normalize_whatsapp_number(phone: str, default_country_code: str = "+62") -> str:
    cleaned = re.sub(r"[\\s\\-\\(\\)]", "", phone.strip())
    if cleaned.startswith("0"):
        cleaned = default_country_code + cleaned[1:]
    elif not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned

def validate_whatsapp_number(phone: str) -> bool:
    return bool(PHONE_E164_REGEX.match(normalize_whatsapp_number(phone)))

def validate_otp_code(code: str) -> bool:
    cleaned = code.strip()
    return cleaned.isdigit() and len(cleaned) == OTP_LENGTH

def validate_media_file(file_path: str, is_image: bool = False) -> tuple[bool, str]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return False, "File tidak ditemukan."
    ext = path.suffix.lower()
    allowed_exts = ALLOWED_IMAGE_EXTENSIONS if is_image else (ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOC_EXTENSIONS)
    if ext not in allowed_exts:
        return False, f"Ekstensi {ext} tidak diizinkan."
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        return False, f"Tipe MIME {mime_type} tidak didukung."
    size_mb = path.stat().st_size / (1024 * 1024)
    limit_mb = MAX_IMAGE_SIZE_MB if is_image else MAX_FILE_SIZE_MB
    if size_mb > limit_mb:
        return False, f"Ukuran file melebihi batas {limit_mb} MB."
    return True, "OK"
"""

FILES["utils/permissions.py"] = """from utils.logger import get_logger

logger = get_logger("Permissions")

def request_android_permissions() -> bool:
    try:
        from kivy.utils import platform
        if platform != "android":
            return True
        from android.permissions import Permission, request_permissions
        request_permissions([
            Permission.INTERNET,
            Permission.CAMERA,
            Permission.READ_MEDIA_IMAGES,
            Permission.READ_MEDIA_VIDEO,
            Permission.POST_NOTIFICATIONS,
        ])
        return True
    except Exception as exc:
        logger.warning(f"Izin Android dilewati: {exc}")
        return False
"""

FILES["utils/helpers.py"] = """from datetime import datetime

def format_chat_time(iso_timestamp: str | None) -> str:
    if not iso_timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%I:%M %p").lstrip("0")
    except Exception:
        return ""

def format_file_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
"""

FILES["database/__init__.py"] = ""

FILES["database/migrations.py"] = """CACHE_SCHEMA_SQL = \"\"\"
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
\"\"\"
"""

FILES["database/local_cache.py"] = """import sqlite3
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
                \"\"\"
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
                \"\"\",
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
                \"\"\"
                INSERT OR REPLACE INTO cached_messages
                (id, conversation_id, sender_id, message_type, content, attachment_url, attachment_name, attachment_size, reply_to, created_at, edited_at, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                \"\"\",
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
"""

FILES["services/__init__.py"] = ""

FILES["services/supabase_client.py"] = """from config.supabase_config import SUPABASE_ANON_KEY, SUPABASE_URL, is_configured
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
"""

FILES["services/auth_service.py"] = """import time
from config.settings import OTP_MAX_ATTEMPTS, OTP_RESEND_COOLDOWN_SECONDS
from config.supabase_config import WHATSAPP_OTP_API_URL, WHATSAPP_OTP_PROVIDER
from services.supabase_client import SupabaseManager
from utils.logger import get_logger
from utils.validators import normalize_whatsapp_number, validate_otp_code, validate_whatsapp_number

logger = get_logger("AuthService")

class AuthService:
    def __init__(self):
        self.client = SupabaseManager.get_client()
        self._last_otp_sent_at = 0.0
        self._verify_attempts = 0

    def can_resend_otp(self) -> tuple[bool, int]:
        elapsed = time.time() - self._last_otp_sent_at
        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            return False, int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
        return True, 0

    def request_whatsapp_otp(self, raw_phone: str) -> dict:
        if not validate_whatsapp_number(raw_phone):
            return {"ok": False, "error": "Nomor WhatsApp tidak valid."}
        can_send, wait_sec = self.can_resend_otp()
        if not can_send:
            return {"ok": False, "error": f"Tunggu {wait_sec} detik untuk kirim ulang OTP."}
        phone = normalize_whatsapp_number(raw_phone)
        try:
            if WHATSAPP_OTP_API_URL:
                import httpx
                with httpx.Client(timeout=15.0) as http:
                    resp = http.post(WHATSAPP_OTP_API_URL, json={"action": "send_otp", "phone": phone, "provider": WHATSAPP_OTP_PROVIDER})
                    if resp.status_code == 200:
                        self._last_otp_sent_at = time.time()
                        self._verify_attempts = 0
                        return {"ok": True, "phone": phone}
            if self.client:
                self.client.auth.sign_in_with_otp({"phone": phone, "options": {"channel": "whatsapp"}})
                self._last_otp_sent_at = time.time()
                self._verify_attempts = 0
                return {"ok": True, "phone": phone}
            return {"ok": False, "error": "Supabase belum dikonfigurasi di .env"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def verify_whatsapp_otp(self, raw_phone: str, otp_code: str) -> dict:
        if self._verify_attempts >= OTP_MAX_ATTEMPTS:
            return {"ok": False, "error": "Maksimal percobaan OTP habis."}
        if not validate_otp_code(otp_code):
            return {"ok": False, "error": "OTP harus 6 digit angka."}
        self._verify_attempts += 1
        phone = normalize_whatsapp_number(raw_phone)
        if not self.client:
            return {"ok": False, "error": "Supabase belum dikonfigurasi."}
        try:
            res = self.client.auth.verify_otp({"phone": phone, "token": otp_code.strip(), "type": "sms"})
            user = getattr(res, "user", None)
            if user:
                self.client.table("profiles").upsert({"id": user.id, "phone_number": phone, "is_verified": True, "is_online": True}).execute()
                return {"ok": True, "user_id": user.id}
            return {"ok": False, "error": "Verifikasi OTP gagal."}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def update_profile(self, user_id: str, username: str, full_name: str, bio: str, avatar_url: str | None = None) -> dict:
        if not self.client:
            return {"ok": False}
        payload = {"username": username, "full_name": full_name, "bio": bio, "is_online": True}
        if avatar_url:
            payload["avatar_url"] = avatar_url
        res = self.client.table("profiles").update(payload).eq("id", user_id).execute()
        return {"ok": True, "data": res.data}

    def get_current_user(self):
        if not self.client:
            return None
        try:
            session = self.client.auth.get_session()
            return session.user if session else None
        except Exception:
            return None
"""

FILES["services/chat_service.py"] = """from datetime import datetime, timezone
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
"""

FILES["services/realtime_service.py"] = """import json
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
"""

FILES["services/media_service.py"] = """from pathlib import Path
from config.settings import BASE_DIR

class MediaService:
    @staticmethod
    def compress_image(input_path: str, max_width: int = 1280, quality: int = 80) -> str:
        from PIL import Image
        src = Path(input_path)
        out_dir = BASE_DIR / "database" / "tmp_media"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"compressed_{src.stem}.jpg"
        with Image.open(src) as img:
            img = img.convert("RGB")
            if img.width > max_width:
                ratio = max_width / float(img.width)
                img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
            img.save(out_path, "JPEG", optimize=True, quality=quality)
        return str(out_path)

    @staticmethod
    def pick_file(on_selection: callable, filters: list[str] | None = None) -> None:
        from plyer import filechooser
        filechooser.open_file(on_selection=on_selection, filters=filters or ["*.*"])
"""

FILES["services/storage_service.py"] = """import mimetypes
from pathlib import Path
from config.supabase_config import STORAGE_BUCKETS
from services.media_service import MediaService
from services.supabase_client import SupabaseManager
from utils.validators import validate_media_file

class StorageService:
    def __init__(self):
        self.client = SupabaseManager.get_client()

    def upload_file(self, bucket_key: str, storage_path: str, local_file_path: str, is_image: bool = False) -> dict:
        valid, msg = validate_media_file(local_file_path, is_image=is_image)
        if not valid:
            return {"ok": False, "error": msg}
        if not self.client:
            return {"ok": False, "error": "Supabase belum terhubung."}
        target = MediaService.compress_image(local_file_path) if is_image else local_file_path
        bucket_name = STORAGE_BUCKETS[bucket_key]
        mime_type, _ = mimetypes.guess_type(target)
        data = Path(target).read_bytes()
        self.client.storage.from_(bucket_name).upload(path=storage_path, file=data, file_options={"content-type": mime_type or "application/octet-stream", "upsert": "true"})
        signed = self.client.storage.from_(bucket_name).create_signed_url(storage_path, 3600)
        return {"ok": True, "path": storage_path, "signed_url": signed.get("signedURL", "") if isinstance(signed, dict) else ""}
"""

FILES["services/contact_service.py"] = """from services.supabase_client import SupabaseManager

class ContactService:
    def __init__(self):
        self.client = SupabaseManager.get_client()

    def add_contact_by_phone(self, user_id: str, phone_number: str) -> dict:
        if not self.client:
            return {"ok": False, "error": "Supabase belum dikonfigurasi."}
        found = self.client.table("profiles").select("id, full_name").eq("phone_number", phone_number).execute()
        if not found.data:
            return {"ok": False, "error": "Nomor belum terdaftar di RamaChat."}
        target_id = found.data[0]["id"]
        self.client.table("contacts").upsert({"user_id": user_id, "contact_user_id": target_id}).execute()
        return {"ok": True, "contact": found.data[0]}
"""

FILES["services/status_service.py"] = """from services.supabase_client import SupabaseManager

class StatusService:
    def __init__(self):
        self.client = SupabaseManager.get_client()
"""

FILES["services/notification_service.py"] = """class NotificationService:
    @staticmethod
    def show_local_notification(title: str, message: str) -> None:
        try:
            from plyer import notification
            notification.notify(title=title, message=message, app_name="RamaChat", timeout=5)
        except Exception:
            pass
"""

FILES["components/__init__.py"] = ""

FILES["components/user_avatar.py"] = """from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.relativelayout import MDRelativeLayout

Builder.load_string(\"\"\"
<UserAvatar>:
    size_hint: None, None
    size: root.avatar_size, root.avatar_size

    MDCard:
        size_hint: 1, 1
        radius: [root.avatar_size / 2]
        md_bg_color: 0.88, 0.92, 0.98, 1
        elevation: 0
        pos_hint: {"center_x": 0.5, "center_y": 0.5}

        MDLabel:
            text: root.initials
            halign: "center"
            valign: "center"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.16, 0.47, 0.94, 1

    Widget:
        size_hint: None, None
        size: dp(12), dp(12)
        pos_hint: {"right": 0.98, "y": 0.02}
        canvas.before:
            Color:
                rgba: (1, 1, 1, 1) if root.is_online else (0, 0, 0, 0)
            Ellipse:
                pos: self.x - dp(1.5), self.y - dp(1.5)
                size: self.width + dp(3), self.height + dp(3)
            Color:
                rgba: (0.18, 0.80, 0.44, 1) if root.is_online else (0, 0, 0, 0)
            Ellipse:
                pos: self.pos
                size: self.size
\"\"\")

class UserAvatar(MDRelativeLayout):
    initials = StringProperty("R")
    avatar_size = NumericProperty(48)
    is_online = BooleanProperty(True)
"""

FILES["components/chat_card.py"] = """from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.card import MDCard
from components.user_avatar import UserAvatar

Builder.load_string(\"\"\"
<ChatCard>:
    size_hint_y: None
    height: dp(76)
    padding: dp(14), dp(10)
    spacing: dp(12)
    elevation: 0
    md_bg_color: 0.968, 0.976, 0.988, 1
    ripple_behavior: True

    UserAvatar:
        initials: root.name[:1].upper() if root.name else "U"
        is_online: root.is_online
        avatar_size: dp(50)
        pos_hint: {"center_y": 0.5}

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(4)
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.name
            bold: True
            font_style: "Subtitle1"
            theme_text_color: "Custom"
            text_color: 0.125, 0.16, 0.22, 1
            shorten: True

        MDLabel:
            text: root.last_message
            font_style: "Body2"
            bold: True if root.unread_count > 0 else False
            theme_text_color: "Custom"
            text_color: (0.125, 0.16, 0.22, 1) if root.unread_count > 0 else (0.48, 0.53, 0.61, 1)
            shorten: True
            shorten_from: "right"

    MDBoxLayout:
        orientation: "vertical"
        size_hint_x: None
        width: dp(62)
        spacing: dp(6)
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.timestamp
            font_style: "Caption"
            halign: "right"
            theme_text_color: "Custom"
            text_color: 0.55, 0.60, 0.68, 1

        AnchorLayout:
            anchor_x: "right"
            anchor_y: "center"

            MDCard:
                size_hint: None, None
                size: dp(20), dp(20)
                radius: [dp(10)]
                md_bg_color: (0.157, 0.47, 0.94, 1) if root.unread_count > 0 else (0, 0, 0, 0)
                elevation: 0

                MDLabel:
                    text: str(root.unread_count) if root.unread_count > 0 else ""
                    halign: "center"
                    valign: "center"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
\"\"\")

class ChatCard(MDCard):
    conversation_id = StringProperty("")
    name = StringProperty("")
    last_message = StringProperty("")
    timestamp = StringProperty("")
    unread_count = NumericProperty(0)
    is_online = BooleanProperty(False)
"""

FILES["components/chat_bubble.py"] = """from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string(\"\"\"
<ChatBubble>:
    orientation: "horizontal"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(12), dp(6)
    spacing: dp(8)

    Widget:
        size_hint_x: 0.22 if root.is_sender else None
        width: dp(0) if not root.is_sender else self.width

    UserAvatar:
        initials: root.sender_initial
        avatar_size: dp(30)
        is_online: False
        opacity: 0 if root.is_sender else 1
        size_hint_x: None
        width: dp(0) if root.is_sender else dp(30)
        pos_hint: {"top": 1}

    MDBoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: self.minimum_height
        size_hint_x: 0.72
        spacing: dp(3)

        MDCard:
            size_hint_y: None
            height: msg_label.texture_size[1] + dp(24)
            padding: dp(14), dp(12)
            elevation: 0
            md_bg_color: (0.157, 0.47, 0.94, 1) if root.is_sender else (0.918, 0.937, 0.961, 1)
            radius: [dp(18), dp(18), dp(4) if root.is_sender else dp(18), dp(18) if root.is_sender else dp(4)]

            MDLabel:
                id: msg_label
                text: root.content
                size_hint_y: None
                height: self.texture_size[1]
                theme_text_color: "Custom"
                text_color: (1, 1, 1, 1) if root.is_sender else (0.125, 0.16, 0.22, 1)
                font_style: "Body2"

        MDLabel:
            text: root.timestamp
            size_hint_y: None
            height: dp(14)
            font_style: "Caption"
            halign: "right" if root.is_sender else "left"
            theme_text_color: "Custom"
            text_color: 0.55, 0.60, 0.68, 1

    Widget:
        size_hint_x: 0.22 if not root.is_sender else None
        width: dp(0) if root.is_sender else self.width
\"\"\")

class ChatBubble(MDBoxLayout):
    message_id = StringProperty("")
    content = StringProperty("")
    timestamp = StringProperty("")
    is_sender = BooleanProperty(False)
    sender_initial = StringProperty("D")
"""

FILES["components/message_input.py"] = """from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string(\"\"\"
<MessageInputBar>:
    size_hint_y: None
    height: dp(68)
    padding: dp(14), dp(10)
    md_bg_color: 1, 1, 1, 1

    MDCard:
        size_hint: 1, 1
        radius: [dp(24)]
        md_bg_color: 0.955, 0.968, 0.985, 1
        elevation: 0
        padding: dp(6), dp(4)
        spacing: dp(8)

        MDIconButton:
            icon: "plus"
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            icon_size: "18sp"
            pos_hint: {"center_y": 0.5}
            on_release: root.on_attach() if root.on_attach else None

        TextInput:
            id: msg_field
            hint_text: "Type your message here"
            background_color: 0, 0, 0, 0
            foreground_color: 0.125, 0.16, 0.22, 1
            hint_text_color: 0.55, 0.60, 0.68, 1
            multiline: False
            font_size: "14sp"
            padding: [dp(6), dp(12), dp(6), dp(8)]
            on_text_validate: root.trigger_send()

        MDIconButton:
            icon: "emoticon-happy-outline"
            theme_icon_color: "Custom"
            icon_color: 0.55, 0.60, 0.68, 1
            pos_hint: {"center_y": 0.5}
            on_release: root.trigger_send()
\"\"\")

class MessageInputBar(MDBoxLayout):
    on_send = ObjectProperty(None)
    on_attach = ObjectProperty(None)

    def trigger_send(self):
        text = self.ids.msg_field.text.strip()
        if text and self.on_send:
            self.on_send(text)
            self.ids.msg_field.text = ""
"""

FILES["components/attachment_menu.py"] = """from kivymd.uix.bottomsheet import MDListBottomSheet

class AttachmentMenu:
    @staticmethod
    def open(on_select: callable):
        sheet = MDListBottomSheet()
        items = [
            ("Camera - Ambil Foto", "camera", "camera"),
            ("Gallery - Pilih Gambar", "image", "gallery"),
            ("Document - PDF, DOCX, XLSX", "file-document-outline", "document"),
            ("Archive - ZIP", "folder-zip-outline", "file"),
        ]
        for label, icon, key in items:
            sheet.add_item(label, lambda x, k=key: on_select(k), icon=icon)
        sheet.open()
"""

FILES["components/loading.py"] = """from kivymd.uix.spinner import MDSpinner
from kivy.metrics import dp

def create_loading_spinner() -> MDSpinner:
    return MDSpinner(size_hint=(None, None), size=(dp(36), dp(36)), pos_hint={"center_x": 0.5, "center_y": 0.5})
"""

FILES["screens/__init__.py"] = ""

FILES["screens/onboarding.py"] = """from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

Builder.load_string(\"\"\"
<OnboardingScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(32)
        spacing: dp(20)
        Widget:
        MDLabel:
            text: "RamaChat"
            halign: "center"
            font_style: "H4"
            bold: True
        MDFillRoundFlatButton:
            text: "Mulai dengan Nomor WhatsApp"
            size_hint_x: 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            on_release: app.switch_screen("login")
        Widget:
\"\"\")

class OnboardingScreen(MDScreen):
    pass
"""

FILES["screens/login.py"] = """from kivy.lang import Builder
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen
from utils.validators import normalize_whatsapp_number, validate_whatsapp_number

Builder.load_string(\"\"\"
<LoginScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(28)
        spacing: dp(18)
        Widget:
        MDLabel:
            text: "Verifikasi Nomor WhatsApp"
            font_style: "H5"
            bold: True
        MDTextField:
            id: phone_input
            hint_text: "Nomor WhatsApp (+62...)"
            text: "+62"
            mode: "rectangle"
        MDFillRoundFlatButton:
            text: "Kirim OTP WhatsApp"
            size_hint_x: 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            on_release: root.send_otp()
        MDFlatButton:
            text: "Masuk ke Halaman Utama"
            pos_hint: {"center_x": 0.5}
            on_release: app.switch_screen("home")
        Widget:
\"\"\")

class LoginScreen(MDScreen):
    def send_otp(self):
        raw_phone = self.ids.phone_input.text.strip()
        if not validate_whatsapp_number(raw_phone):
            toast("Format nomor WhatsApp tidak valid!")
            return
        app = self.manager.app
        app.pending_phone = normalize_whatsapp_number(raw_phone)
        app.auth_service.request_whatsapp_otp(app.pending_phone)
        app.switch_screen("otp")
"""

FILES["screens/otp.py"] = """from kivy.lang import Builder
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen
from utils.validators import validate_otp_code

Builder.load_string(\"\"\"
<OTPScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(28)
        spacing: dp(18)
        Widget:
        MDLabel:
            text: "Masukkan 6 Digit OTP"
            font_style: "H5"
            bold: True
        MDTextField:
            id: otp_input
            hint_text: "Kode OTP"
            max_text_length: 6
            input_filter: "int"
            mode: "rectangle"
        MDFillRoundFlatButton:
            text: "Verifikasi"
            size_hint_x: 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            on_release: root.verify_otp()
        Widget:
\"\"\")

class OTPScreen(MDScreen):
    def verify_otp(self):
        code = self.ids.otp_input.text.strip()
        if not validate_otp_code(code):
            toast("Masukkan 6 digit angka OTP.")
            return
        self.manager.app.switch_screen("home")
"""

FILES["screens/chats.py"] = """from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from components.chat_card import ChatCard
from components.user_avatar import UserAvatar

Builder.load_string(\"\"\"
<StoryAvatarItem@MDBoxLayout>:
    orientation: "vertical"
    size_hint: None, None
    size: dp(62), dp(82)
    spacing: dp(6)
    initials: "J"
    user_name: "Jane"

    UserAvatar:
        initials: root.initials
        avatar_size: dp(54)
        is_online: True
        pos_hint: {"center_x": 0.5}

    MDLabel:
        text: root.user_name
        halign: "center"
        font_style: "Caption"
        bold: True
        theme_text_color: "Custom"
        text_color: 0.125, 0.16, 0.22, 1

<ChatsView>:
    orientation: "vertical"
    md_bg_color: 0.968, 0.976, 0.988, 1

    MDBoxLayout:
        size_hint_y: None
        height: dp(64)
        padding: dp(18), dp(10)
        spacing: dp(14)

        UserAvatar:
            initials: "R"
            avatar_size: dp(36)
            is_online: False
            pos_hint: {"center_y": 0.5}

        MDLabel:
            text: "Messages"
            font_style: "H6"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.125, 0.16, 0.22, 1

        MDIconButton:
            icon: "magnify"
            pos_hint: {"center_y": 0.5}

    ScrollView:
        size_hint_y: None
        height: dp(96)
        do_scroll_y: False
        bar_width: 0

        MDBoxLayout:
            id: stories_row
            orientation: "horizontal"
            size_hint_x: None
            width: self.minimum_width
            padding: dp(18), dp(6)
            spacing: dp(14)

    ScrollView:
        do_scroll_x: False

        MDBoxLayout:
            id: chat_list_box
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            padding: dp(4), dp(4)
            spacing: dp(2)
\"\"\")

class ChatsView(MDBoxLayout):
    pass
"""

FILES["screens/contacts.py"] = """from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string(\"\"\"
<ContactsView>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(12)
    MDLabel:
        text: "Contacts"
        font_style: "H6"
        bold: True
    Widget:
\"\"\")

class ContactsView(MDBoxLayout):
    pass
"""

FILES["screens/status.py"] = """from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string(\"\"\"
<StatusView>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(14)
    MDLabel:
        text: "Status Updates (24h)"
        font_style: "H6"
        bold: True
    Widget:
\"\"\")

class StatusView(MDBoxLayout):
    pass
"""

FILES["screens/profile.py"] = """from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string(\"\"\"
<ProfileView>:
    orientation: "vertical"
    padding: dp(24)
    spacing: dp(14)
    MDLabel:
        text: "Profile & Settings"
        font_style: "H6"
        bold: True
    Widget:
\"\"\")

class ProfileView(MDBoxLayout):
    pass
"""

FILES["screens/settings.py"] = """from kivymd.uix.screen import MDScreen

class SettingsScreen(MDScreen):
    pass
"""

FILES["screens/home.py"] = """from kivy.lang import Builder
from kivy.factory import Factory
from kivymd.uix.screen import MDScreen
from components.chat_card import ChatCard
from screens.chats import ChatsView
from screens.contacts import ContactsView
from screens.profile import ProfileView
from screens.status import StatusView

Builder.load_string(\"\"\"
<HomeScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1

    MDRelativeLayout:
        MDBottomNavigation:
            id: bottom_nav
            panel_color: 1, 1, 1, 1
            text_color_active: 0.157, 0.47, 0.94, 1
            text_color_normal: 0.55, 0.60, 0.68, 1

            MDBottomNavigationItem:
                name: "tab_home"
                text: "Home"
                icon: "home-outline"
                StatusView:

            MDBottomNavigationItem:
                name: "tab_calls"
                text: "Calls"
                icon: "phone-outline"
                MDBoxLayout:

            MDBottomNavigationItem:
                name: "tab_messages"
                text: "Messages"
                icon: "message-processing-outline"
                ChatsView:
                    id: chats_view

            MDBottomNavigationItem:
                name: "tab_contacts"
                text: "Contacts"
                icon: "account-outline"
                ContactsView:

            MDBottomNavigationItem:
                name: "tab_profile"
                text: "Profile"
                icon: "account-circle-outline"
                ProfileView:

        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: 0.157, 0.47, 0.94, 1
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            pos_hint: {"right": 0.93, "y": 0.12}
\"\"\")

class HomeScreen(MDScreen):
    def on_enter(self):
        self.ids.bottom_nav.switch_tab("tab_messages")
        self.populate_chats()

    def populate_chats(self):
        stories_row = self.ids.chats_view.ids.stories_row
        chat_list_box = self.ids.chats_view.ids.chat_list_box
        stories_row.clear_widgets()
        chat_list_box.clear_widgets()

        for name in ["Jane", "Dana", "James", "Kate", "Mike"]:
            stories_row.add_widget(Factory.StoryAvatarItem(initials=name[0], user_name=name))

        app = self.manager.app
        for conv in app.get_conversation_list():
            card = ChatCard(
                conversation_id=conv["id"],
                name=conv["name"],
                last_message=conv["last_message"],
                timestamp=conv["timestamp"],
                unread_count=conv["unread_count"],
                is_online=conv["is_online"],
            )
            card.bind(on_release=lambda inst, c=conv: app.open_conversation(c))
            chat_list_box.add_widget(card)
"""

FILES["screens/conversation.py"] = """from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from components.attachment_menu import AttachmentMenu
from components.chat_bubble import ChatBubble
from components.message_input import MessageInputBar

Builder.load_string(\"\"\"
<ConversationScreen>:
    md_bg_color: 1, 1, 1, 1

    MDBoxLayout:
        orientation: "vertical"

        MDBoxLayout:
            size_hint_y: None
            height: dp(68)
            padding: dp(8), dp(10)
            spacing: dp(8)

            MDIconButton:
                icon: "chevron-left"
                pos_hint: {"center_y": 0.5}
                on_release: app.switch_screen("home")

            UserAvatar:
                initials: root.partner_name[:1] if root.partner_name else "D"
                avatar_size: dp(40)
                is_online: True
                pos_hint: {"center_y": 0.5}

            MDBoxLayout:
                orientation: "vertical"
                pos_hint: {"center_y": 0.5}
                spacing: dp(2)

                MDLabel:
                    text: root.partner_name
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.125, 0.16, 0.22, 1

                MDLabel:
                    text: root.partner_status
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.55, 0.60, 0.68, 1

            MDIconButton:
                icon: "phone"
                theme_icon_color: "Custom"
                icon_color: 0.157, 0.47, 0.94, 1
                pos_hint: {"center_y": 0.5}

            MDIconButton:
                icon: "video"
                theme_icon_color: "Custom"
                icon_color: 0.157, 0.47, 0.94, 1
                pos_hint: {"center_y": 0.5}

        AnchorLayout:
            size_hint_y: None
            height: dp(36)

            MDCard:
                size_hint: None, None
                size: dp(76), dp(26)
                radius: [dp(13)]
                md_bg_color: 0.955, 0.968, 0.985, 1
                elevation: 0

                MDLabel:
                    text: "Today"
                    halign: "center"
                    valign: "center"
                    font_style: "Caption"

        ScrollView:
            id: msg_scroll
            do_scroll_x: False

            MDBoxLayout:
                id: messages_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(6), dp(10)
                spacing: dp(6)

        MessageInputBar:
            id: input_bar
\"\"\")

class ConversationScreen(MDScreen):
    conversation_id = StringProperty("conv-dana")
    partner_name = StringProperty("Dana Kingston")
    partner_status = StringProperty("Last seen online at 1:31 PM")

    def on_enter(self):
        self.ids.input_bar.on_send = self.handle_send_text
        self.ids.input_bar.on_attach = lambda: AttachmentMenu.open(lambda k: None)
        self.render_messages()

    def render_messages(self):
        box = self.ids.messages_box
        box.clear_widgets()
        for msg in self.manager.app.get_messages_for_conversation(self.conversation_id):
            box.add_widget(
                ChatBubble(
                    message_id=msg["id"],
                    content=msg["content"],
                    timestamp=msg["timestamp"],
                    is_sender=msg["is_sender"],
                    sender_initial=self.partner_name[:1],
                )
            )

    def handle_send_text(self, text: str):
        new_msg = self.manager.app.send_chat_message(self.conversation_id, text)
        self.ids.messages_box.add_widget(
            ChatBubble(
                message_id=new_msg["id"],
                content=new_msg["content"],
                timestamp=new_msg["timestamp"],
                is_sender=True,
                sender_initial="R",
            )
        )
"""

FILES["main.py"] = """import uuid
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
"""

FILES["buildozer.spec"] = """[app]
title = RamaChat
package.name = ramachat
package.domain = com.rama
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,ttf,sql
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,httpx,websocket-client,plyer,supabase,python-dotenv
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/splash.png
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,CAMERA,POST_NOTIFICATIONS,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
"""

FILES["scripts/generate_assets.py"] = """import struct
import zlib
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

def create_solid_png(path: Path, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    raw_row = b"\\x00" + bytes(rgb) * width
    raw_data = raw_row * height
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\\x89PNG\\r\\n\\x1a\\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_data, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)

def generate_all_assets() -> None:
    create_solid_png(ASSETS_DIR / "icon.png", 256, 256, (40, 120, 240))
    create_solid_png(ASSETS_DIR / "logo.png", 256, 256, (40, 120, 240))
    create_solid_png(ASSETS_DIR / "splash.png", 360, 640, (247, 249, 252))
    print("[OK] assets/icon.png, logo.png, splash.png berhasil dibuat.")

if __name__ == "__main__":
    generate_all_assets()
"""

FILES["scripts/check_project.py"] = """import py_compile
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def verify_project() -> bool:
    for py_file in BASE_DIR.rglob("*.py"):
        py_compile.compile(str(py_file), doraise=True)
    print("[OK] Semua file Python di RamaChat valid dan bebas syntax error.")
    return True

if __name__ == "__main__":
    sys.exit(0 if verify_project() else 1)
"""

FILES["scripts/build_apk.sh"] = """#!/usr/bin/env bash
set -e
python3 scripts/check_project.py
buildozer android debug
ls -lh bin/*.apk
"""

FILES["tests/test_auth.py"] = """from utils.validators import normalize_whatsapp_number, validate_otp_code, validate_whatsapp_number

def test_validators():
    assert normalize_whatsapp_number("081234567890") == "+6281234567890"
    assert validate_whatsapp_number("+6281234567890") is True
    assert validate_otp_code("123456") is True
"""

FILES["tests/test_database.py"] = """from pathlib import Path
from database.local_cache import LocalCache

def test_cache(tmp_path: Path):
    c = LocalCache(tmp_path / "test.db")
    c.upsert_conversation({"id": "c1", "conversation_name": "Dana", "last_message": "Hi", "last_time": "9:31 AM", "unread_count": 1, "is_online": True})
    assert len(c.get_conversations()) == 1
"""

FILES["tests/test_services.py"] = """from config.settings import COLORS

def test_colors():
    assert COLORS["primary"] == "#2878F0"
"""

FILES["README.md"] = """# RamaChat (com.rama.ramachat)
Aplikasi Messenger Android berbasis Python, KivyMD, Buildozer & Supabase.
"""

def build_project(force: bool = False):
    for d in ["assets/fonts", "assets/images", "config", "database", "screens", "components", "services", "utils", "supabase/migrations", "scripts", "tests"]:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)

    for rel_path, content in FILES.items():
        target = BASE_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > 0 and not force:
            print(f"[SKIP] {rel_path} sudah ada")
        else:
            target.write_text(content, encoding="utf-8")
            print(f"[CREATED] {rel_path}")

    os.chmod(BASE_DIR / "scripts/build_apk.sh", 0o755)
    shutil.copyfile(__file__, BASE_DIR / "scripts/create_project.py")

    # Buat PNG assets tanpa perlu dependency eksternal
    import sys
    sys.path.insert(0, str(BASE_DIR))
    from scripts.generate_assets import generate_all_assets
    from scripts.check_project import verify_project
    generate_all_assets()
    verify_project()
    print(f"\n[SELESAI] Seluruh proyek RamaChat berhasil dibuat di: {BASE_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    build_project(force=args.force)
