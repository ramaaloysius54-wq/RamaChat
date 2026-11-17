from kivymd.uix.bottomsheet import MDListBottomSheet

class AttachmentMenu:
    @staticmethod
    def open(on_select: callable):
        sheet = MDListBottomSheet()
        items = [
            ("Camera - Ambil Foto", "camera", "camera"),
            ("Gallery - Pilih Gambar", "image", "gallery"),
            ("Document - PDF, DOCX, XLSX", "file-document-outline", "document"),
            ("Archive - ZIP", "folder-zip-outline", "file"),
        ]
        for label, icon, key in items:
            sheet.add_item(label, lambda x, k=key: on_select(k), icon=icon)
        sheet.open()
