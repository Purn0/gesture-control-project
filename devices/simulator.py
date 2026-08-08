class DeviceSimulator:
    def __init__(self):
        self.last_action = "None"

    def execute(self, command: str, state: dict):
        self.last_action = command
        return {
            "success": True,
            "message": f"Executed {command}",
            "state": state
        }