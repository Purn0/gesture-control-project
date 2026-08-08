import csv
import os
import sys
import time
from collections import Counter

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CSV_PATH = os.path.join(DATA_DIR, "gestures.csv")

GESTURE_KEYS = {
    ord('o'): "Open_Palm",
    ord('f'): "Closed_Fist",
    ord('t'): "Thumb_Up",
    ord('v'): "Victory",
    ord('p'): "Pointing_Up",
    ord('d'): "Thumb_Down",
    ord('c'): "Call_Me",
    ord('r'): "Rock",
}

ALL_GESTURES = [
    "Open_Palm",
    "Closed_Fist",
    "Thumb_Up",
    "Victory",
    "Pointing_Up",
    "Thumb_Down",
    "Call_Me",
    "Rock",
]

WINDOW_NAME = "Gesture Data Collector - Burst Mode"

BURST_FRAMES = 20
BURST_INTERVAL_SECONDS = 0.06
POST_BURST_COOLDOWN_SECONDS = 1.2


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def create_csv_if_not_exists():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["label"]
            for i in range(21):
                header.extend([f"x{i}", f"y{i}"])
            writer.writerow(header)


def load_existing_counts():
    counts = {gesture: 0 for gesture in ALL_GESTURES}

    if not os.path.exists(CSV_PATH):
        return counts

    try:
        df = pd.read_csv(CSV_PATH)
        if "label" not in df.columns or df.empty:
            return counts

        found = Counter(df["label"].dropna())
        for gesture in ALL_GESTURES:
            counts[gesture] = int(found.get(gesture, 0))
    except Exception as e:
        print(f"Warning: could not read CSV counts: {e}")

    return counts


def get_total_rows():
    if not os.path.exists(CSV_PATH):
        return 0

    try:
        df = pd.read_csv(CSV_PATH)
        if "label" not in df.columns or df.empty:
            return 0
        return len(df)
    except Exception as e:
        print(f"Warning: could not count CSV rows: {e}")
        return 0


def normalize_landmarks(hand_landmarks):
    coords = np.array([[lm.x, lm.y] for lm in hand_landmarks.landmark], dtype=np.float32)

    wrist = coords[0]
    coords = coords - wrist

    max_val = np.max(np.abs(coords))
    if max_val > 0:
        coords = coords / max_val

    return coords.flatten().tolist()


def save_sample(label, features):
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([label] + features)


def remove_last_n_rows(n):
    if n <= 0 or not os.path.exists(CSV_PATH):
        return 0

    try:
        df = pd.read_csv(CSV_PATH)
        if df.empty:
            return 0

        original_len = len(df)
        new_len = max(0, original_len - n)
        df = df.iloc[:new_len]

        df.to_csv(CSV_PATH, index=False)
        return original_len - new_len
    except Exception as e:
        print(f"Error while removing rows: {e}")
        return 0


