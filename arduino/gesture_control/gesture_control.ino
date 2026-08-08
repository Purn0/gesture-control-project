const int EMG_PIN = A0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  unsigned long t = millis();

  int emg = analogRead(EMG_PIN);

  // Format expected by your Python app:
  // t_ms,ch1,ch2
  Serial.print(t);
  Serial.print(",");
  Serial.print(emg);
  Serial.print(",");
  Serial.println(emg);

  delay(5);   // ~200 Hz
}