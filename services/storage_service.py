import mimetypes
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
