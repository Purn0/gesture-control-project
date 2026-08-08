import cv2

from config import (
    CAMERA_SOURCE,
    GESTURE_HOLD_FRAMES,
    COMMAND_COOLDOWN_SECONDS,
    WINDOW_NAME,
    DEVICE_BACKEND,
    ESP32_BASE_URL,
    SERIAL_PORT,
    SERIAL_BAUD,
    USE_ML_MODEL,
    ML_CONFIDENCE_THRESHOLD,
)
from input.camera import CameraStream
from control.debounce import GestureDebouncer
from control.command_mapper import CommandMapper
from control.state_manager import DeviceStateManager
from ui.overlay import draw_status_panel


def build_recognizer():
    """
    Prefer the trained ML model. If it fails to load for any reason
    (missing file, sklearn mismatch, bad pickle, etc.) we fall back to
    the rule-based recognizer so the live demo ALWAYS has something
    working. The current working demo is the floor, not the ceiling.
    """
    if USE_ML_MODEL:
        try:
            from recognition.ml_gesture_recognizer import MLGestureRecognizer
            recognizer = MLGestureRecognizer(
                confidence_threshold=ML_CONFIDENCE_THRESHOLD
            )
            print(f"[recognizer] ML model loaded "
                  f"(threshold={ML_CONFIDENCE_THRESHOLD})")
            return recognizer
        except Exception as e:
            print(f"[recognizer] ML model failed to load: {e}")
            print("[recognizer] Falling back to rule-based recognizer.")

    from recognition.gesture_recognizer import GestureRecognizerModule
    print("[recognizer] Using rule-based recognizer.")
    return GestureRecognizerModule()


def build_device_backend():
    """
    Returns (backend_name, backend_instance). Falls back to the simulator
    if the requested hardware can't be opened.
    """
    backend = (DEVICE_BACKEND or "simulator").lower()

    if backend == "simulator":
        from devices.simulator import DeviceSimulator
        print("[device] Backend: simulator")
        return ("simulator", DeviceSimulator())

    if backend == "serial":
        try:
            from devices.serial_client import SerialClient
            client = SerialClient(SERIAL_PORT, SERIAL_BAUD)
            print(f"[device] Backend: serial ({SERIAL_PORT} @ {SERIAL_BAUD})")
            return ("serial", client)
        except Exception as e:
            print(f"[device] Serial failed on {SERIAL_PORT}: {e}")
            print("[device] Falling back to simulator.")
            from devices.simulator import DeviceSimulator
            return ("simulator", DeviceSimulator())

    if backend == "esp32":
        from devices.esp32_client import ESP32Client
        print(f"[device] Backend: esp32 ({ESP32_BASE_URL})")
        return ("esp32", ESP32Client(ESP32_BASE_URL))

    print(f"[device] Unknown backend '{DEVICE_BACKEND}', using simulator.")
    from devices.simulator import DeviceSimulator
    return ("simulator", DeviceSimulator())


def dispatch(backend_name, backend, command, state):
    if backend_name == "simulator":
        backend.execute(command, state)
    else:
        result = backend.send_command(command)
        if not result.get("success"):
            print(f"[device] send_command failed: {result}")


def main():
    camera = CameraStream(CAMERA_SOURCE)
    if not camera.is_opened():
        print("Error: could not open camera.")
        return

    recognizer = build_recognizer()
    debouncer = GestureDebouncer(
        hold_frames=GESTURE_HOLD_FRAMES,
        cooldown_seconds=COMMAND_COOLDOWN_SECONDS
    )
    mapper = CommandMapper()
    state_manager = DeviceStateManager()

    backend_name, backend = build_device_backend()

    current_gesture = "Unknown"
    current_command = None

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Error: failed to read frame.")
                break

            frame = cv2.flip(frame, 1)

            raw_results, parsed_results = recognizer.process_with_raw(frame)
            recognizer.draw_landmarks(frame, raw_results)

            if parsed_results:
                top_result = parsed_results[0]
                current_gesture = top_result.gesture_name

                stable_gesture = debouncer.update(current_gesture)
                if stable_gesture:
                    mapped_command = mapper.map_gesture_to_command(stable_gesture)
                    if mapped_command:
                        current_command = mapped_command
                        new_state = state_manager.apply_command(mapped_command)
                        dispatch(backend_name, backend, mapped_command, new_state)
            else:
                current_gesture = "Unknown"

            draw_status_panel(
                frame,
                current_gesture,
                current_command,
                state_manager.state
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        if backend_name == "serial":
            try:
                backend.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
