import time
from collections import deque


class GestureDebouncer:
    def __init__(self, hold_frames=8, cooldown_seconds=1.5):
        self.hold_frames = hold_frames
        self.cooldown_seconds = cooldown_seconds
        self.buffer = deque(maxlen=hold_frames)
        self.last_trigger_time = 0
        self.last_triggered_gesture = None

    def update(self, gesture_name: str):
        now = time.time()
        self.buffer.append(gesture_name)

        if len(self.buffer) < self.hold_frames:
            return None

        if len(set(self.buffer)) != 1:
            return None

        stable_gesture = self.buffer[0]

        if stable_gesture == "Unknown":
            return None

        if (
            stable_gesture == self.last_triggered_gesture
            and (now - self.last_trigger_time) < self.cooldown_seconds
        ):
            return None

        self.last_triggered_gesture = stable_gesture
        self.last_trigger_time = now
        return stable_gesture