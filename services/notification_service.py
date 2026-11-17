class NotificationService:
    @staticmethod
    def show_local_notification(title: str, message: str) -> None:
        try:
            from plyer import notification
            notification.notify(title=title, message=message, app_name="RamaChat", timeout=5)
        except Exception:
            pass
