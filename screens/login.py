from kivy.lang import Builder
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen
from utils.validators import normalize_whatsapp_number, validate_whatsapp_number

Builder.load_string("""
<LoginScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(28)
        spacing: dp(18)
        Widget:
        MDLabel:
            text: "Verifikasi Nomor WhatsApp"
            font_style: "H5"
            bold: True
        MDTextField:
            id: phone_input
            hint_text: "Nomor WhatsApp (+62...)"
            text: "+62"
            mode: "rectangle"
        MDFillRoundFlatButton:
            text: "Kirim OTP WhatsApp"
            size_hint_x: 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            on_release: root.send_otp()
        MDFlatButton:
            text: "Masuk ke Halaman Utama"
            pos_hint: {"center_x": 0.5}
            on_release: app.switch_screen("home")
        Widget:
""")

class LoginScreen(MDScreen):
    def send_otp(self):
        raw_phone = self.ids.phone_input.text.strip()
        if not validate_whatsapp_number(raw_phone):
            toast("Format nomor WhatsApp tidak valid!")
            return
        app = self.manager.app
        app.pending_phone = normalize_whatsapp_number(raw_phone)
        app.auth_service.request_whatsapp_otp(app.pending_phone)
        app.switch_screen("otp")
