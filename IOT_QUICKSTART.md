# Smart Bus Management System — IoT Quick Start Guide

## What You Have

✅ **Complete Real-Time IoT Bus Arrival Detection System**

This system detects when buses arrive at gates using RFID scanning, records arrival times in real-time, determines if buses are on-time or late, and displays live updates on admin dashboards.

---

## Quick Start (5 Minutes)

### 1. Configure Hardware

**MFRC522 to ESP32 Pinout:**
```
MFRC522 Pin  →  ESP32 GPIO
─────────────────────────────
SDA (SS)     →  GPIO 5
SCK          →  GPIO 18
MOSI         →  GPIO 23
MISO         →  GPIO 19
GND          →  GND
RST          →  GPIO 22
3.3V         →  3.3V    ⚠️ NOT 5V!
```

**Wire the MFRC522 to ESP32 breadboard** (see IOT_SETUP_GUIDE.md Part 1 for diagram)

### 2. Flash ESP32 Firmware

1. Open Arduino IDE
2. Install libraries: **MFRC522**, **ArduinoJson** (v7+), **ESP32 board package**
3. Open: `iot/esp32_gate_bus_rfid.ino`
4. Edit lines ~40-50:
   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_PASSWORD";
   const char* SERVER_IP     = "192.168.1.100";  // Your PC IP (ipconfig)
   ```
5. **Upload** (Ctrl+U)

### 3. Register Bus RFID UIDs

1. Get RFID UID from ESP32 Serial Monitor (115200 baud)
2. Admin Dashboard → Bus Management
3. Set RFID UID for each bus
4. Save

### 4. Start System

```bash
cd "c:\Users\ACER\OneDrive\Desktop\Smart Bus Management System"
python app.py
```

Visit: `http://127.0.0.1:5000/admin`

### 5. Scan & Verify

1. Hold RFID card near MFRC522
2. Serial Monitor shows: `[RFID] UID: 72 3C 14 5C`
3. Bus Arrivals dashboard updates within 2 seconds
4. Arrival recorded in database

---

## System Architecture

```
RFID Card → MFRC522 → ESP32 → WiFi → Flask API → MySQL → Dashboard
  Scan      Reader   WiFi    Post   /api/         Storage  Real-time
                              JSON   rfid                  Update
```

---

## Key Routes & APIs

