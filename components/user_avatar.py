from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.relativelayout import MDRelativeLayout

Builder.load_string("""
<UserAvatar>:
    size_hint: None, None
    size: root.avatar_size, root.avatar_size

    MDCard:
        size_hint: 1, 1
        radius: [root.avatar_size / 2]
        md_bg_color: 0.88, 0.92, 0.98, 1
        elevation: 0
        pos_hint: {"center_x": 0.5, "center_y": 0.5}

        MDLabel:
            text: root.initials
            halign: "center"
            valign: "center"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.16, 0.47, 0.94, 1

    Widget:
        size_hint: None, None
        size: dp(12), dp(12)
        pos_hint: {"right": 0.98, "y": 0.02}
        canvas.before:
            Color:
                rgba: (1, 1, 1, 1) if root.is_online else (0, 0, 0, 0)
            Ellipse:
                pos: self.x - dp(1.5), self.y - dp(1.5)
                size: self.width + dp(3), self.height + dp(3)
            Color:
                rgba: (0.18, 0.80, 0.44, 1) if root.is_online else (0, 0, 0, 0)
            Ellipse:
                pos: self.pos
                size: self.size
""")

class UserAvatar(MDRelativeLayout):
    initials = StringProperty("R")
    avatar_size = NumericProperty(48)
    is_online = BooleanProperty(True)
