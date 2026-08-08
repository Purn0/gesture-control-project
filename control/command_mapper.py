from config import SUPPORTED_GESTURES


class CommandMapper:
    def __init__(self):
        self.mapping = SUPPORTED_GESTURES

    def map_gesture_to_command(self, gesture_name: str):
        return self.mapping.get(gesture_name)