### Backend Routes (Flask)

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/rfid` | POST | Submit BUS RFID scan (maps UID → bus and records arrival) |
| `/admin/api/bus-arrivals` | GET | Get live arrival rows for admin bus arrivals dashboard |

### Frontend

| Page | URL | What It Does |
|------|-----|---|
| Bus Arrivals Dashboard | `/admin/bus-arrivals` | Displays live gate arrivals (bus, plate, driver, status) |
| Admin Dashboard | `/admin` | Displays summary and management widgets |
| Management Dashboard | `/management` | Shows on-time/late counts + attendance charts |

### Real-Time Updates

```
Bus arrivals dashboard polls /admin/api/bus-arrivals
every 2 seconds via JavaScript (static/js/bus_arrivals_live.js)
```

---

## Configuration

### Time Cutoff (On-Time vs Late)

**Default:** 9:10 AM

Buses arriving ≤ 9:10 AM = **On Time (green)**  
Buses arriving > 9:10 AM = **Late (red)**

**To Change:** Edit `config.py`
```python
BUS_ARRIVAL_CUTOFF_HOUR=9      # Hour (0-23)
BUS_ARRIVAL_CUTOFF_MINUTE=10   # Minute (0-59)
```

### Debounce Window

**Default:** 15 seconds

Prevents the same RFID card being scanned multiple times in quick succession (bus slowing down at gate) from creating duplicate records.

**To Change:** Edit `config.py`
```python
BUS_ARRIVAL_DEBOUNCE_SECONDS=15
```

---

## Troubleshooting

### "RFID not found in database" (404 response)

**Solution:** Register the RFID UID in Bus Management

1. Check Serial Monitor for UID (e.g., `AB12CD34`)
2. Admin Dashboard → Bus Management → Edit Bus
3. Set RFID UID field
4. Save

### Dashboard Not Updating

**Solution:** Check browser console (F12)

1. Press **F12** → **Console** tab
2. Look for errors
3. Check Network tab: `/admin/api/bus-arrivals` should poll every 2 sec

### ESP32 Won't Connect to WiFi

**Solution:** Verify credentials

1. SSID and password are case-sensitive
2. WiFi must be 2.4 GHz (most ESP32 don't support 5 GHz)
3. ESP32 and PC must be on **same network**

Test: From ESP32's perspective, can it reach PC?
```
(Check Serial Monitor for WiFi IP)
ping PC_IP_ADDRESS
```

### RFID Card Won't Read

**Solution:** Check wiring and placement

1. Verify SPI pins match code (GPIO 5, 18, 23, 19, 22)
2. Move card slowly (not too fast) over antenna
3. Try different cards (compatibility varies)
4. Check MFRC522 LED is on (power received)

---

## File Structure

```
Smart Bus Management System/
├── app.py                          ← Main Flask app
├── config.py                       ← Configuration (cutoff time, debounce, email)
├── routes/
│   ├── iot_routes.py               ← Legacy IoT API endpoints
│   ├── rfid_api.py                 ← Bus RFID arrival endpoint (/api/rfid)
│   ├── admin_bus_routes.py         ← Live bus arrivals dashboard routes
│   ├── admin_routes.py             ← Admin CRUD operations
│   ├── auth_routes.py              ← Login/signup
│   ├── student_routes.py           ← Student dashboard
│   └── driver_routes.py            ← Driver dashboard
├── models/
│   ├── bus_arrival_log.py          ← Bus arrival log ORM (bus details + RFID + time)
│   ├── arrival_model.py            ← Arrival ORM (bus + time + status)
│   ├── bus_model.py                ← Bus model (includes rfid_uid field)
│   └── ...                         ← Other models (Student, Driver, User, etc)
├── templates/
│   ├── admin/bus_arrivals_dashboard.html ← Live gate arrivals panel (2-sec polling)
│   ├── admin_dashboard.html        ← Admin summary panel
│   ├── management_dashboard.html   ← Management panel with IoT KPI cards
│   └── ...                         ← Other templates
├── static/
│   ├── js/
│   │   └── bus_arrivals_live.js    ← Real-time polling script (2-sec)
│   └── css/
│       └── style.css
├── iot/
│   ├── esp32_gate_bus_rfid.ino     ← ESP32 gate RFID firmware for /api/rfid
│   └── ...                         ← Optional legacy/experimental firmware files
├── IOT_SETUP_GUIDE.md              ← Hardware wiring + Arduino setup
├── IOT_TESTING_GUIDE.md            ← 30+ test cases
└── requirements.txt                ← Python dependencies
```

---

## Database Schema (Relevant Tables)

### buses Table
```
id (PK) | bus_number | route_name | driver_id | rfid_uid | ...
────────────────────────────────────────────────────────────
1       | BUS-001    | Route A    | 5        | AB12CD34
```

### arrivals Table
```
id (PK) | bus_id (FK) | arrival_time        | status    | created_at
──────────────────────────────────────────────────────────────────────
1       | 1          | 2024-01-15 09:05:30 | on_time   | 2024-01-15 09:05:31
2       | 1          | 2024-01-15 09:35:20 | late      | 2024-01-15 09:35:21
```

---

## API Examples

### Register a Bus Arrival (ESP32 calls this)

```bash
curl -X POST http://127.0.0.1:5000/api/rfid \
  -H "Content-Type: application/json" \
  -d '{"uid": "72 3C 14 5C"}'
```

**Response (201):**
```json
{
  "status": "success",
  "message": "Bus arrival recorded",
  "bus_id": 1,
  "bus_number": "BUS_01",
  "license_plate": "MP09 6271",
  "driver_name": "Rahul Singh",
  "rfid_uid": "72 3C 14 5C",
  "arrival_time": "2026-03-15 12:49:18",
  "arrival_status": "late"
}
```

### Get Live Bus Arrivals (Dashboard calls this every 2s)

```bash
curl http://127.0.0.1:5000/admin/api/bus-arrivals
```

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
    },
    ...
  ]
}
```

