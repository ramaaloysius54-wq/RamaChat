from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from components.chat_card import ChatCard
from components.user_avatar import UserAvatar

Builder.load_string("""
<StoryAvatarItem@MDBoxLayout>:
    orientation: "vertical"
    size_hint: None, None
    size: dp(62), dp(82)
    spacing: dp(6)
    initials: "J"
    user_name: "Jane"

    UserAvatar:
        initials: root.initials
        avatar_size: dp(54)
        is_online: True
        pos_hint: {"center_x": 0.5}

    MDLabel:
        text: root.user_name
        halign: "center"
        font_style: "Caption"
        bold: True
        theme_text_color: "Custom"
        text_color: 0.125, 0.16, 0.22, 1

<ChatsView>:
    orientation: "vertical"
    md_bg_color: 0.968, 0.976, 0.988, 1

    MDBoxLayout:
        size_hint_y: None
        height: dp(64)
        padding: dp(18), dp(10)
        spacing: dp(14)

        UserAvatar:
            initials: "R"
            avatar_size: dp(36)
            is_online: False
            pos_hint: {"center_y": 0.5}

        MDLabel:
            text: "Messages"
            font_style: "H6"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.125, 0.16, 0.22, 1

        MDIconButton:
            icon: "magnify"
            pos_hint: {"center_y": 0.5}

    ScrollView:
        size_hint_y: None
        height: dp(96)
        do_scroll_y: False
        bar_width: 0

        MDBoxLayout:
            id: stories_row
            orientation: "horizontal"
            size_hint_x: None
            width: self.minimum_width
            padding: dp(18), dp(6)
            spacing: dp(14)

    ScrollView:
        do_scroll_x: False

        MDBoxLayout:
            id: chat_list_box
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            padding: dp(4), dp(4)
            spacing: dp(2)
""")

class ChatsView(MDBoxLayout):
    pass
