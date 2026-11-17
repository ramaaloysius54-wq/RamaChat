from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from components.attachment_menu import AttachmentMenu
from components.chat_bubble import ChatBubble
from components.message_input import MessageInputBar

Builder.load_string("""
<ConversationScreen>:
    md_bg_color: 1, 1, 1, 1

    MDBoxLayout:
        orientation: "vertical"

        MDBoxLayout:
            size_hint_y: None
            height: dp(68)
            padding: dp(8), dp(10)
            spacing: dp(8)

            MDIconButton:
                icon: "chevron-left"
                pos_hint: {"center_y": 0.5}
                on_release: app.switch_screen("home")

            UserAvatar:
                initials: root.partner_name[:1] if root.partner_name else "D"
                avatar_size: dp(40)
                is_online: True
                pos_hint: {"center_y": 0.5}

            MDBoxLayout:
                orientation: "vertical"
                pos_hint: {"center_y": 0.5}
                spacing: dp(2)

                MDLabel:
                    text: root.partner_name
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.125, 0.16, 0.22, 1

                MDLabel:
                    text: root.partner_status
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.55, 0.60, 0.68, 1

            MDIconButton:
                icon: "phone"
                theme_icon_color: "Custom"
                icon_color: 0.157, 0.47, 0.94, 1
                pos_hint: {"center_y": 0.5}

            MDIconButton:
                icon: "video"
                theme_icon_color: "Custom"
                icon_color: 0.157, 0.47, 0.94, 1
                pos_hint: {"center_y": 0.5}

        AnchorLayout:
            size_hint_y: None
            height: dp(36)

            MDCard:
                size_hint: None, None
                size: dp(76), dp(26)
                radius: [dp(13)]
                md_bg_color: 0.955, 0.968, 0.985, 1
                elevation: 0

                MDLabel:
                    text: "Today"
                    halign: "center"
                    valign: "center"
                    font_style: "Caption"

        ScrollView:
            id: msg_scroll
            do_scroll_x: False

            MDBoxLayout:
                id: messages_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(6), dp(10)
                spacing: dp(6)

        MessageInputBar:
            id: input_bar
""")

class ConversationScreen(MDScreen):
    conversation_id = StringProperty("conv-dana")
    partner_name = StringProperty("Dana Kingston")
    partner_status = StringProperty("Last seen online at 1:31 PM")

    def on_enter(self):
        self.ids.input_bar.on_send = self.handle_send_text
        self.ids.input_bar.on_attach = lambda: AttachmentMenu.open(lambda k: None)
        self.render_messages()

    def render_messages(self):
        box = self.ids.messages_box
        box.clear_widgets()
        for msg in self.manager.app.get_messages_for_conversation(self.conversation_id):
            box.add_widget(
                ChatBubble(
                    message_id=msg["id"],
                    content=msg["content"],
                    timestamp=msg["timestamp"],
                    is_sender=msg["is_sender"],
                    sender_initial=self.partner_name[:1],
                )
            )

    def handle_send_text(self, text: str):
        new_msg = self.manager.app.send_chat_message(self.conversation_id, text)
        self.ids.messages_box.add_widget(
            ChatBubble(
                message_id=new_msg["id"],
                content=new_msg["content"],
                timestamp=new_msg["timestamp"],
                is_sender=True,
                sender_initial="R",
            )
        )
