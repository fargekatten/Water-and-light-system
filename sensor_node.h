#pragma once
#include <stdio.h>
// USB sensor hub: Arduino Uno WiFi Rev2. No pump and no network keys needed.
#include "sensor_config.h"

const byte MOTION_PIN = 2;       // HC-SR501 OUT: HIGH = motion
const byte SCREEN_PIN = 3;       // NO switch to GND, closed when screen is down
const byte SIMULATE_PIN = 4;     // Push button to GND
const byte DRY_LED_PIN = 7;      // LED through 330 ohm resistor to GND
const byte WATERING_LED_PIN = 8; // LED through 330 ohm resistor to GND
const byte SOIL_PIN = A0;
unsigned long lastSample = 0;
unsigned long simulationStarted = 0;
unsigned long buttonChanged = 0;
bool simulating = false;
bool previousButton = HIGH;
bool stableButton = HIGH;

void setup() {
  Serial.begin(115200);
#ifdef WIFI_SENSOR
  wifiSetup();
#endif
  pinMode(MOTION_PIN, INPUT);
  pinMode(SCREEN_PIN, INPUT_PULLUP);
  pinMode(SIMULATE_PIN, INPUT_PULLUP);
  pinMode(DRY_LED_PIN, OUTPUT);
  pinMode(WATERING_LED_PIN, OUTPUT);
}

void loop() {
  const unsigned long now = millis();
#ifdef WIFI_SENSOR
  wifiTick(now);
#endif
  const bool button = digitalRead(SIMULATE_PIN);
  if (button != previousButton) buttonChanged = now;
  previousButton = button;
  if (now - buttonChanged >= 40 && button != stableButton) {
    stableButton = button;
    if (button == LOW && !simulating) {
      simulating = true;
      simulationStarted = now;
    }
  }
  if (simulating && now - simulationStarted >= SIMULATION_MS) simulating = false;
  digitalWrite(WATERING_LED_PIN, simulating ? HIGH : LOW);
  if (now - lastSample < 100) return;
  lastSample = now;
  const int raw = analogRead(SOIL_PIN);
  const int moisture = constrain(map(raw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100), 0, 100);
  const bool dry = moisture < SOIL_DRY_PERCENT;
  digitalWrite(DRY_LED_PIN, dry ? HIGH : LOW);
  char payload[200];
  snprintf(payload, sizeof(payload),
    "{\"motion\":%d,\"screen_down\":%d,\"soil_raw\":%d,\"soil_percent\":%d,\"needs_water\":%d,\"watering_simulated\":%d}",
    digitalRead(MOTION_PIN) == HIGH ? 1 : 0, digitalRead(SCREEN_PIN) == LOW ? 1 : 0,
    raw, moisture, dry ? 1 : 0, simulating ? 1 : 0);
  Serial.println(payload);
#ifdef WIFI_SENSOR
  wifiPublish(payload, digitalRead(MOTION_PIN), digitalRead(SCREEN_PIN), now);
#endif
}
