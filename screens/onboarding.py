from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

Builder.load_string("""
<OnboardingScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(32)
        spacing: dp(20)
        Widget:
        MDLabel:
            text: "RamaChat"
            halign: "center"
            font_style: "H4"
            bold: True
        MDFillRoundFlatButton:
            text: "Mulai dengan Nomor WhatsApp"
            size_hint_x: 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            on_release: app.switch_screen("login")
        Widget:
""")

class OnboardingScreen(MDScreen):
    pass
