from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.card import MDCard
from components.user_avatar import UserAvatar

Builder.load_string("""
<ChatCard>:
    size_hint_y: None
    height: dp(76)
    padding: dp(14), dp(10)
    spacing: dp(12)
    elevation: 0
    md_bg_color: 0.968, 0.976, 0.988, 1
    ripple_behavior: True

    UserAvatar:
        initials: root.name[:1].upper() if root.name else "U"
        is_online: root.is_online
        avatar_size: dp(50)
        pos_hint: {"center_y": 0.5}

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(4)
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.name
            bold: True
            font_style: "Subtitle1"
            theme_text_color: "Custom"
            text_color: 0.125, 0.16, 0.22, 1
            shorten: True

        MDLabel:
            text: root.last_message
            font_style: "Body2"
            bold: True if root.unread_count > 0 else False
            theme_text_color: "Custom"
            text_color: (0.125, 0.16, 0.22, 1) if root.unread_count > 0 else (0.48, 0.53, 0.61, 1)
            shorten: True
            shorten_from: "right"

    MDBoxLayout:
        orientation: "vertical"
        size_hint_x: None
        width: dp(62)
        spacing: dp(6)
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.timestamp
            font_style: "Caption"
            halign: "right"
            theme_text_color: "Custom"
            text_color: 0.55, 0.60, 0.68, 1

        AnchorLayout:
            anchor_x: "right"
            anchor_y: "center"

            MDCard:
                size_hint: None, None
                size: dp(20), dp(20)
                radius: [dp(10)]
                md_bg_color: (0.157, 0.47, 0.94, 1) if root.unread_count > 0 else (0, 0, 0, 0)
                elevation: 0

                MDLabel:
                    text: str(root.unread_count) if root.unread_count > 0 else ""
                    halign: "center"
                    valign: "center"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
""")

class ChatCard(MDCard):
    conversation_id = StringProperty("")
    name = StringProperty("")
    last_message = StringProperty("")
    timestamp = StringProperty("")
    unread_count = NumericProperty(0)
    is_online = BooleanProperty(False)
