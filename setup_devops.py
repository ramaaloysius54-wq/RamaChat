from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEVOPS_FILES = {}

# ==============================================================================
# 1. FIX TEST SUPABASE & ENV (.env)
# ==============================================================================
DEVOPS_FILES[".env"] = """SUPABASE_URL=https://wmauyurhlwodusqnbkcv.supabase.co
SUPABASE_ANON_KEY=sb_publishable_eZ7Tdo4P-oW10lvImVUJbA_QJlYNNke

WHATSAPP_OTP_PROVIDER=custom_gateway
WHATSAPP_OTP_API_URL=http://localhost:4040/functions/v1/whatsapp-otp

FIREBASE_PROJECT_ID=ramachat-android
"""

DEVOPS_FILES["test_supabase.py"] = """import os
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
"""

# ==============================================================================
# 2. SERVER API VERIFIKASI WHATSAPP OTP (UNTUK POD CONTAINER DI VPS)
# ==============================================================================
DEVOPS_FILES["server/otp_server.py"] = """import hashlib
import json
import os
import random
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "4040"))
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
"""

DEVOPS_FILES["Dockerfile"] = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir python-dotenv httpx pytest

COPY . /app

EXPOSE 4040

CMD ["python3", "server/otp_server.py"]
"""

# ==============================================================================
# 3. MANIFES KUBERNETES POD & ARGOCD GITOPS (k8s/)
# ==============================================================================
DEVOPS_FILES["k8s/namespace.yaml"] = """apiVersion: v1
kind: Namespace
metadata:
  name: ramachat
"""

DEVOPS_FILES["k8s/deployment.yaml"] = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: ramachat-otp-server
  namespace: ramachat
  labels:
    app: ramachat-otp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ramachat-otp-server
  template:
    metadata:
      labels:
        app: ramachat-otp-server
    spec:
      restartPolicy: Always
      containers:
        - name: otp-verification-api
          image: ramachat-otp-server:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 4040
          env:
            - name: PORT
              value: "4040"
            - name: SUPABASE_URL
              value: "https://wmauyurhlwodusqnbkcv.supabase.co"
            - name: SUPABASE_ANON_KEY
              value: "sb_publishable_eZ7Tdo4P-oW10lvImVUJbA_QJlYNNke"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 4040
            initialDelaySeconds: 5
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /healthz
              port: 4040
            initialDelaySeconds: 3
            periodSeconds: 10
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "256Mi"
              cpu: "250m"
"""

DEVOPS_FILES["k8s/service.yaml"] = """apiVersion: v1
kind: Service
metadata:
  name: ramachat-otp-service
  namespace: ramachat
spec:
  type: LoadBalancer
  selector:
    app: ramachat-otp-server
  ports:
    - protocol: TCP
      port: 4040
      targetPort: 4040
      
"""

DEVOPS_FILES["k8s/argocd-application.yaml"] = """apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ramachat-gitops
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/USERNAME_ANDA/RamaChat.git
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: ramachat
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
"""

