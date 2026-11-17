import hashlib
import json
import os
import random
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "8080"))
WA_GATEWAY_URL = os.getenv("WA_GATEWAY_URL", "")
WA_GATEWAY_TOKEN = os.getenv("WA_GATEWAY_TOKEN", "")

# Penyimpanan hash OTP di memori container (SHA-256, masa berlaku 5 menit, cooldown 60 detik)
OTP_STORE = {}

def hash_otp(phone: str, code: str) -> str:
    return hashlib.sha256(f"{phone}:{code}".encode("utf-8")).hexdigest()

class OTPRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Endpoint Healthcheck untuk Liveness & Readiness Probe Kubernetes Pod
        if self.path in ("/", "/healthz"):
            self._send_json(200, {"status": "healthy", "service": "ramachat-otp-pod"})
        else:
            self._send_json(404, {"ok": False, "error": "Not Found"})

    def do_POST(self):
        if self.path != "/functions/v1/whatsapp-otp":
            self._send_json(404, {"ok": False, "error": "Endpoint tidak ditemukan"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(raw_body)
        except Exception:
            self._send_json(400, {"ok": False, "error": "JSON tidak valid"})
            return

        action = data.get("action")
        phone = str(data.get("phone", "")).strip()
        if not phone:
            self._send_json(400, {"ok": False, "error": "Nomor WhatsApp wajib diisi"})
            return

        now = time.time()

        if action == "send_otp":
            existing = OTP_STORE.get(phone)
            if existing and now < existing["cooldown_until"]:
                wait_sec = int(existing["cooldown_until"] - now)
                self._send_json(429, {"ok": False, "error": f"Tunggu {wait_sec} detik sebelum kirim ulang OTP."})
                return

            otp_code = f"{random.randint(100000, 999999)}"
            OTP_STORE[phone] = {
                "otp_hash": hash_otp(phone, otp_code),
                "expires_at": now + 300,
                "cooldown_until": now + 60,
                "attempts": 0,
            }

            # Teruskan ke Gateway / Bot WhatsApp jika URL dikonfigurasi
            if WA_GATEWAY_URL:
                try:
                    req_data = json.dumps({
                        "to": phone,
                        "message": f"*RamaChat* - Kode OTP Anda: *{otp_code}* (Berlaku 5 menit)."
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        WA_GATEWAY_URL,
                        data=req_data,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {WA_GATEWAY_TOKEN}"
                        },
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=10)
                except Exception as exc:
                    print(f"[WARN] Gagal meneruskan ke WA Gateway: {exc}")

            print(f"[OTP-SERVER] OTP generated untuk nomor {phone}")
            self._send_json(200, {"ok": True, "phone": phone, "message": "OTP berhasil dikirim"})
            return

        if action == "verify_otp":
            otp_code = str(data.get("otp_code", "")).strip()
            record = OTP_STORE.get(phone)
            if not record or now > record["expires_at"]:
                self._send_json(400, {"ok": False, "error": "OTP kedaluwarsa atau belum diminta."})
                return

            if record["attempts"] >= 5:
                self._send_json(403, {"ok": False, "error": "Batas maksimal 5 percobaan habis."})
                return

            record["attempts"] += 1
            if hash_otp(phone, otp_code) != record["otp_hash"]:
                self._send_json(401, {"ok": False, "error": "Kode OTP salah."})
                return

            OTP_STORE.pop(phone, None)
            self._send_json(200, {"ok": True, "verified": True, "phone": phone})
            return

        self._send_json(400, {"ok": False, "error": "Action tidak valid"})

if __name__ == "__main__":
    print(f"[START] RamaChat OTP Verification Pod berjalan di port {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), OTPRequestHandler)
    server.serve_forever()
