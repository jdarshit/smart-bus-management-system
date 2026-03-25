# IoT Bus Arrival Detection System — Setup & Testing Guide

> **Update (2026-03-15):** Current gate flow uses **BUS RFID → `/api/rfid`** with firmware file `iot/esp32_gate_bus_rfid.ino`. Live bus arrivals dashboard refresh interval is **2 seconds**.

## Overview

This guide covers hardware setup, ESP32 firmware configuration, and complete end-to-end testing for the real-time RFID bus arrival detection system.

---

## Part 1: Hardware Wiring

### Components Required

- **ESP32 Dev Board** (e.g., NodeMCU-32S or similar)
- **MFRC522 RFID Reader Module** (13.56 MHz, typical ~$5-10)
- **RFID Cards/Tags** (125 kHz or 13.56 MHz, depending on reader)
- **USB Micro-B Cable** (for programming and power)
- **Breadboard & Jumper Wires**
- **3.3V Power Supply** (if not using USB)

### MFRC522 to ESP32 Pinout

| MFRC522 Pin | ESP32 GPIO | Wire Color | Notes |
|---|---|---|---|
| SDA (SS) | GPIO 5 | Yellow | Chip Select |
| SCK | GPIO 18 | Green | Serial Clock |
| MOSI | GPIO 23 | Blue | Master Out / Slave In |
| MISO | GPIO 19 | Purple | Master In / Slave Out |
| IRQ | — | — | Not used (leave unconnected) |
| GND | GND | Black | Ground |
| RST | GPIO 22 | Orange | Reset |
| 3.3V | 3.3V | Red | **IMPORTANT: Use 3.3V NOT 5V** |

### Wiring Diagram (Text)

```
┌──────────────────────────────┐
│         ESP32 Dev Board      │
│                              │
│   5V  GND  23  19  18  22  5 │
│   │    │    │   │   │   │   │
│   │    └────┴───┴───┴───┴───┼──── SPI Bus
│   │                          │
│   └──→ (USB Power)           │
└──────────────────────────────┘

       ┌─────────────────┐
       │   MFRC522       │
       │  RFID Reader    │
       │                 │
       │ 3.3V GND SDA    │
       │  │    │   │     │
       └──┴────┴───┴─────┘
          │    │   │
        (Red)(Blk)(Yel)
            ↓ ↓ ↓
      3.3V GND GPIO5
```

### Critical Notes

⚠️ **NEVER connect MFRC522 to 5V!** This will permanently damage the module. Always use 3.3V.

✓ **Use quality jumper wires** — Poor connections cause intermittent RFID read failures.

✓ **Keep SPI wires short** — Long wires can introduce noise on the signal lines.

---

## Part 2: Arduino IDE Setup

### Step 1: Install Arduino IDE

Download from [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software) (IDE 2.x recommended).

### Step 2: Add ESP32 Board Support

1. **File → Preferences**
2. **Additional boards manager URLs**, paste:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Click OK
4. **Tools → Board → Boards Manager**
5. Search: `esp32`
6. Install **"esp32 by Espressif Systems"** (latest version)

### Step 3: Install Required Libraries

**Tools → Manage Libraries**, search for and install:

1. **MFRC522** by GithubCommunity
   - Handles RFID reader communication
   - Version: latest stable (usually v1.4.10+)

2. **ArduinoJson** by Benoit Blanchon (IMPORTANT: Version 7.x)
   - JSON serialization for HTTP payloads
   - Required for building `{"uid": "..."}` JSON

3. **WiFi** (bundled with ESP32 board package)

4. **HTTPClient** (bundled with ESP32 board package)

### Step 4: Board & Port Configuration

1. **Tools → Board** → Select **"ESP32 Dev Module"** (or your specific variant)
2. **Tools → Port** → Select the USB COM port (e.g., `COM3`, `/dev/ttyUSB0`)
3. **Tools → Upload Speed** → Set to `921600` (faster uploads)

---

## Part 3: ESP32 Firmware Configuration

