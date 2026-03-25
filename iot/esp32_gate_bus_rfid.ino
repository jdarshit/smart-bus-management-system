/**
 * Smart Bus Management System — ESP32 Gate Bus-RFID Scanner
 *
 * Purpose:
 *   Scan BUS RFID cards at college gate and POST to Flask /api/rfid
 *   Payload: {"uid": "72 3C 14 5C"}
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// ---------------- USER CONFIG ----------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_IP     = "192.168.1.100"; // PC/LAN IP
const int   SERVER_PORT   = 5000;
String SERVER_URL = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/api/rfid";

#define SS_PIN   5
#define RST_PIN  22
#define LED_PIN  2

const unsigned long DEBOUNCE_MS = 5000;
const int HTTP_TIMEOUT_MS = 8000;

MFRC522 rfid(SS_PIN, RST_PIN);
String lastUID = "";
unsigned long lastScanMs = 0;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("[WiFi] Connecting");
  int attempt = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
    attempt++;
    if (attempt > 40) {
      Serial.println("\n[WiFi] Timeout - restarting");
      ESP.restart();
    }
  }
  Serial.println();
  Serial.print("[WiFi] Connected IP: ");
  Serial.println(WiFi.localIP());
}

String getUIDSpaced() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) uid += " ";
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

int postBusRFID(const String& uid) {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(HTTP_TIMEOUT_MS);

  StaticJsonDocument<128> req;
  req["uid"] = uid;

  String body;
  serializeJson(req, body);

  Serial.print("[HTTP] POST ");
  Serial.println(body);

  int code = http.POST(body);
  String response = http.getString();

  Serial.print("[HTTP] Code: ");
  Serial.println(code);
  Serial.print("[HTTP] Resp: ");
  Serial.println(response);

  if (code == 201) {
    StaticJsonDocument<256> json;
    if (deserializeJson(json, response) == DeserializationError::Ok) {
      Serial.print("[ARRIVAL] Bus: ");
      Serial.print(json["bus_number"].as<String>());
      Serial.print(" | Plate: ");
      Serial.print(json["license_plate"].as<String>());
      Serial.print(" | Driver: ");
      Serial.print(json["driver_name"].as<String>());
      Serial.print(" | Status: ");
      Serial.println(json["arrival_status"].as<String>());
    }
  }

  http.end();
  return code;
}

void blink(int count) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}

void setup() {
  Serial.begin(115200);
  delay(400);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  SPI.begin();
  rfid.PCD_Init();

  Serial.println("\n=== Bus RFID Gate Scanner ===");
  connectWiFi();
  Serial.println("[System] Ready. Scan BUS RFID cards...");
  blink(3);
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  String uid = getUIDSpaced();
  unsigned long now = millis();

  if (uid == lastUID && (now - lastScanMs) < DEBOUNCE_MS) {
    Serial.println("[DEBOUNCE] Duplicate scan skipped");
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return;
  }

  lastUID = uid;
  lastScanMs = now;

  Serial.print("[RFID] UID: ");
  Serial.println(uid);

  int code = postBusRFID(uid);
  if (code == 201) blink(2);
  else blink(1);

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(300);
}
