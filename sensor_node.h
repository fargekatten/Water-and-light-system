#pragma once
#include <stdio.h>
#include "sensor_config.h"

const byte MOTION_PIN = 2;       // HC-SR501 OUT: HIGH = motion
const byte SCREEN_PIN = 3;       // Normally-open reed switch to GND; closed when screen is down
const byte SIMULATE_PIN = 4;     // Push button to GND
const byte DRY_LED_PIN = 7;      // LED through 330 ohm resistor to GND
const byte WATERING_LED_PIN = 8; // LED through 330 ohm resistor to GND
const byte SOIL_PIN = A0;        // Capacitive soil-moisture analog output
const byte LIGHT_PIN = A1;       // Grove light sensor analog output; place at the window
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

  const int soilRaw = analogRead(SOIL_PIN);
  const int soilPercent = constrain(map(soilRaw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100), 0, 100);
  const bool needsWater = soilPercent < SOIL_DRY_PERCENT;
  const int lightRaw = analogRead(LIGHT_PIN);
  const bool lightBright = lightRaw >= LIGHT_BRIGHT_THRESHOLD;
  const int motion = digitalRead(MOTION_PIN) == HIGH ? 1 : 0;
  const int screenDown = digitalRead(SCREEN_PIN) == LOW ? 1 : 0;

  digitalWrite(DRY_LED_PIN, needsWater ? HIGH : LOW);
  char payload[256];
  snprintf(payload, sizeof(payload),
    "{\"motion\":%d,\"screen_down\":%d,\"light_raw\":%d,\"light_bright\":%d,\"soil_raw\":%d,\"soil_percent\":%d,\"needs_water\":%d,\"watering_simulated\":%d}",
    motion, screenDown, lightRaw, lightBright ? 1 : 0, soilRaw, soilPercent,
    needsWater ? 1 : 0, simulating ? 1 : 0);
  Serial.println(payload);
#ifdef WIFI_SENSOR
  wifiPublish(payload, motion, screenDown, lightBright ? 1 : 0, now);
#endif
}