### Edit Configuration Before Uploading

Open `iot/esp32_gate_bus_rfid.ino` and edit these lines:

```cpp
// Wi-Fi credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";      // ← Your WiFi network name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";  // ← Your WiFi password

// Flask server address
const char* SERVER_IP   = "192.168.1.100";   // ← Your PC's LAN IP
const int   SERVER_PORT = 5000;               // ← Flask port (usually 5000)
```

### Find Your PC's LAN IP

**Windows (PowerShell):**
```powershell
ipconfig
```
Look for "IPv4 Address" under your active WiFi adapter (e.g., `192.168.1.100`).

**Linux/Mac:**
```bash
ifconfig
# or
hostname -I
```

### Important: Same Network Requirement

✓ ESP32 and PC must be on the **SAME WiFi network** (same SSID).

✓ Verify they can reach each other:
```bash
ping 192.168.1.100  # From ESP32's WiFi perspective: ESP32 should reach PC
ping ESP32_IP       # From PC: PC should reach ESP32
```

---

## Part 4: Upload Firmware to ESP32

1. **Connect ESP32** via USB cable to your computer
2. **File → Open** → Select `iot/esp32_gate_bus_rfid.ino`
3. **Sketch → Upload** (or press Ctrl+U)
4. Wait for `Leaving... Hard resetting via RTS pin...` message
5. Open **Tools → Serial Monitor** (Ctrl+Shift+M)
6. Set baud rate to **115200** (bottom-right dropdown)
7. Press the **RST (Reset)** button on ESP32

Expected output in Serial Monitor:
```
[WiFi] Connecting to MyWiFi...........
[WiFi] Connected! IP: 192.168.1.50
[RFID] Reader ready. Firmware: Version 1.0
[System] Waiting for bus RFID tags...
(3 LED blinks = ready)
```

### Troubleshooting Upload Issues

| Issue | Solution |
|-------|----------|
| "Failed to connect to COM port" | Try holding `IO0` button during upload; check USB cable; try different USB port |
| "PySerial or esptool not found" | Reinstall Arduino IDE or install Python + pyserial |
| Baud rate mismatch | Set Serial Monitor to **115200** baud |

---

## Part 5: Test RFID Reading

### Test 1: Serial Monitor (Local RFID Scan)

1. Keep **Serial Monitor open** (115200 baud)
2. **Hold an RFID card/tag near the MFRC522 antenna**
3. Expected output:
   ```
   [RFID] UID: 72 3C 14 5C
   [HTTP] POST → {"uid":"72 3C 14 5C"}
   [HTTP] Response (404): {"status":"error","message":"Unknown bus RFID UID"}
   [WARN] RFID not registered in database.
   ```

### Interpreting Serial Output

| Message | Meaning |
|---------|---------|
| `[RFID] UID: 72 3C 14 5C` | Card successfully read ✓ |
| `[HTTP] Response (201):` | Arrival recorded successfully ✓ |
| `[HTTP] Response (404):` | RFID UID not found — register it first |
| `[HTTP] Response (400):` | JSON format error or empty UID |
| `[WiFi] Timeout — restarting ESP32` | Can't connect to WiFi — check credentials |
| Error: Connection refused | Flask server not running; check PC IP & port; verify WiFi connectivity |

### LED Feedback

| Pattern | Meaning |
|---------|---------|
| 3 blinks @ startup | ESP32 ready ✓ |
| 2 quick blinks | Arrival logged (201) ✓ |
| LED held ON for 500ms | Error (404, 400, or network error) |

---

## Part 6: Register RFID UIDs in Database

Before testing end-to-end, you must register your RFID cards with the system.

### Via Admin Dashboard

1. Navigate to **Admin Panel → Bus Management** (or driver management)
2. Find the bus record you want to assign
3. In the "RFID UID" field, enter the UID from the Serial Monitor (e.g., `72 3C 14 5C`)
4. Click **Save/Update**

### Via MySQL (Direct Insert)

