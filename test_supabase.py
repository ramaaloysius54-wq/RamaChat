import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Muat .env terlebih dahulu sebelum import modul config
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

import config.supabase_config as sc
sc.SUPABASE_URL = os.getenv("SUPABASE_URL", sc.SUPABASE_URL).strip()
sc.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", sc.SUPABASE_ANON_KEY).strip()

from services.auth_service import AuthService

def run_backend_checks():
    print("=== PENGUJIAN BACKEND & KONFIGURASI RAMACHAT ===")
    if not sc.is_configured():
        print("[ERROR] SUPABASE_URL atau SUPABASE_ANON_KEY belum terisi dengan benar.")
        sys.exit(1)
    print(f"[OK] SUPABASE_URL terbaca: {sc.SUPABASE_URL}")

    auth = AuthService()
    can_send, wait = auth.can_resend_otp()
    assert can_send is True and wait == 0
    print("[OK] Service Auth & Rate Limiter OTP siap digunakan.")
    print("[SUCCESS] Semua pemeriksaan backend lulus tanpa error!")

if __name__ == "__main__":
    run_backend_checks()
