from dataclasses import dataclass
from typing import Optional, List, Tuple

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class GestureResult:
    gesture_name: str
    score: float
    handedness: str
    landmarks: Optional[List[Tuple[int, int]]] = None


class GestureRecognizerModule:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

    def process_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        output = []
        if not results.multi_hand_landmarks:
            return output

        image_h, image_w, _ = frame.shape

        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            landmark_points = []
            for lm in hand_landmarks.landmark:
                x = int(lm.x * image_w)
                y = int(lm.y * image_h)
                landmark_points.append((x, y))

            handedness = "Unknown"
            if results.multi_handedness and idx < len(results.multi_handedness):
                handedness = results.multi_handedness[idx].classification[0].label

            gesture_name = self._rule_based_gesture(hand_landmarks, handedness)
            score = 1.0 if gesture_name != "Unknown" else 0.0

            output.append(
                GestureResult(
                    gesture_name=gesture_name,
                    score=score,
                    handedness=handedness,
                    landmarks=landmark_points
                )
            )

        return output

    def draw_landmarks(self, frame, raw_results):
        if raw_results.multi_hand_landmarks:
            for hand_landmarks in raw_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

    def process_with_raw(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        raw_results = self.hands.process(rgb)
        parsed = []

        if raw_results.multi_hand_landmarks:
            image_h, image_w, _ = frame.shape
            for idx, hand_landmarks in enumerate(raw_results.multi_hand_landmarks):
                landmark_points = []
                for lm in hand_landmarks.landmark:
                    x = int(lm.x * image_w)
                    y = int(lm.y * image_h)
                    landmark_points.append((x, y))

                handedness = "Unknown"
                if raw_results.multi_handedness and idx < len(raw_results.multi_handedness):
                    handedness = raw_results.multi_handedness[idx].classification[0].label

                gesture_name = self._rule_based_gesture(hand_landmarks, handedness)
                score = 1.0 if gesture_name != "Unknown" else 0.0

                parsed.append(
                    GestureResult(
                        gesture_name=gesture_name,
                        score=score,
                        handedness=handedness,
                        landmarks=landmark_points
                    )
                )

        return raw_results, parsed

    def _rule_based_gesture(self, hand_landmarks, handedness: str) -> str:
        lm = hand_landmarks.landmark

        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]

        fingers = []

        # Thumb (improved)
        thumb_open = abs(lm[4].x - lm[3].x) > 0.04
        fingers.append(1 if thumb_open else 0)

        # Other fingers (more robust)
        for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
            fingers.append(1 if lm[tip].y < lm[pip].y else 0)

        if fingers == [0, 0, 0, 0, 0]:
            return "Closed_Fist"

        if fingers == [1, 1, 1, 1, 1]:
            return "Open_Palm"

        # better thumb detection
        if fingers[0] == 1 and sum(fingers[1:]) == 0:
            return "Thumb_Up"

        if fingers[1] == 1 and fingers[2] == 1 and sum(fingers[3:]) == 0:
            return "Victory"

        return "Unknown"