```sql
USE smart_bus_db;

-- Find a bus_id
SELECT id, bus_number, rfid_uid FROM buses LIMIT 1;

-- Update with RFID UID from Serial Monitor
UPDATE buses SET rfid_uid = '72 3C 14 5C' WHERE id = 1;

-- Verify
SELECT id, bus_number, rfid_uid FROM buses WHERE id = 1;
```

---

## Part 7: End-to-End System Testing

### Phase 1: Manual Test with Postman

(This simulates what the ESP32 will do)

1. **Start Flask server:**
   ```bash
   cd "c:\Users\ACER\OneDrive\Desktop\Smart Bus Management System"
   python app.py
   ```
   Expected: `Running on http://127.0.0.1:5000`

2. **Open Postman** (or curl):

   **Request:**
   ```http
   POST http://127.0.0.1:5000/api/rfid
   Content-Type: application/json

   {
   "uid": "72 3C 14 5C"
   }
   ```

   **Expected Response (201 Created):**
   ```json
   {
     "id": 123,
     "bus_number": "BUS-001",
     "route_name": "Route A",
     "driver_name": "John Doe",
     "arrival_time": "2024-01-15 09:05:30",
     "status": "on_time"
   }
   ```

3. **Verify Database:**
   ```sql
   SELECT * FROM arrivals WHERE bus_id = 1 ORDER BY arrival_time DESC LIMIT 1;
   ```

### Phase 2: Dashboard Live Updates

1. **Open Admin Dashboard:**
   ```
   http://127.0.0.1:5000/admin
   ```

2. **Scroll to "Live Bus Arrivals" widget**
   - Should show summary cards (On-Time, Late, Total)
   - Table should auto-update every 2 seconds

3. **Trigger a Postman POST** (or ESP32 scan):
   - Within 2 seconds, the dashboard should show the new arrival
   - Status badge should show `On Time` (green) or `Late` (red)

### Phase 3: ESP32 Hardware Test

1. **Upload firmware** to ESP32 (see Part 4)
2. **Open Serial Monitor** (115200 baud)
3. **Scan registered RFID card** near MFRC522
4. **Verify in Serial Monitor:**
   ```
   [RFID] UID: 72 3C 14 5C
   [HTTP] Response (201): Bus-001  Route: Route A  Status: on_time
   ```

5. **Check Admin Dashboard:**
   - New arrival should appear in the table within 2 seconds
   - Summary counts should update

### Phase 4: Edge Case Testing

#### Test: Unregistered RFID

1. Create a new RFID card with unknown UID (unseen before)
2. **Expected:** HTTP 404 (Not Found)
3. **Serial output:** `[WARN] RFID not registered in database.`

#### Test: WiFi Disconnect & Auto-Reconnect

1. Disconnect PC from WiFi (simulate network loss)
2. Scan card
3. **Expected:** ESP32 prints `[WiFi] Connection lost — reconnecting...`
4. ESP32 should re-connect automatically
5. After reconnection, next scan should succeed

---

## Part 8: Production Deployment Checklist

- [ ] All bus records have `rfid_uid` field populated in database
- [ ] ESP32 WiFi credentials are correct and match PC network
- [ ] Server IP in ESP32 code matches PC's LAN IP (check with `ipconfig`)
- [ ] Flask server is running: `python app.py`
- [ ] Admin Dashboard loads without errors at `http://127.0.0.1:5000/admin`
- [ ] Live Arrivals widget displays (check browser console for JS errors)
- [ ] Manual Postman test succeeds (201 response, record in DB)
- [ ] ESP32 serial output shows successful WiFi connection
- [ ] ESP32 successfully reads RFID cards
- [ ] Dashboard updates within 2 seconds of scan
- [ ] LED feedback works (2 blinks on success)

---

## Part 9: Troubleshooting

### Issue: "RFID not found in database" (404)

**Solution:**
1. Open Admin Dashboard
2. Go to Bus Management
3. Find the bus and set its RFID UID to the scanned value (from Serial Monitor)
4. Save and test again

### Issue: Dashboard not updating

