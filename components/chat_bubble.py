from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string("""
<ChatBubble>:
    orientation: "horizontal"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(12), dp(6)
    spacing: dp(8)

    Widget:
        size_hint_x: 0.22 if root.is_sender else None
        width: dp(0) if not root.is_sender else self.width

    UserAvatar:
        initials: root.sender_initial
        avatar_size: dp(30)
        is_online: False
        opacity: 0 if root.is_sender else 1
        size_hint_x: None
        width: dp(0) if root.is_sender else dp(30)
        pos_hint: {"top": 1}

    MDBoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: self.minimum_height
        size_hint_x: 0.72
        spacing: dp(3)

        MDCard:
            size_hint_y: None
            height: msg_label.texture_size[1] + dp(24)
            padding: dp(14), dp(12)
            elevation: 0
            md_bg_color: (0.157, 0.47, 0.94, 1) if root.is_sender else (0.918, 0.937, 0.961, 1)
            radius: [dp(18), dp(18), dp(4) if root.is_sender else dp(18), dp(18) if root.is_sender else dp(4)]

            MDLabel:
                id: msg_label
                text: root.content
                size_hint_y: None
                height: self.texture_size[1]
                theme_text_color: "Custom"
                text_color: (1, 1, 1, 1) if root.is_sender else (0.125, 0.16, 0.22, 1)
                font_style: "Body2"

        MDLabel:
            text: root.timestamp
            size_hint_y: None
            height: dp(14)
            font_style: "Caption"
            halign: "right" if root.is_sender else "left"
            theme_text_color: "Custom"
            text_color: 0.55, 0.60, 0.68, 1

    Widget:
        size_hint_x: 0.22 if not root.is_sender else None
        width: dp(0) if root.is_sender else self.width
""")

class ChatBubble(MDBoxLayout):
    message_id = StringProperty("")
    content = StringProperty("")
    timestamp = StringProperty("")
    is_sender = BooleanProperty(False)
    sender_initial = StringProperty("D")
