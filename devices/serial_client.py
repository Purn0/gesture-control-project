import time

try:
    import serial  # pyserial
except ImportError:  # pragma: no cover
    serial = None


class SerialClient:
    """
    Simple newline-terminated serial command sender for an Arduino
    (Uno / Nano). Opens the port on construction, waits briefly for the
    Arduino auto-reset to complete, then sends commands on demand.
    """

    def __init__(self, port: str, baud: int = 9600, startup_wait: float = 2.0):
        if serial is None:
            raise RuntimeError(
                "pyserial is not installed. Run: pip install pyserial"
            )

        self.port = port
        self.baud = baud
        # write_timeout protects the UI from hanging if the port opens but
        # the device (or a ghost driver) never actually drains the buffer.
        self.ser = serial.Serial(
            port,
            baud,
            timeout=1,
            write_timeout=1,
        )

        # Arduinos auto-reset on serial open; give the sketch time to boot.
        time.sleep(startup_wait)
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass

    def send_command(self, command: str):
        """
        Send a command string terminated with '\\n'. Returns a small dict
        describing the outcome (keeps the same shape as ESP32Client).
        """
        if not command:
            return {"success": False, "error": "empty command"}

        try:
            payload = (command.strip() + "\n").encode("utf-8")
            self.ser.write(payload)
            self.ser.flush()
            return {"success": True, "sent": command}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
