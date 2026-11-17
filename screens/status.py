from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string("""
<StatusView>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(14)
    MDLabel:
        text: "Status Updates (24h)"
        font_style: "H6"
        bold: True
    Widget:
""")

class StatusView(MDBoxLayout):
    pass
