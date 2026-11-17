import os
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
