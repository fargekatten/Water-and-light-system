#define TS_ENABLE_SSL
#include <WiFiNINA.h>
#include <ThingSpeak.h>
#if __has_include("arduino_secrets.h")
#include "arduino_secrets.h"
#else
#include "arduino_secrets.example.h"
#endif

const char* ssid = SECRET_SSID;
const char* pass = SECRET_PASS;
const unsigned long channelNumber = SECRET_CHANNEL_NUMBER;
const char* writeAPIKey = SECRET_WRITE_API_KEY;



WiFiSSLClient client;

void setup() {
  Serial.begin(115200);

  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("WiFi module not found.");
    while (true) {}
  }

  ThingSpeak.begin(client);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connecting to Wi-Fi");

    while (WiFi.status() != WL_CONNECTED) {
      WiFi.begin(ssid, pass);
      delay(5000);
      Serial.print(".");
    }

    Serial.println("\nWi-Fi connected.");
  }

  int temperatureRaw = analogRead(A2);
  int lightRaw = analogRead(A1);
  int soundRaw = analogRead(A0);

  ThingSpeak.setField(1, temperatureRaw);
  ThingSpeak.setField(2, lightRaw);
  ThingSpeak.setField(3, soundRaw);

  int result = ThingSpeak.writeFields(channelNumber, writeAPIKey);

  if (result == 200) {
    Serial.println("ThingSpeak update successful.");
  } else {
    Serial.print("ThingSpeak error: ");
    Serial.println(result);
  }

  delay(20000);
}