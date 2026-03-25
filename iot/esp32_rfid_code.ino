/**
 * Smart Bus Management System — ESP32 RFID Gate Scanner
 * =======================================================
 * Hardware: ESP32 Dev Board + MFRC522 RFID Reader
 *
 * Wiring (MFRC522 → ESP32)
 * -------------------------
 *   SDA  (SS)  → GPIO  5
 *   SCK        → GPIO 18
 *   MOSI       → GPIO 23
 *   MISO       → GPIO 19
 *   IRQ        → (not connected)
 *   GND        → GND
 *   RST        → GPIO 22
 *   3.3V       → 3.3V   ← IMPORTANT: do NOT use 5V, it will damage the module
 *
 * Required Libraries (install via Arduino Library Manager)
 * ----------------------------------------------------------
 *   - MFRC522  by GithubCommunity  (search "MFRC522")
 *   - ArduinoJson by Benoit Blanchon (search "ArduinoJson", install v7)
 *   - WiFi and HTTPClient are bundled with the ESP32 board package
 *
 * Board Setup
 * -----------
 *   File → Preferences → Additional boards URL:
 *     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
 *   Tools → Board → ESP32 Arduino → "ESP32 Dev Module"
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────────────────────────────────────
// USER CONFIGURATION  ← Edit these before uploading
// ─────────────────────────────────────────────────────────────────────────────

// Wi-Fi credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Flask server address — use the PC's LAN IP (run `ipconfig` on Windows)
// Make sure both ESP32 and PC are on the SAME Wi-Fi network
const char* SERVER_IP   = "192.168.1.100";   // ← Change this
const int   SERVER_PORT = 5000;

// Full URL for the bus-arrival endpoint
// e.g. "http://192.168.1.100:5000/api/bus-arrival"
String SERVER_URL = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/api/bus-arrival";

// ─────────────────────────────────────────────────────────────────────────────
// PIN DEFINITIONS
// ─────────────────────────────────────────────────────────────────────────────

#define SS_PIN   5   // SDA / Chip Select
#define RST_PIN  22
#define LED_PIN  2   // Built-in LED on most ESP32 boards (optional feedback)

// ─────────────────────────────────────────────────────────────────────────────
// TUNABLES
// ─────────────────────────────────────────────────────────────────────────────

// Minimum milliseconds between two accepted scans of the SAME card
// Prevents double-logging from a bus slowing down at the gate
const unsigned long DEBOUNCE_MS = 5000;  // 5 seconds

// HTTP request timeout in milliseconds
const int HTTP_TIMEOUT_MS = 8000;

// ─────────────────────────────────────────────────────────────────────────────
// GLOBALS
// ─────────────────────────────────────────────────────────────────────────────

MFRC522 rfid(SS_PIN, RST_PIN);

String  lastUID       = "";
unsigned long lastScanTime = 0;

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Connect to WiFi and block until connected (or retry every 2 s).
 */
void connectWiFi() {
    Serial.print("[WiFi] Connecting to ");
    Serial.print(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempt = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        attempt++;
        if (attempt > 40) {         // 20 s timeout → restart
            Serial.println("\n[WiFi] Timeout — restarting ESP32");
            ESP.restart();
        }
    }

    Serial.println();
    Serial.print("[WiFi] Connected! IP: ");
    Serial.println(WiFi.localIP());
}

/**
 * Read the current card's UID and return it as an uppercase hex string.
 * e.g. "AB12CD34"
 */
String getUID() {
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) uid += "0";   // zero-pad single hex digit
        uid += String(rfid.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();
    return uid;
}

/**
 * POST the scanned RFID UID to the Flask /api/bus-arrival endpoint.
 * Returns the HTTP status code (201 = recorded, 409 = duplicate, etc.)
 */
