from utils.logger import get_logger

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
