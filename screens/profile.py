from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string("""
<ProfileView>:
    orientation: "vertical"
    padding: dp(24)
    spacing: dp(14)
    MDLabel:
        text: "Profile & Settings"
        font_style: "H6"
        bold: True
    Widget:
""")

class ProfileView(MDBoxLayout):
    pass
