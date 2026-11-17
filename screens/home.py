from kivy.lang import Builder
from kivy.factory import Factory
from kivymd.uix.screen import MDScreen
from components.chat_card import ChatCard
from screens.chats import ChatsView
from screens.contacts import ContactsView
from screens.profile import ProfileView
from screens.status import StatusView

Builder.load_string("""
<HomeScreen>:
    md_bg_color: 0.968, 0.976, 0.988, 1

    MDRelativeLayout:
        MDBottomNavigation:
            id: bottom_nav
            panel_color: 1, 1, 1, 1
            text_color_active: 0.157, 0.47, 0.94, 1
            text_color_normal: 0.55, 0.60, 0.68, 1

            MDBottomNavigationItem:
                name: "tab_home"
                text: "Home"
                icon: "home-outline"
                StatusView:

            MDBottomNavigationItem:
                name: "tab_calls"
                text: "Calls"
                icon: "phone-outline"
                MDBoxLayout:

            MDBottomNavigationItem:
                name: "tab_messages"
                text: "Messages"
                icon: "message-processing-outline"
                ChatsView:
                    id: chats_view

            MDBottomNavigationItem:
                name: "tab_contacts"
                text: "Contacts"
                icon: "account-outline"
                ContactsView:

            MDBottomNavigationItem:
                name: "tab_profile"
                text: "Profile"
                icon: "account-circle-outline"
                ProfileView:

        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: 0.157, 0.47, 0.94, 1
            theme_icon_color: "Custom"
            icon_color: 1, 1, 1, 1
            pos_hint: {"right": 0.93, "y": 0.12}
""")

class HomeScreen(MDScreen):
    def on_enter(self):
        self.ids.bottom_nav.switch_tab("tab_messages")
        self.populate_chats()

    def populate_chats(self):
        stories_row = self.ids.chats_view.ids.stories_row
        chat_list_box = self.ids.chats_view.ids.chat_list_box
        stories_row.clear_widgets()
        chat_list_box.clear_widgets()

        for name in ["Jane", "Dana", "James", "Kate", "Mike"]:
            stories_row.add_widget(Factory.StoryAvatarItem(initials=name[0], user_name=name))

        app = self.manager.app
        for conv in app.get_conversation_list():
            card = ChatCard(
                conversation_id=conv["id"],
                name=conv["name"],
                last_message=conv["last_message"],
                timestamp=conv["timestamp"],
                unread_count=conv["unread_count"],
                is_online=conv["is_online"],
            )
            card.bind(on_release=lambda inst, c=conv: app.open_conversation(c))
            chat_list_box.add_widget(card)
