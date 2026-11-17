import time
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
