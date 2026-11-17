from kivymd.uix.spinner import MDSpinner
from kivy.metrics import dp

def create_loading_spinner() -> MDSpinner:
    return MDSpinner(size_hint=(None, None), size=(dp(36), dp(36)), pos_hint={"center_x": 0.5, "center_y": 0.5})