---

## Monitoring & Logs

### Flask Server Logs

```
python app.py
# shows all HTTP requests
```

### ESP32 Serial Monitor

```
Tools → Serial Monitor (115200 baud)
# shows WiFi connection, RFID reads, HTTP responses
```

### Browser Console

```
F12 → Console
# shows JavaScript polling, network errors, DOM updates
```

### Database Queries

```sql
-- View today's arrivals
SELECT * FROM arrivals 
WHERE DATE(arrival_time) = CURDATE() 
ORDER BY arrival_time DESC;

-- View on-time count today
SELECT COUNT(*) FROM arrivals 
WHERE DATE(arrival_time) = CURDATE() 
AND status = 'on_time';

-- View late count today
SELECT COUNT(*) FROM arrivals 
WHERE DATE(arrival_time) = CURDATE() 
AND status = 'late';
```

---

## Deployment Checklist

- [ ] All buses have RFID UIDs registered (Admin → Bus Management)
- [ ] ESP32 WiFi credentials correct (edit code line ~40)
- [ ] Server IP in ESP32 code matches PC IP (`ipconfig`)
- [ ] Flask app running: `python app.py`
- [ ] Admin Dashboard loads: `http://127.0.0.1:5000/admin`
- [ ] Live Arrivals widget visible and polling
- [ ] ESP32 Serial Monitor shows WiFi connected
- [ ] Test scan: RFID card → Serial Monitor → Bus Arrivals dashboard (within 2 sec)

---

## Testing Quick Links

**Full test suites:** See `IOT_TESTING_GUIDE.md`

**Hardware setup:** See `IOT_SETUP_GUIDE.md`

**Quick tests:**
1. Serial Monitor: Scan card → expect UID output ✓
2. Postman: POST to `/api/rfid` → expect 201 ✓
3. Dashboard: Refresh page → expect Live Arrivals widget ✓
4. End-to-end: Scan card → dashboard updates within 2 sec ✓

---

## Performance Targets

- **RFID Read Time:** <500ms
- **HTTP POST Time:** 1-3 seconds (depends on WiFi)
- **Dashboard Update Latency:** 2-4 seconds (2-sec poll window)
- **Duplicate Detection:** 15 seconds
- **Database Inserts:** <100ms per record
- **Concurrent Buses:** Tested for 5+ ESP32 devices on same network

---

## Next Steps

1. **Wire hardware** (see IOT_SETUP_GUIDE.md Part 1)
2. **Flash ESP32** (see IOT_SETUP_GUIDE.md Part 2-4)
3. **Register RFID UIDs** (Admin Dashboard)
4. **Run full test suite** (IOT_TESTING_GUIDE.md)
5. **Deploy to production** (run `python app.py` on server PC)

---

## Support

- **Hardware Issues:** See IOT_SETUP_GUIDE.md Troubleshooting (Part 9)
- **Test Failures:** See IOT_TESTING_GUIDE.md Troubleshooting (Section 5-7)
- **API Questions:** See API Reference (IOT_SETUP_GUIDE.md Part 11)
- **Code Comments:** Read `iot/esp32_gate_bus_rfid.ino` line-by-line

---

## Summary

🎯 **You have a complete, production-ready IoT bus arrival system:**

✓ ESP32 firmware for RFID scanning  
✓ Flask API for arrival recording  
✓ Real-time dashboard displays  
✓ On-time/late status calculation  
✓ Duplicate detection  
✓ Full test coverage  
✓ Hardware setup guide  
✓ Comprehensive documentation  

📖 Read IOT_SETUP_GUIDE.md for detailed hardware setup  
🧪 Read IOT_TESTING_GUIDE.md for complete test procedures  

**Ready to deploy!** 🚀
