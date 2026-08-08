# Gesture Control System

Control real hardware with hand gestures. A webcam feeds MediaPipe for hand
landmark detection; a trained RandomForest classifier interprets the 21
landmarks as one of four gestures; the app debounces the prediction and
sends a command over USB serial to an Arduino that drives an LED, a buzzer,
and a small motor.

A rule-based recognizer (pure geometry on the landmarks) is kept as an
automatic fallback so the demo still works if the ML model fails to load.

## Gestures and actions

| Gesture     | Command     | Hardware action                 |
|-------------|-------------|----------------------------------|
| Open Palm   | LIGHT_ON    | Built-in LED (pin 13) ON         |
| Closed Fist | LIGHT_OFF   | Built-in LED OFF                 |
| Thumb Up    | FAN_ON      | Motor (pin 9) ON at PWM ~200     |
| Victory     | FAN_OFF     | Motor OFF                        |

A short buzzer chirp plays on every recognized command as audible feedback.

## Architecture

```
    webcam
      |
      v
  CameraStream  ->  recognizer  ->  debouncer  ->  CommandMapper
                    (ML or rule)    (8 frames +     (gesture -> cmd)
                                     1.5s cooldown)        |
                                                           v
                                                   DeviceStateManager
                                                           |
                                                           v
                                        [simulator | SerialClient | ESP32]
                                                           |
                                                           v
                                                   Arduino Uno / Nano
                                                   (LED + buzzer + motor)
```

Each layer is a small, single-responsibility module under a dedicated
package (`input/`, `recognition/`, `control/`, `devices/`, `ui/`).

## Repository layout

```
gesture_control_project/
├── app.py                        # main loop
├── config.py                     # all tunable settings
├── requirements.txt
├── README.md
│
├── input/
│   └── camera.py                 # OpenCV VideoCapture wrapper
│
├── recognition/
│   ├── gesture_recognizer.py     # rule-based (MediaPipe + geometry)
│   └── ml_gesture_recognizer.py  # trained RandomForest (+ confidence gate)
│
├── control/
│   ├── command_mapper.py         # gesture -> command
│   ├── debounce.py               # hold + cooldown debouncer
│   └── state_manager.py          # tracks LED/fan/door state
│
├── devices/
│   ├── simulator.py              # prints only
│   ├── serial_client.py          # USB serial -> Arduino
│   └── esp32_client.py           # HTTP -> ESP32 in AP mode
│
├── ui/
│   └── overlay.py                # OpenCV text overlays
│
├── scripts/
│   ├── collect_data.py           # burst-mode landmark collector
│   └── train_model.py            # RandomForest trainer
│
├── data/
│   └── gestures.csv              # label + 42 (x,y) landmark features
│
├── models/
│   └── gesture_model.pkl         # trained RandomForestClassifier
│
└── arduino/
    └── gesture_control/
        └── gesture_control.ino   # firmware for Uno / Nano
```

## Hardware

Primary target: **Arduino Uno** (Nano works with the same sketch).

| Component        | Arduino pin | Notes                                           |
|------------------|-------------|--------------------------------------------------|
| Built-in LED     | 13          | No wiring needed.                               |
| Buzzer (+)       | 8           | (-) to GND. Active or passive piezo works.      |
| Motor            | 9 (PWM)     | **Use a TIP120 + flyback diode + external 5V.** |

**Motor wiring (TIP120):**
```
  Arduino pin 9 --[1k]--+-- TIP120 base
                        |
  Motor(+)  ---- external 5V ----+
  Motor(-)  ---- TIP120 collector|
  TIP120 emitter ---- GND (common with Arduino GND)
  Flyback diode (1N4007) across motor, cathode to 5V side
```

If no transistor is on hand, replace the motor with a small 5V servo
(signal -> pin 9, +5V, GND) — the Arduino can power it directly.

## Setup

1. Install Python deps:
   ```
   pip install -r requirements.txt
   ```

2. Upload the Arduino sketch
   (`arduino/gesture_control/gesture_control.ino`) to an Uno/Nano.
   On power-up it plays a short boot chirp and prints `READY` on serial.

3. Find your Arduino serial port and set it in `config.py`:
   - Windows: look in Device Manager (e.g. `COM3`)
   - Linux: `ls /dev/ttyUSB* /dev/ttyACM*`
   - macOS: `ls /dev/tty.usbmodem*`

4. Run the app:
   ```
   python app.py
   ```

Press `q` or `Esc` to quit.

## Configuration quick reference (`config.py`)

| Setting                    | Purpose                                              |
|----------------------------|------------------------------------------------------|
| `USE_ML_MODEL`             | `True` = use trained model; auto-falls back on fail. |
| `ML_CONFIDENCE_THRESHOLD`  | Predictions below this -> `Unknown`.                 |
| `DEVICE_BACKEND`           | `"simulator"`, `"serial"`, or `"esp32"`.             |
| `SERIAL_PORT` / `SERIAL_BAUD` | Arduino connection settings.                      |
| `GESTURE_HOLD_FRAMES`      | Frames a gesture must be stable to trigger.          |
| `COMMAND_COOLDOWN_SECONDS` | Min seconds between identical triggers.              |
| `SUPPORTED_GESTURES`       | Gesture -> command dict.                             |

## Training the model

```
python scripts/collect_data.py   # press o/f/t/v to capture 20-frame bursts
python scripts/train_model.py    # prints accuracy + classification report
```

Dataset: 960 rows across 4 classes, 42 features per row
(21 landmarks × (x, y), wrist-centered and scale-normalized).

## Troubleshooting

- **"Serial failed on COMx"** - wrong port, Arduino IDE's Serial Monitor
  is open (only one client can own the port at a time), or the cable is
  a charge-only cable.
- **Model not being used** - check the first line of app output; if it
  says "Falling back to rule-based recognizer", there's an exception
  printed right above it.
- **Motor brown-outs the Arduino** - you're driving the motor off the
  Arduino 5V. Move it to the external supply as described above.
- **Gesture only fires occasionally** - lower `ML_CONFIDENCE_THRESHOLD`
  in `config.py`, or increase lighting / move hand closer to camera.
