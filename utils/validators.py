import mimetypes
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

PHONE_E164_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")

def normalize_whatsapp_number(phone: str, default_country_code: str = "+62") -> str:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
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
