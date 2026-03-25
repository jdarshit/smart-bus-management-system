#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <time.h>

// ===== WiFi / API =====
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
const char* API_URL   = "http://192.168.1.100:5000/api/rfid";

// ===== RFID (MFRC522) =====
#define SS_PIN   5
#define RST_PIN  22
MFRC522 mfrc522(SS_PIN, RST_PIN);

// ===== Fast network tuning =====
static const uint32_t WIFI_RETRY_MS = 3000;
static const uint32_t HTTP_TIMEOUT_MS = 1500;   // < 2 sec as requested
static const uint8_t  HTTP_RETRY_COUNT = 3;

// ===== Local buffer (memory queue) =====
struct ScanEvent {
  String uid;
  uint32_t capturedAtMs;
};

static const int SCAN_QUEUE_CAPACITY = 128;
ScanEvent scanQueue[SCAN_QUEUE_CAPACITY];
int queueHead = 0;
int queueTail = 0;
int queueSize = 0;

WiFiClient wifiClient;
HTTPClient http;

uint32_t lastWifiAttemptMs = 0;
uint32_t lastNtpSyncMs = 0;

bool enqueueScan(const String& uid) {
  if (queueSize >= SCAN_QUEUE_CAPACITY) {
    queueHead = (queueHead + 1) % SCAN_QUEUE_CAPACITY;
    queueSize--;
  }
  scanQueue[queueTail] = {uid, millis()};
  queueTail = (queueTail + 1) % SCAN_QUEUE_CAPACITY;
  queueSize++;
  return true;
}

bool dequeueScan(ScanEvent& out) {
  if (queueSize == 0) return false;
  out = scanQueue[queueHead];
  queueHead = (queueHead + 1) % SCAN_QUEUE_CAPACITY;
  queueSize--;
  return true;
}

String uidToString(MFRC522::Uid* uid) {
  String out = "";
  for (byte i = 0; i < uid->size; i++) {
    if (i > 0) out += " ";
    if (uid->uidByte[i] < 0x10) out += "0";
    out += String(uid->uidByte[i], HEX);
  }
  out.toUpperCase();
  return out;
}

void connectWiFiNonBlocking() {
  if (WiFi.status() == WL_CONNECTED) return;

  uint32_t now = millis();
  if (now - lastWifiAttemptMs < WIFI_RETRY_MS) return;

  lastWifiAttemptMs = now;
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void syncNtpIfNeeded() {
  uint32_t now = millis();
  if (now - lastNtpSyncMs < 60000UL) return;
  lastNtpSyncMs = now;

  if (WiFi.status() == WL_CONNECTED) {
    configTime(19800, 0, "pool.ntp.org", "time.nist.gov"); // Asia/Kolkata UTC+5:30
  }
}

bool postUidFast(const String& uid) {
  if (WiFi.status() != WL_CONNECTED) return false;

  const String payload = String("{\"uid\":\"") + uid + "\"}"; // minimal payload

  for (uint8_t attempt = 0; attempt < HTTP_RETRY_COUNT; attempt++) {
    if (!http.begin(wifiClient, API_URL)) {
      delay(20);
      continue;
    }

    http.setConnectTimeout(HTTP_TIMEOUT_MS);
    http.setTimeout(HTTP_TIMEOUT_MS);
    http.setReuse(true); // keep-alive where supported
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Connection", "keep-alive");

    int statusCode = http.POST((uint8_t*)payload.c_str(), payload.length());
    http.end();

    if (statusCode == 200 || statusCode == 201) {
      return true;
    }

    delay(30);
  }

  return false;
}

void flushBufferedScans() {
  if (WiFi.status() != WL_CONNECTED || queueSize == 0) return;

  const int maxFlushPerLoop = 6;
  int sent = 0;
  while (queueSize > 0 && sent < maxFlushPerLoop) {
    ScanEvent ev;
    if (!dequeueScan(ev)) break;

    if (!postUidFast(ev.uid)) {
      enqueueScan(ev.uid);
      break;
    }
    sent++;
  }
}

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  WiFi.setAutoReconnect(true);
  WiFi.persistent(false);
  connectWiFiNonBlocking();
  syncNtpIfNeeded();
}

void loop() {
  connectWiFiNonBlocking();
  syncNtpIfNeeded();
  flushBufferedScans();

  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    delay(5);
    return;
  }

  String uid = uidToString(&mfrc522.uid);

  if (!postUidFast(uid)) {
    enqueueScan(uid);
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(35);
}
