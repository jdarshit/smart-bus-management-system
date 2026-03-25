/*
 * Smart Bus Management System
 * ESP32 + NEO-6M GPS  →  Flask /api/gps
 *
 * Hardware connections
 * ────────────────────
 *   NEO-6M TX  →  ESP32 GPIO 16 (RX2)
 *   NEO-6M RX  →  ESP32 GPIO 17 (TX2)
 *   NEO-6M VCC →  3.3 V
 *   NEO-6M GND →  GND
 *
 * Combined RFID + GPS sketch
 * ──────────────────────────
 * If this bus ALSO has an MFRC522 RFID reader (student card scanning),
 * include the RFID section below and POST to /api/rfid with both UID
 * and the current GPS coordinates.
 *
 * Libraries (install via Arduino Library Manager)
 * ────────────────────────────────────────────────
 *   TinyGPS++     by Mikal Hart
 *   ArduinoJson   by Benoit Blanchon  (v6)
 *   WiFi          (bundled with ESP32 core)
 *   HTTPClient    (bundled with ESP32 core)
 * ------------------------------------------------------------------ */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

// ── WiFi credentials ───────────────────────────────────────────────
const char* WIFI_SSID     = "YourWiFiSSID";
const char* WIFI_PASSWORD = "YourWiFiPassword";

// ── Flask server ───────────────────────────────────────────────────
// Replace with your server IP (local) or deployed URL
const char* SERVER_GPS_URL  = "http://192.168.1.100:5000/api/gps";
const char* SERVER_RFID_URL = "http://192.168.1.100:5000/api/rfid";

// ── Bus identity ───────────────────────────────────────────────────
const char* BUS_ID = "BUS_01";

// ── GPS post interval (milliseconds) ──────────────────────────────
const unsigned long GPS_POST_INTERVAL_MS = 10000;  // 10 seconds

// ── Serial2 for NEO-6M ────────────────────────────────────────────
HardwareSerial gpsSerial(2);          // UART2
TinyGPSPlus    gps;

unsigned long lastPostMs = 0;
float         lastLat    = 0.0f;
float         lastLng    = 0.0f;

// ──────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);  // RX=16, TX=17

  Serial.println("[BOOT] ESP32 GPS Tracker starting…");

  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WiFi] Connecting");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 20000) {
    delay(500);
    Serial.print('.');
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WiFi] FAILED – will retry each loop");
  }
}

// ──────────────────────────────────────────────────────────────────
void loop() {
  // Feed GPS serial data to TinyGPS++
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  unsigned long now = millis();

  if (now - lastPostMs >= GPS_POST_INTERVAL_MS) {
    lastPostMs = now;

    if (WiFi.status() != WL_CONNECTED) {
      WiFi.reconnect();
      Serial.println("[WiFi] Reconnecting…");
      return;
    }

    if (gps.location.isValid() && gps.location.isUpdated()) {
      lastLat = gps.location.lat();
      lastLng = gps.location.lng();

      Serial.printf("[GPS ] Fix: lat=%.6f  lng=%.6f  sats=%d\n",
                    lastLat, lastLng, gps.satellites.value());

      postGPSFix(lastLat, lastLng);
    } else {
      Serial.println("[GPS ] Waiting for fix…"
                     + String(gps.satellites.isValid()
                               ? " Sats: " + String(gps.satellites.value())
                               : " No signal"));
    }
  }
}

// ──────────────────────────────────────────────────────────────────
// POST GPS fix to Flask
// ──────────────────────────────────────────────────────────────────
void postGPSFix(float lat, float lng) {
  HTTPClient http;
  http.begin(SERVER_GPS_URL);
  http.addHeader("Content-Type", "application/json");

  // Build JSON payload
  StaticJsonDocument<200> doc;
  doc["bus_id"]    = BUS_ID;
  doc["latitude"]  = lat;
  doc["longitude"] = lng;
  // Omit "timestamp" → server records arrival time automatically

  String body;
  serializeJson(doc, body);

  int code = http.POST(body);

  if (code == 200) {
    Serial.printf("[GPS ] OK  200  posted lat=%.6f lng=%.6f\n", lat, lng);
  } else {
    Serial.printf("[GPS ] FAIL  HTTP %d\n", code);
    Serial.println("[GPS ] Response: " + http.getString());
  }
  http.end();
}

// ──────────────────────────────────────────────────────────────────
// OPTIONAL: post RFID scan WITH current GPS coords to /api/rfid
// Call this from your RFID interrupt / polling loop.
// ──────────────────────────────────────────────────────────────────
void postRFIDWithGPS(const char* uid) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(SERVER_RFID_URL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["uid"]       = uid;
  doc["bus_id"]    = BUS_ID;
  doc["latitude"]  = lastLat;
  doc["longitude"] = lastLng;
  // "timestamp" omitted → server uses current UTC

  String body;
  serializeJson(doc, body);

  int code = http.POST(body);
  Serial.printf("[RFID] %s  UID=%s  HTTP %d\n",
                code == 200 ? "OK " : "ERR", uid, code);
  if (code != 200) {
    Serial.println("[RFID] Response: " + http.getString());
  }
  http.end();
}
