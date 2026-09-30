# Gesture Control System

Real-time hand-gesture recognition from an ordinary webcam, driving real
hardware. MediaPipe finds 21 hand landmarks per frame, a Random Forest
classifies them as one of **eight gestures**, and the app debounces the
prediction and sends a command over USB serial to an Arduino that switches an
LED, a DC motor and a buzzer. Runs on a laptop CPU; no GPU needed.

This recognizer is also the camera input of
[EMG-AI-Arm](https://github.com/Purn0/emg-ai-arm), my undergraduate thesis,
where the same model drives a simulated six-degree-of-freedom robotic arm
alongside a surface-EMG classifier.

## Highlights

- **8 gestures, 96.9% accuracy on held-out capture bursts**
  (97.0 &plusmn; 2.5% over 5&times;5 grouped cross-validation), with a
  leakage-aware evaluation script (see [Evaluation](#evaluation)).
- **Own dataset**: 3,200 landmark samples (400 per gesture) recorded with a
  burst-mode collection tool (`scripts/collect_data.py`), with undo.
- **Stable commands**: confidence gate (0.60), 8-frame stability check and
  1.5 s cooldown, so a single misclassified frame does not trigger anything.
- **Fallbacks**: if the trained model cannot be loaded, a rule-based
  recognizer (landmark geometry, four gestures) takes over; if the serial
  port cannot be opened, commands go to a simulator.
- **Device backends**: simulator, USB serial (Arduino Uno/Nano), or an HTTP
  client for an ESP32 access point (the ESP32 firmware is not included).

## Gestures and actions

| Gesture     | Collect key | Command     | Hardware action                  |
|-------------|:-----------:|-------------|----------------------------------|
| Open Palm   | `o`         | LIGHT_ON    | Built-in LED (pin 13) on         |
| Closed Fist | `f`         | LIGHT_OFF   | Built-in LED off                 |
| Thumb Up    | `t`         | FAN_ON      | Motor (pin 9) on at PWM 200      |
| Victory     | `v`         | FAN_OFF     | Motor off                        |
| Pointing Up | `p`         | &mdash;     | recognized, not mapped yet       |
| Thumb Down  | `d`         | &mdash;     | recognized, not mapped yet       |
| Call Me     | `c`         | &mdash;     | recognized, not mapped yet       |
| Rock        | `r`         | &mdash;     | recognized, not mapped yet       |

A short buzzer chirp confirms every command the Arduino accepts. Map the other
four gestures in `SUPPORTED_GESTURES` (`config.py`); in EMG-AI-Arm all eight
drive the arm (up/down, grip open/close, wrist and base rotation).

## How it works

```
    webcam
      |
      v
  CameraStream -> MediaPipe Hands -> normalize -> Random Forest -> confidence gate
                  (21 landmarks)     (42 values)  (500 trees)      (>= 0.60)
                                                                        |
                                                                        v
  [simulator | SerialClient | ESP32Client] <- state manager <- command map <- debouncer
                   |                                                    (8 frames + 1.5 s)
                   v
          Arduino Uno / Nano (LED + motor + buzzer)
```

**Features.** Each frame's 21 (x, y) landmarks are shifted so the wrist is the
origin and divided by the largest absolute coordinate, which makes them
independent of where the hand is in the image and how far it is from the
camera. The result is a 42-value feature vector.

**Classifier.** A scikit-learn `RandomForestClassifier` (500 trees). Predictions
whose top class probability is below `ML_CONFIDENCE_THRESHOLD` become
`Unknown` and never trigger anything.

**Debouncing.** A gesture must be the same for `GESTURE_HOLD_FRAMES` frames in a
row, and the same command is not repeated within `COMMAND_COOLDOWN_SECONDS`.

Each layer is a small single-purpose module (`input/`, `recognition/`,
`control/`, `devices/`, `ui/`).

## Evaluation

The collection tool records each gesture instance as a **burst of 20 frames**
taken ~0.06 s apart. Frames in a burst are nearly identical, so a random
train/test split puts copies of the same moment on both sides and measures
memorization rather than recognition. `scripts/evaluate_model.py` compares the
naive split with splits that keep every burst on one side:

| Evaluation (500-tree Random Forest)              | Accuracy            | Macro-F1            |
|--------------------------------------------------|---------------------|---------------------|
| Random 80/20 row split (leaks bursts)            | 100%                | 1.000               |
| Burst-wise 80/20 split (32 held-out bursts)      | 96.9%               | 0.964               |
| 5&times;5 stratified group k-fold over bursts    | 97.0 &plusmn; 2.5%  | 0.970 &plusmn; 0.026 |

In the burst-wise split every gesture is recognized perfectly except one
held-out *Closed Fist* burst, which is read as *Call Me*: both are folded-finger
poses that differ mainly in the thumb and little finger.

Limitation: all samples come from one person (the author), so these numbers
say how well held-out *repetitions* are recognized, not how well the model
transfers to other users.

## Hardware

Target: **Arduino Uno** (a Nano works with the same sketch).

| Component    | Arduino pin | Notes                                           |
|--------------|-------------|-------------------------------------------------|
| Built-in LED | 13          | No wiring needed.                               |
| Buzzer (+)   | 8           | (-) to GND. Active or passive piezo.            |
| Motor        | 9 (PWM)     | **Use a TIP120 + flyback diode + external 5 V.** |

**Motor wiring (TIP120):**
```
  Arduino pin 9 --[1k]--+-- TIP120 base
                        |
  Motor(+)  ---- external 5V ----+
  Motor(-)  ---- TIP120 collector|
  TIP120 emitter ---- GND (common with Arduino GND)
  Flyback diode (1N4007) across motor, cathode to 5V side
```

**Serial protocol.** 9600 baud, one command per line (`LIGHT_ON\n`, ...).
The sketch prints `READY` after boot, answers `OK <command>` or
`UNKNOWN <text>`, and chirps on every accepted command.

## Setup

Python 3.11. The versions in `requirements.txt` are the tested ones; MediaPipe
0.10.9 has no wheels for Python 3.12 or newer.

```
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python scripts/train_model.py      # trains models/gesture_model.pkl (a few seconds)
python app.py                      # q or Esc quits
```

The app starts with the **simulator** backend, so it runs without any hardware.
To drive the Arduino:

1. Upload `arduino/gesture_control/gesture_control.ino` to an Uno/Nano. On
   power-up it chirps twice and prints `READY`.
2. Find the port (Windows: Device Manager, e.g. `COM3`; Linux:
   `ls /dev/ttyUSB* /dev/ttyACM*`; macOS: `ls /dev/tty.usbmodem*`).
3. In `config.py` set `DEVICE_BACKEND = "serial"` and `SERIAL_PORT`.

## Collecting your own data

```
python scripts/collect_data.py     # o f t v p d c r = capture a 20-frame burst, z = undo, q = quit
python scripts/train_model.py      # prints accuracy, classification report, confusion matrix
python scripts/evaluate_model.py   # burst-wise evaluation (does not overwrite the model)
```

`data/gestures.csv` holds one row per frame: the label, then `x0, y0, ..., x20, y20`.

## Configuration (`config.py`)

| Setting                       | Purpose                                                |
|-------------------------------|--------------------------------------------------------|
| `USE_ML_MODEL`                | `True` = trained model, with automatic rule-based fallback. |
| `ML_CONFIDENCE_THRESHOLD`     | Predictions below this become `Unknown` (default 0.60). |
| `GESTURE_HOLD_FRAMES`         | Frames a gesture must stay stable to trigger (8).      |
| `COMMAND_COOLDOWN_SECONDS`    | Minimum time between identical triggers (1.5 s).       |
| `DEVICE_BACKEND`              | `"simulator"`, `"serial"` or `"esp32"`.                |
| `SERIAL_PORT` / `SERIAL_BAUD` | Arduino connection.                                    |
| `ESP32_BASE_URL`              | ESP32 access point (`GET /command?action=<command>`).  |
| `SUPPORTED_GESTURES`          | Gesture &rarr; command map.                            |

## Repository layout

```
app.py                         main loop: camera -> recognizer -> debouncer -> device
config.py                      all settings
input/camera.py                OpenCV capture wrapper
recognition/
  ml_gesture_recognizer.py     MediaPipe + Random Forest + confidence gate
  gesture_recognizer.py        rule-based fallback (landmark geometry)
control/
  debounce.py                  hold-frames + cooldown debouncer
  command_mapper.py            gesture -> command
  state_manager.py             light / fan / door state
devices/
  simulator.py                 no hardware, keeps state only
  serial_client.py             USB serial -> Arduino (write timeout, never hangs the UI)
  esp32_client.py              HTTP -> ESP32
ui/overlay.py                  on-screen status panel
scripts/
  collect_data.py              burst-mode landmark collector
  train_model.py               trains and saves the Random Forest
  evaluate_model.py            leakage-aware evaluation
data/gestures.csv              3,200 samples, 8 gestures, 42 features
arduino/gesture_control/       firmware for Uno / Nano
```

## History

The first version (April 2026) recognized four gestures from 960 samples and
was demonstrated end to end on an Arduino driving the LED, motor and buzzer. The dataset was then re-collected with eight gestures and
3,200 samples for the EMG-AI-Arm thesis, where the model controls every
movement of a simulated arm.

## Troubleshooting

- **"Serial failed on COMx"**: wrong port, the Arduino IDE's Serial Monitor
  is open (only one program can own the port), or a charge-only cable.
- **Model not used**: the first line of output says why; if it reads "Falling
  back to rule-based recognizer", the exception is printed just above. Run
  `python scripts/train_model.py` if `models/gesture_model.pkl` is missing.
- **Motor browns out the Arduino**: the motor is on the Arduino's 5 V. Move it
  to the external supply as shown above.
- **Gesture fires only now and then**: lower `ML_CONFIDENCE_THRESHOLD`, add
  light, or bring the hand closer to the camera.

## License

MIT, see [LICENSE](LICENSE).
