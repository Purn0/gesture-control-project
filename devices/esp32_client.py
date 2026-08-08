import requests


class ESP32Client:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def send_command(self, command: str):
        try:
            response = requests.get(
                f"{self.base_url}/command",
                params={"action": command},
                timeout=2
            )
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "text": response.text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }