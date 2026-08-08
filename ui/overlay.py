import cv2
from config import FONT_SCALE, FONT_THICKNESS


def draw_status_panel(frame, gesture_name, command, state):
    y = 30

    cv2.putText(
        frame,
        f"Gesture: {gesture_name}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        FONT_SCALE,
        (0, 255, 0),
        FONT_THICKNESS
    )

    y += 35
    cv2.putText(
        frame,
        f"Command: {command if command else 'None'}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        FONT_SCALE,
        (255, 255, 0),
        FONT_THICKNESS
    )

    y += 35
    cv2.putText(
        frame,
        f"Light: {'ON' if state['light'] else 'OFF'}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        FONT_SCALE,
        (255, 255, 255),
        FONT_THICKNESS
    )

    y += 35
    cv2.putText(
        frame,
        f"Fan: {'ON' if state['fan'] else 'OFF'}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        FONT_SCALE,
        (255, 255, 255),
        FONT_THICKNESS
    )

    y += 35
    cv2.putText(
        frame,
        f"Door: {'LOCKED' if state['door_locked'] else 'UNLOCKED'}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        FONT_SCALE,
        (255, 255, 255),
        FONT_THICKNESS
    )