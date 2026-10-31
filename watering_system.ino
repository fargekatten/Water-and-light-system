#define TS_ENABLE_SSL
#include <WiFiNINA.h>
#include <ThingSpeak.h>



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