def draw_ui(frame, sample_counts, total_count, hand_detected=False,
            burst_label=None, burst_saved=0, burst_total=0,
            cooldown_remaining=0.0, last_saved_label=None, message=""):
    cv2.putText(
        frame,
        "o=Open  f=Fist  t=ThumbUp  v=Victory",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "p=Point  d=ThumbDown  c=CallMe  r=Rock  z=Undo  q=Quit",
        (10, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Burst: {BURST_FRAMES} frames | Interval: {BURST_INTERVAL_SECONDS:.2f}s",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 255, 200),
        2
    )

    cv2.putText(
        frame,
        f"CSV: {CSV_PATH}",
        (10, 88),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (180, 180, 180),
        1
    )

    y = 120
    cv2.putText(
        frame,
        f"Total samples: {total_count}",
        (10, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    y += 35
    for gesture in ALL_GESTURES:
        cv2.putText(
            frame,
            f"{gesture}: {sample_counts[gesture]}",
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )
        y += 30

    status_text = "Hand detected" if hand_detected else "No hand detected"
    status_color = (0, 255, 0) if hand_detected else (0, 0, 255)
    cv2.putText(
        frame,
        status_text,
        (10, y + 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        status_color,
        2
    )

    if burst_label is not None:
        cv2.putText(
            frame,
            f"Capturing: {burst_label} [{burst_saved}/{burst_total}]",
            (10, y + 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 200, 255),
            2
        )

    if cooldown_remaining > 0:
        cv2.putText(
            frame,
            f"Cooldown: {cooldown_remaining:.1f}s",
            (10, y + 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2
        )

    if last_saved_label:
        cv2.putText(
            frame,
            f"Last burst: {last_saved_label}",
            (10, y + 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 200, 0),
            2
        )

    if message:
        cv2.putText(
            frame,
            message,
            (10, y + 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 100, 100),
            2
        )


def main():
    ensure_data_dir()
    create_csv_if_not_exists()

    sample_counts = load_existing_counts()
    total_count = get_total_rows()
    last_saved_label = None
    status_message = ""

    # keeps only current session burst history for undo
    burst_history = []

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    cooldown_until = 0.0

    print("Burst data collection started.")
    print(f"CSV path: {CSV_PATH}")
    print("Keys:")
    print("  o = Open_Palm")
    print("  f = Closed_Fist")
    print("  t = Thumb_Up")
    print("  v = Victory")
    print("  p = Pointing_Up")
    print("  d = Thumb_Down")
    print("  c = Call_Me")
    print("  r = Rock")
    print("  z = Undo last burst")
    print("  q = Quit\n")

    print("Existing counts:")
    for gesture in ALL_GESTURES:
        print(f"  {gesture}: {sample_counts[gesture]}")
    print(f"  Total: {total_count}\n")

    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Failed to read frame.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        hand_detected = False

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            hand_detected = True

        cooldown_remaining = max(0.0, cooldown_until - time.time())

        draw_ui(
            frame,
            sample_counts,
            total_count,
            hand_detected=hand_detected,
            burst_label=None,
            burst_saved=0,
            burst_total=0,
            cooldown_remaining=cooldown_remaining,
            last_saved_label=last_saved_label,
            message=status_message
        )

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        if key == ord('z'):
            if not burst_history:
                status_message = "No burst to undo in this session"
                print(status_message)
                continue

            last_burst = burst_history.pop()
            removed = remove_last_n_rows(last_burst["count"])

            if removed > 0:
                sample_counts[last_burst["label"]] -= removed
                total_count -= removed
                status_message = f"Undid last burst: {last_burst['label']} ({removed} samples)"
                print(status_message)
            else:
                status_message = "Undo failed"
                print(status_message)

            continue

        if time.time() < cooldown_until:
            continue

        if key in GESTURE_KEYS:
            label = GESTURE_KEYS[key]

            if not hand_detected:
                status_message = f"No hand detected. Burst for {label} not started."
                print(status_message)
                continue

            print(f"Starting burst capture for: {label}")
            saved_in_burst = 0
            burst_start = time.time()

            while saved_in_burst < BURST_FRAMES:
                success, burst_frame = cap.read()
                if not success:
                    print("Error: Failed to read frame during burst.")
                    break

                burst_frame = cv2.flip(burst_frame, 1)
                rgb_burst = cv2.cvtColor(burst_frame, cv2.COLOR_BGR2RGB)
                burst_results = hands.process(rgb_burst)

                burst_hand_detected = False

                if burst_results.multi_hand_landmarks:
                    burst_hand_landmarks = burst_results.multi_hand_landmarks[0]
                    mp_draw.draw_landmarks(
                        burst_frame,
                        burst_hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

                    burst_features = normalize_landmarks(burst_hand_landmarks)
                    save_sample(label, burst_features)

                    sample_counts[label] += 1
                    total_count += 1
                    saved_in_burst += 1
                    burst_hand_detected = True

                draw_ui(
                    burst_frame,
                    sample_counts,
                    total_count,
                    hand_detected=burst_hand_detected,
                    burst_label=label,
                    burst_saved=saved_in_burst,
                    burst_total=BURST_FRAMES,
                    cooldown_remaining=0.0,
                    last_saved_label=last_saved_label,
                    message=status_message
                )

                if not burst_hand_detected:
                    cv2.putText(
                        burst_frame,
                        "Hand lost - keep gesture visible",
                        (10, 470),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

                cv2.imshow(WINDOW_NAME, burst_frame)

                inner_key = cv2.waitKey(1) & 0xFF
                if inner_key == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    print(f"Dataset saved to: {CSV_PATH}")
                    return

                time.sleep(BURST_INTERVAL_SECONDS)

            if saved_in_burst > 0:
                burst_history.append({
                    "label": label,
                    "count": saved_in_burst
                })

            last_saved_label = label
            status_message = f"Saved burst: {label} ({saved_in_burst} samples)"
            cooldown_until = time.time() + POST_BURST_COOLDOWN_SECONDS

            elapsed = time.time() - burst_start
            print(
                f"Finished burst: {label} | Saved: {saved_in_burst} | "
                f"{label} total: {sample_counts[label]} | Overall total: {total_count} | "
                f"Elapsed: {elapsed:.2f}s"
            )

    cap.release()
    cv2.destroyAllWindows()
    print(f"Dataset saved to: {CSV_PATH}")


if __name__ == "__main__":
    main()