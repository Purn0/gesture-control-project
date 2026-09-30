# =========================================================
# Camera
# =========================================================
CAMERA_SOURCE = 0  # 0 for webcam, or use an IP camera URL

# =========================================================
# Gesture recognition
# =========================================================
# If True, the app uses your trained ML model (models/gesture_model.pkl).
# If the model fails to load for any reason, the app AUTOMATICALLY falls
# back to the rule-based recognizer, so the demo never goes dark.
USE_ML_MODEL = True

# Predictions below this probability are treated as "Unknown".
# Raise it (e.g. 0.75) to make the system more conservative; lower it
# (e.g. 0.4) if it's rejecting too many valid gestures.
ML_CONFIDENCE_THRESHOLD = 0.60

# Debounce / cooldown
GESTURE_HOLD_FRAMES = 8            # frames a gesture must be stable
COMMAND_COOLDOWN_SECONDS = 1.5     # min seconds between identical triggers

# =========================================================
# UI
# =========================================================
WINDOW_NAME = "Gesture Control System"
FONT_SCALE = 0.8
FONT_THICKNESS = 2

# =========================================================
# Device backend
# =========================================================
# Options:
#   "simulator" -> no hardware, prints only (safe for dev)
#   "serial"    -> Arduino Uno/Nano over USB
#   "esp32"     -> HTTP to ESP32 in AP mode
#
# IMPORTANT: set this to "simulator" whenever the Arduino is NOT plugged in.
# If a ghost COM port exists (leftover driver) and "serial" is selected, the
# app can open the port but then hang on the first write.
DEVICE_BACKEND = "simulator"

# Kept for backwards compatibility with older code paths.
ENABLE_SIMULATOR = (DEVICE_BACKEND == "simulator")

# Serial (Arduino) settings
#   Windows: "COM3", "COM4", ...
#   Linux:   "/dev/ttyUSB0" or "/dev/ttyACM0"
#   macOS:   "/dev/tty.usbmodemXXXX"
SERIAL_PORT = "COM6"
SERIAL_BAUD = 9600

# ESP32 settings (only used if DEVICE_BACKEND == "esp32")
ESP32_BASE_URL = "http://192.168.4.1"

# =========================================================
# Gesture -> command mapping
# =========================================================
# The trained model recognises eight gestures (Open_Palm, Closed_Fist,
# Thumb_Up, Thumb_Down, Victory, Pointing_Up, Rock, Call_Me). Gestures not
# listed here are shown on screen but send nothing.
SUPPORTED_GESTURES = {
    "Open_Palm":   "LIGHT_ON",
    "Closed_Fist": "LIGHT_OFF",
    "Thumb_Up":    "FAN_ON",
    "Victory":     "FAN_OFF",
    # "Pointing_Up": "DOOR_TOGGLE",  # state is tracked; the sketch has no door actuator yet
}