**Solution:**
1. Press F12 (Developer Tools) → Console tab
2. Check for JavaScript errors
3. Verify `bus_arrivals_live.js` is loaded (Network tab)
4. Test API manually: `curl http://127.0.0.1:5000/admin/api/bus-arrivals`

### Issue: RFID scan not detected in Serial Monitor

**Solution:**
1. Check SPI wiring (especially SCK, MOSI, MISO, SDA)
2. Verify pins match code (GPIO 5, 18, 23, 19, 22)
3. Try different RFID card (some cards may not be compatible)
4. Move card slowly towards antenna (not too fast)
5. Check Serial Monitor baud rate = 115200

### Issue: ESP32 won't connect to WiFi

**Solution:**
1. Double-check SSID and password (case-sensitive, special characters)
2. Verify WiFi uses 2.4 GHz (some ESP32 don't support 5 GHz)
3. Check if PC and ESP32 are on same network:
   ```
   ping 192.168.1.100  (from ESP32: Does PC respond?)
   ```
4. Try re-uploading firmware with correct credentials
5. Restart router

---

## Part 10: Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     ESP32 + MFRC522 Gate                        │
│                                                                 │
│  Scan RFID Card                                                 │
│       ↓                                                          │
│  Read UID (e.g., "72 3C 14 5C")                                  │
│       ↓                                                          │
│  Optional local debounce (ESP32-side)                           │
│       ↓                                                          │
│  POST JSON: {"uid": "72 3C 14 5C"}                               │
│       ↓                                                          │
│  WiFi → Flask API @ http://SERVER_IP:5000/api/rfid             │
└─────────────────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────┐
│            Flask Backend (app.py)                            │
│                                                              │
│  POST /api/rfid                                              │
│  ├─ Validate RFID UID                                        │
│  ├─ Query Bus where rfid_uid = '72 3C 14 5C'               │
│  ├─ Calculate status (on_time / late based on 9:10 AM)      │
│  ├─ INSERT into arrivals table                              │
│  └─ Return JSON w/ bus_number, route, driver, status        │
└──────────────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────┐
│            MySQL Database (smart_bus_db)                     │
│                                                              │
│  arrivals table                                              │
│  ├─ id, bus_id, arrival_time, status, created_at           │
│  └─ Example: (123, 1, 2024-01-15 09:05:30, 'on_time', ...) │
└──────────────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────┐
│   Bus Arrivals Dashboard (JavaScript Polling every 2s)       │
│                                                              │
│  fetch("/admin/api/bus-arrivals")                           │
│       ↓                                                      │
│  Update table rows (bus, route, driver, arrival_time, ✓)   │
│  Update summary counts (on_time, late, total)               │
└──────────────────────────────────────────────────────────────┘
```

---

## Part 11: API Reference

### POST /api/rfid

**Request:**
```json
{
   "uid": "72 3C 14 5C"
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "bus_number": "BUS-001",
  "route_name": "Route A",
  "driver_name": "John Doe",
  "arrival_time": "2024-01-15 09:05:30",
  "status": "on_time"
}
```

**Error Responses:**
- **400 Bad Request**: Missing or empty `uid`
- **404 Not Found**: RFID UID not registered (no bus with that UID)

### GET /admin/api/bus-arrivals

**Response:**
```json
{
   "arrivals": [
      {
         "bus_number": "BUS_01",
         "license_plate": "MP09 6271",
         "driver_name": "Rahul Singh",
         "rfid_uid": "72 3C 14 5C",
         "arrival_time": "2026-03-15 12:49:18",
         "status": "Late"
      }
   ]
}
```

---

## Summary

You now have a **production-ready IoT bus arrival system** with:

✓ ESP32 RFID scanner posting to Flask API  
✓ Real-time dashboard updates (2-sec polling)  
✓ Automatic on-time/late status calculation  
✓ Consistent UID normalization and validation  
✓ Complete error handling  

For support or issues, check the troubleshooting section or review the code comments in `esp32_gate_bus_rfid.ino`.
