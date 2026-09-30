// Gesture Control System - firmware for Arduino Uno / Nano.
//
// app.py sends one newline-terminated command per recognised gesture over
// USB serial (9600 baud). This sketch drives the demo hardware:
//
//   LIGHT_ON  / LIGHT_OFF  -> built-in LED (pin 13)
//   FAN_ON    / FAN_OFF    -> DC motor via a TIP120 on PWM pin 9
//
// Every accepted command plays a short chirp on the buzzer (pin 8) and is
// echoed back as "OK <command>"; anything else is answered "UNKNOWN <text>".
// On power-up the sketch plays a two-tone boot chirp and prints "READY".
//
// tone() uses Timer2 on the Uno, so it does not disturb PWM on pin 9 (Timer1).

const int LED_PIN = 13;
const int BUZZER_PIN = 8;
const int MOTOR_PIN = 9;

const int MOTOR_PWM = 200;            // fan speed, 0-255
const unsigned int CHIRP_HZ = 2000;
const unsigned int CHIRP_MS = 60;
const unsigned int MAX_COMMAND = 31;  // longest accepted command, in characters

String line;

void chirp() {
  tone(BUZZER_PIN, CHIRP_HZ, CHIRP_MS);
}

void handleCommand(const String &cmd) {
  if (cmd == "LIGHT_ON") {
    digitalWrite(LED_PIN, HIGH);
  } else if (cmd == "LIGHT_OFF") {
    digitalWrite(LED_PIN, LOW);
  } else if (cmd == "FAN_ON") {
    analogWrite(MOTOR_PIN, MOTOR_PWM);
  } else if (cmd == "FAN_OFF") {
    analogWrite(MOTOR_PIN, 0);
  } else {
    Serial.print("UNKNOWN ");
    Serial.println(cmd);
    return;
  }

  chirp();
  Serial.print("OK ");
  Serial.println(cmd);
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  analogWrite(MOTOR_PIN, 0);

  Serial.begin(9600);
  line.reserve(MAX_COMMAND + 1);

  tone(BUZZER_PIN, 1500, 80);
  delay(120);
  tone(BUZZER_PIN, 2200, 80);
  delay(100);

  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\n') {
      line.trim();
      if (line.length() > 0) {
        handleCommand(line);
      }
      line = "";
    } else if (c != '\r' && line.length() < MAX_COMMAND) {
      line += c;
    }
  }
}
