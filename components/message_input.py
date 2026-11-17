from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string("""
<MessageInputBar>:
    size_hint_y: None
    height: dp(68)
    padding: dp(14), dp(10)
    md_bg_color: 1, 1, 1, 1

    MDCard:
        size_hint: 1, 1
        radius: [dp(24)]
        md_bg_color: 0.955, 0.968, 0.985, 1
        elevation: 0
        padding: dp(6), dp(4)
        spacing: dp(8)

        MDIconButton:
            icon: "plus"
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            md_bg_color: 0.157, 0.47, 0.94, 1
            icon_size: "18sp"
            pos_hint: {"center_y": 0.5}
            on_release: root.on_attach() if root.on_attach else None

        TextInput:
            id: msg_field
            hint_text: "Type your message here"
            background_color: 0, 0, 0, 0
            foreground_color: 0.125, 0.16, 0.22, 1
            hint_text_color: 0.55, 0.60, 0.68, 1
            multiline: False
            font_size: "14sp"
            padding: [dp(6), dp(12), dp(6), dp(8)]
            on_text_validate: root.trigger_send()

        MDIconButton:
            icon: "emoticon-happy-outline"
            theme_icon_color: "Custom"
            icon_color: 0.55, 0.60, 0.68, 1
            pos_hint: {"center_y": 0.5}
            on_release: root.trigger_send()
""")

class MessageInputBar(MDBoxLayout):
    on_send = ObjectProperty(None)
    on_attach = ObjectProperty(None)

    def trigger_send(self):
        text = self.ids.msg_field.text.strip()
        if text and self.on_send:
            self.on_send(text)
            self.ids.msg_field.text = ""