int postArrival(const String& uid) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[HTTP] WiFi disconnected — reconnecting...");
        connectWiFi();
    }

    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    // Build JSON payload: {"rfid_uid": "AB12CD34"}
    StaticJsonDocument<64> doc;
    doc["rfid_uid"] = uid;
    String payload;
    serializeJson(doc, payload);

    Serial.print("[HTTP] POST → ");
    Serial.println(payload);

    int httpCode = http.POST(payload);

    if (httpCode > 0) {
        String response = http.getString();
        Serial.print("[HTTP] Response (");
        Serial.print(httpCode);
        Serial.print("): ");
        Serial.println(response);

        // Parse and summarise the response
        StaticJsonDocument<256> resp;
        DeserializationError err = deserializeJson(resp, response);
        if (!err) {
            if (httpCode == 201) {
                Serial.print("[OK]  Bus: ");
                Serial.print(resp["bus_number"].as<String>());
                Serial.print("  Route: ");
                Serial.print(resp["route_name"].as<String>());
                Serial.print("  Status: ");
                Serial.println(resp["status"].as<String>());
            } else if (httpCode == 409) {
                Serial.println("[INFO] Duplicate scan — skipped by server.");
            } else if (httpCode == 404) {
                Serial.println("[WARN] RFID not registered in database.");
            } else if (httpCode == 400) {
                Serial.println("[WARN] Invalid JSON payload or empty RFID UID.");
            }
        }
    } else {
        Serial.print("[HTTP] Error: ");
        Serial.println(http.errorToString(httpCode));
    }

    http.end();
    return httpCode;
}

/**
 * Blink the built-in LED to give visual feedback.
 * count × 100 ms on / 100 ms off.
 */
void blinkLED(int count) {
    for (int i = 0; i < count; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);
        delay(100);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    delay(500);   // allow serial monitor to open

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    Serial.println("╔══════════════════════════════════╗");
    Serial.println("║  Smart Bus RFID Gate Scanner     ║");
    Serial.println("╚══════════════════════════════════╝");

    // Init SPI and MFRC522
    SPI.begin();
    rfid.PCD_Init();
    rfid.PCD_DumpVersionToSerial();   // prints firmware version; useful for confirming wiring

    Serial.print("[RFID] Reader ready. Firmware: ");

    // Connect to Wi-Fi
    connectWiFi();

    Serial.println("[System] Waiting for bus RFID tags...\n");
    blinkLED(3);   // 3 blinks = ready
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN LOOP
// ─────────────────────────────────────────────────────────────────────────────

void loop() {
    // ── 1. Reconnect Wi-Fi if dropped ────────────────────────────────────────
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Connection lost — reconnecting...");
        connectWiFi();
    }

    // ── 2. Wait for a card to be present ────────────────────────────────────
    if (!rfid.PICC_IsNewCardPresent()) {
        return;   // no card in field yet
    }

    if (!rfid.PICC_ReadCardSerial()) {
        return;   // failed to read the card (noise, partial read)
    }

    // ── 3. Debounce — same card scanned too quickly ──────────────────────────
    String uid = getUID();
    unsigned long now = millis();

    if (uid == lastUID && (now - lastScanTime) < DEBOUNCE_MS) {
        Serial.print("[DEBOUNCE] Same card within debounce window (");
        Serial.print((now - lastScanTime) / 1000);
        Serial.println(" s) — skipped.");
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
        return;
    }

    lastUID      = uid;
    lastScanTime = now;

    Serial.print("\n[RFID] Card detected UID: ");
    Serial.println(uid);

    // ── 4. POST to Flask server ───────────────────────────────────────────────
    int code = postArrival(uid);

    // ── 5. LED feedback ───────────────────────────────────────────────────────
    if (code == 201) {
        blinkLED(2);   // 2 quick blinks = success
    } else if (code == 409) {
        blinkLED(1);   // 1 blink = duplicate
    } else {
        // Error: hold LED on for 500 ms
        digitalWrite(LED_PIN, HIGH);
        delay(500);
        digitalWrite(LED_PIN, LOW);
    }

    // ── 6. Halt card so the same card isn't re-read in the next iteration ────
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();

    delay(200);   // short delay before next poll
}
