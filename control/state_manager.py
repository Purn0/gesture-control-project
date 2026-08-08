class DeviceStateManager:
    def __init__(self):
        self.state = {
            "light": False,
            "fan": False,
            "door_locked": True
        }

    def apply_command(self, command: str):
        if command == "LIGHT_ON":
            self.state["light"] = True
        elif command == "LIGHT_OFF":
            self.state["light"] = False
        elif command == "FAN_ON":
            self.state["fan"] = True
        elif command == "FAN_OFF":
            self.state["fan"] = False
        elif command == "DOOR_TOGGLE":
            self.state["door_locked"] = not self.state["door_locked"]

        return self.state.copy()