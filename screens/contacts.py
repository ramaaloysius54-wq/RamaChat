from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string("""
<ContactsView>:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(12)
    MDLabel:
        text: "Contacts"
        font_style: "H6"
        bold: True
    Widget:
""")

class ContactsView(MDBoxLayout):
    pass
