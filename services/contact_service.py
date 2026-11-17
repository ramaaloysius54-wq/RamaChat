from services.supabase_client import SupabaseManager

class ContactService:
    def __init__(self):
        self.client = SupabaseManager.get_client()

    def add_contact_by_phone(self, user_id: str, phone_number: str) -> dict:
        if not self.client:
            return {"ok": False, "error": "Supabase belum dikonfigurasi."}
        found = self.client.table("profiles").select("id, full_name").eq("phone_number", phone_number).execute()
        if not found.data:
            return {"ok": False, "error": "Nomor belum terdaftar di RamaChat."}
        target_id = found.data[0]["id"]
        self.client.table("contacts").upsert({"user_id": user_id, "contact_user_id": target_id}).execute()
        return {"ok": True, "contact": found.data[0]}
