from services.supabase_client import SupabaseManager

class StatusService:
    def __init__(self):
        self.client = SupabaseManager.get_client()
