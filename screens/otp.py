from kivy.lang import Builder
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen
from utils.validators import validate_otp_code

Builder.load_string("""
<OTPScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(28)
        spacing: dp(18)
        Widget:
        MDLabel:
            text: "Masukkan 6 Digit OTP"
            font_style: "H5"
            bold: True
        MDTextField:
            id: otp_input
            hint_text: "Kode OTP"
            max_text_length: 6
            input_filter: "int"
            mode: "rectangle"
        MDFillRoundFlatButton:
            text: "Verifikasi"
            size_hint_x: 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            on_release: root.verify_otp()
        Widget:
""")

class OTPScreen(MDScreen):
    def verify_otp(self):
        code = self.ids.otp_input.text.strip()
        if not validate_otp_code(code):
            toast("Masukkan 6 digit angka OTP.")
            return
        self.manager.app.switch_screen("home")