# ==============================================================================
# 4. GITHUB ACTIONS WORKFLOW (.github/workflows/deploy.yml)
#    - Otomatis Test di GitHub Actions pada setiap push ke main
#    - Hanya jika Test Sukses -> Sync ke /var/www/aplication & Deploy Pod K8s/ArgoCD
#    - Build APK Android hanya dieksekusi jika dijalankan Manual (workflow_dispatch)
# ==============================================================================
DEVOPS_FILES[".github/workflows/deploy.yml"] = """name: CI/CD Pipeline Rama DevOps (RamaChat & K8s Pod)

on:
  push:
    branches:
      - main
  workflow_dispatch:
    inputs:
      build_apk_manual:
        description: 'Centang untuk Build APK Android secara manual'
        required: false
        default: 'false'

jobs:
  # ----------------------------------------------------------------------------
  # JOB 1: AUTOMATED TEST & VERIFICATION DI GITHUB ACTIONS
  # ----------------------------------------------------------------------------
  test-and-verify:
    name: 🧪 Test Syntax, Pytest & Verify Backend
    runs-on: ubuntu-latest

    steps:
      - name: 📥 Checkout Repository
        uses: actions/checkout@v4

      - name: 🐍 Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 📦 Install Test Dependencies
        run: |
          pip install --upgrade pip
          pip install pillow python-dotenv httpx pytest

      - name: 🎨 Generate App Assets & Check Python Syntax
        run: |
          python3 scripts/generate_assets.py
          python3 scripts/check_project.py

      - name: ✅ Run Unit Tests (Pytest) & Backend Config Verification
        env:
          SUPABASE_URL: https://wmauyurhlwodusqnbkcv.supabase.co
          SUPABASE_ANON_KEY: sb_publishable_eZ7Tdo4P-oW10lvImVUJbA_QJlYNNke
        run: |
          pytest -v
          python3 test_supabase.py

  # ----------------------------------------------------------------------------
  # JOB 2: SYNC KE VPS (/var/www/aplication) & DEPLOY POD K8S / ARGOCD
  #        (Hanya berjalan apabila Job 1 lulus 100% tanpa error)
  # ----------------------------------------------------------------------------
  build-and-deploy:
    name: 🚀 Sync & Build Pod di VPS (/var/www/aplication)
    needs: test-and-verify
    runs-on: ubuntu-latest

    steps:
      - name: 📥 Checkout Repository
        uses: actions/checkout@v4

      - name: 🚀 Sync & Build di VPS (/var/www/aplication)
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USER: ${{ secrets.VPS_USER }}
          SSHPASS: ${{ secrets.VPS_PASSWORD }}
        run: |
          sudo apt-get update && sudo apt-get install -y sshpass rsync

          echo "0. Memastikan direktori /var/www/aplication tersedia di VPS..."
          sshpass -e ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -p 22 "$VPS_USER@$VPS_HOST" "mkdir -p /var/www/aplication"

          echo "1. Mengirim file terbaru ke VPS (/var/www/aplication)..."
          sshpass -e rsync -avz --delete \\
            --exclude='.git' \\
            --exclude='node_modules' \\
            --exclude='.env' \\
            --exclude='.buildozer' \\
            --exclude='bin' \\
            --exclude='baileys_auth_info' \\
            -e "ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -p 22" \\
            ./ "$VPS_USER@$VPS_HOST:/var/www/aplication/"

          echo "2. Build Container Image & Deploy Pod Kubernetes + ArgoCD di VPS..."
          sshpass -e ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -p 22 "$VPS_USER@$VPS_HOST" << 'ENDSSH'
            set -e
            cd /var/www/aplication

            echo "--> Memeriksa syntax project di VPS..."
            python3 scripts/check_project.py

            echo "--> Membangun Docker Image untuk Pod OTP Verification Server..."
            if command -v docker &> /dev/null; then
              docker build -t ramachat-otp-server:latest .
              # Jika VPS menggunakan K3s, import image langsung ke containerd K3s
              if command -v k3s &> /dev/null; then
                docker save ramachat-otp-server:latest | sudo k3s ctr images import -
              fi
            fi

            echo "--> Menerapkan Manifes Pod Kubernetes & ArgoCD..."
            if command -v kubectl &> /dev/null; then
              kubectl apply -f k8s/namespace.yaml
              kubectl apply -f k8s/deployment.yaml
              kubectl apply -f k8s/service.yaml
              kubectl rollout restart deployment/ramachat-otp-server -n ramachat
              kubectl get pods -n ramachat
              # Terapkan ArgoCD Application jika namespace argocd tersedia
              if kubectl get ns argocd &> /dev/null; then
                kubectl apply -f k8s/argocd-application.yaml || true
              fi
            fi

            echo "--> Deployment ke /var/www/aplication & Pod Kubernetes Selesai!"
          ENDSSH

  # ----------------------------------------------------------------------------
  # JOB 3: MANUAL APK BUILD (Hanya jalan jika di-trigger manual dari GitHub)
  # ----------------------------------------------------------------------------
  manual-apk-build:
    name: 📱 Manual Build Android APK
    if: github.event_name == 'workflow_dispatch' && github.event.inputs.build_apk_manual == 'true'
    needs: test-and-verify
    runs-on: ubuntu-22.04

    steps:
      - name: 📥 Checkout Repository
        uses: actions/checkout@v4

      - name: 🎨 Generate Assets
        run: python3 scripts/generate_assets.py

      - name: 🔨 Build Debug APK with Buildozer
        uses: ArtemSBulgakov/buildozer-action@v1
        id: buildozer
        with:
          command: buildozer android debug
          buildozer_version: stable

      - name: 📤 Upload APK Artifact
        uses: actions/upload-artifact@v4
        with:
          name: RamaChat-debug-apk
          path: ${{ steps.buildozer.outputs.filename }}
"""

def apply_devops_setup():
    for rel_path, content in DEVOPS_FILES.items():
        fpath = BASE_DIR / rel_path
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
        print(f"[CREATED] {rel_path}")

    print("\n[OK] Setup CI/CD, Docker Pod, Kubernetes & ArgoCD berhasil dibuat!")

if __name__ == "__main__":
    apply_devops_setup()
