#pragma once
#include <WiFiNINA.h>
#include <PubSubClient.h>
#if __has_include("arduino_secrets.h")
#include "arduino_secrets.h"
#else
#include "arduino_secrets.example.h"
#endif
WiFiSSLClient tlsClient;
PubSubClient mqtt(tlsClient);
unsigned long lastConnectAttempt = 0;
unsigned long lastPublished = 0;
bool triedConnect = false;
int previousMotion = -1;
int previousScreen = -1;

void wifiSetup() {
  mqtt.setServer(MQTT_HOST, 8883);
  mqtt.setBufferSize(512);
  mqtt.setSocketTimeout(1);
  // WiFiNINA must trust the broker CA; provision via Arduino certificate tool.
  // Never replace WiFiSSLClient with an unencrypted or unverified connection.
}
void wifiTick(unsigned long now) {
  if (mqtt.connected()) { mqtt.loop(); return; }
  if (triedConnect && now-lastConnectAttempt < 10000) return;
  triedConnect = true;
  lastConnectAttempt = now;
  if (WiFi.status() != WL_CONNECTED) WiFi.begin(SECRET_SSID, SECRET_PASS);
  if (WiFi.status() == WL_CONNECTED) {
    if (mqtt.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASS)) {
      previousMotion = -1;
      previousScreen = -1;
    }
  }
}
void wifiPublish(const char* payload, int motion, int screen, unsigned long now) {
  if (!mqtt.connected()) return;
  if (motion == previousMotion && screen == previousScreen && now-lastPublished < 1000) return;
  if (mqtt.publish(MQTT_TOPIC, payload, false)) {
    previousMotion = motion;
    previousScreen = screen;
    lastPublished = now;
  }
}
