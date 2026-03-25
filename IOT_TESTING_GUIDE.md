# IoT Bus Arrival System — Complete Testing Guide

> **Update (2026-03-15):** Current gate endpoint is **POST `/api/rfid`** with payload `{ "uid": "72 3C 14 5C" }`. Live bus arrivals dashboard is `/admin/bus-arrivals` with **2-second** polling.

## Overview

This document provides step-by-step tests to validate the entire IoT bus arrival detection system, from backend APIs to frontend dashboards to hardware integration.

---

## Pre-Test Checklist

- [ ] MySQL server running (`smart_bus_db` accessible)
- [ ] Flask app running: `python app.py` (listening on http://127.0.0.1:5000)
- [ ] At least one bus record in database with an assigned RFID UID
- [ ] At least one bus record with an assigned driver (for dashboard display)
- [ ] No network firewalls blocking localhost:5000

---

## Test Suite 1: Backend API Tests

### Test 1.1: POST /api/rfid (Success - 201)

**Objective:** Verify successful arrival recording with 201 response

**Prerequisites:**
- Bus with id=1, bus_number="BUS_01", rfid_uid="72 3C 14 5C" exists in database

**Steps:**

1. Open **Postman** (or Terminal with `curl`)
2. Create a new POST request:
   ```
  URL: http://127.0.0.1:5000/api/rfid
   Method: POST
   Headers: Content-Type: application/json
   Body (JSON):
   {
    "uid": "72 3C 14 5C"
   }
   ```

3. Click **Send**

**Expected Result:**
- **Status Code:** 201 Created
- **Response Body:**
  ```json
  {
    "status": "success",
    "message": "Bus arrival recorded",
    "bus_id": 1,
    "bus_number": "BUS_01",
    "license_plate": "MP09 6271",
    "driver_name": "Rahul Singh",
      "uid": "72 3C 14 5C",
    "arrival_time": "2026-03-15 12:49:18",
    "arrival_status": "late"
  }
  ```

**Verification Steps:**
```sql
SELECT * FROM arrivals 
WHERE bus_id = 1 
ORDER BY created_at DESC 
LIMIT 1;
-- Should show one record with status = 'on_time' or 'late'
```

---

### Test 1.2: POST /api/rfid (Repeat Scan)

**Objective:** Verify repeated scans continue to be recorded by backend

**Prerequisites:**
- Bus "BUS_01" with rfid_uid="72 3C 14 5C" exists

**Steps:**

1. From Test 1.1, note the timestamp of the arrival just created
2. Immediately send the SAME POST request (same RFID UID)
3. Click **Send** again within a few seconds

**Expected Result:**
- **Status Code:** 201 Created
- A new arrival row is added

**Verification Steps:**
```sql
SELECT COUNT(*) FROM arrivals 
WHERE bus_id = 1 
AND created_at > DATE_SUB(NOW(), INTERVAL 1 MINUTE);
-- Should increase after each accepted POST
```

---

### Test 1.3: POST /api/rfid (Not Found - 404)

**Objective:** Verify error handling for unregistered RFID UID

**Prerequisites:**
- Use a random RFID UID that doesn't exist in any bus record

**Steps:**

1. Create POST request with unknown RFID:
   ```json
   {
   "uid": "UNKNOWN99"
   }
   ```

2. Click **Send**

**Expected Result:**
- **Status Code:** 404 Not Found
- **Response Body:**
  ```json
  {
    "error": "RFID UID not found in database"
  }
  ```

---

### Test 1.4: POST /api/rfid (Invalid JSON - 400)

**Objective:** Verify validation of missing or invalid RFID UID field

**Steps:**

1. Create POST request with empty RFID:
   ```json
   {
   "uid": ""
   }
   ```

2. Click **Send**

**Expected Result:**
- **Status Code:** 400 Bad Request
- **Response Body:** Error message about empty/invalid RFID

---

### Test 1.5: GET /admin/api/bus-arrivals

**Objective:** Verify retrieval of recent arrivals with correct filtering

**Steps:**

1. Login as admin in browser (or use an authenticated session/cookie)
2. Create GET request:
   ```
   URL: http://127.0.0.1:5000/admin/api/bus-arrivals
   Method: GET
   Headers: Accept: application/json
   ```

3. Click **Send**

**Expected Result:**
- **Status Code:** 200 OK
- **Response Body:**
  ```json
  {
    "arrivals": [
      {
        "id": 123,
        "bus_number": "BUS-001",
        "route_name": "Route A",
        "driver_name": "John Doe",
        "arrival_time": "2024-01-15 09:05:30",
        "status": "on_time"
      },
      ...
    ]
  }
  ```

**Verification:**
- Response should contain at most 5 arrivals (as per limit=5)
- Arrivals should be sorted by most recent first
- Each arrival should have all required fields

---


## Test Suite 2: Frontend Dashboard Tests

### Test 2.1: Admin Dashboard Loads Without Errors

**Objective:** Verify dashboard loads and displays IoT widget

**Steps:**

1. Navigate to: `http://127.0.0.1:5000/admin`
2. Press **F12** (Developer Tools)
3. Go to **Console** tab (check for JavaScript errors)
4. Go to **Network** tab
5. Reload page

**Expected Result:**
- Page loads completely without 404 errors
- No red error messages in Console
- `bus_arrivals_live.js` loads successfully (check Network → JS files)
- "Live Bus Arrivals" widget visible below KPI cards

---

### Test 2.2: Live Arrivals Widget Displays Summary Cards

**Objective:** Verify summary KPI cards display correct data

**Steps:**

1. On Admin Dashboard, scroll to "Live Bus Arrivals" section
2. Observe the three summary cards:
   - "On-Time Buses" (green)
   - "Late Buses" (red)
   - "Total Arrivals Today" (blue)

**Expected Result:**
- All three cards visible with numbers populated
- Numbers are consistent with the rows shown in the latest arrivals table
- Green/red/blue color scheme matches design

---

### Test 2.3: Live Arrivals Table Shows Recent Arrivals

**Objective:** Verify table displays actual arrival records

**Steps:**

1. On Admin Dashboard, below summary cards, find the "Latest Bus Arrivals" table
2. Observe table columns: Bus | Route | Driver | Arrival Time | Status
3. Verify rows display actual bus data

**Expected Result:**
- Table shows at least one row of arrival data
- Columns match: bus_number, route_name, driver_name, arrival_time, status badge
- Status badges are green (on_time) or red (late)
- Timestamps are formatted readably (e.g., "2024-01-15 09:05:30")

---

### Test 2.4: Real-Time Updates (2-Second Polling)

**Objective:** Verify dashboard updates automatically when new arrivals occur

**Steps:**

1. Keep Admin Dashboard open and visible
2. In **another browser tab or Postman**, send a POST to `/api/rfid` with a known RFID UID
3. Note the current time
4. Watch the Admin Dashboard for changes

**Expected Result:**
- Within 2 seconds, new arrival appears in the table (at the top)
- Summary counts increase by 1 (in the appropriate status card)
- No manual refresh required

**Timing Note:** JavaScript polls every 2 seconds, so changes visible within 0-2 seconds.

---

### Test 2.5: Management Dashboard IoT Cards

**Objective:** Verify management dashboard displays real-time IoT data

**Steps:**

1. Navigate to: `http://127.0.0.1:5000/management` (or similar, based on dashboard route)
2. Scroll to top, after the main KPI cards
3. Look for three IoT cards:
   - "On-Time Buses Today" (green)
   - "Late Buses Today" (red)
   - "Total Arrivals Today" (blue)

**Expected Result:**
- Cards display with correct counts
- Counts update automatically every 2 seconds
- Data aligns with what Admin Dashboard shows

---

## Test Suite 3: ESP32 Hardware Integration Tests

### Test 3.1: ESP32 Boots and Connects to WiFi

**Objective:** Verify hardware powers on and establishes network connection

**Prerequisites:**
- ESP32 connected via USB to PC
- ESP32 firmware uploaded with correct WiFi credentials (see IOT_SETUP_GUIDE.md)
- MFRC522 wired correctly

**Steps:**

1. Open **Arduino IDE → Tools → Serial Monitor**
2. Set baud rate to **115200** (bottom-right)
3. Press **RST (Reset)** button on ESP32 or unplug/replug USB

**Expected Output in Serial Monitor:**
```
[WiFi] Connecting to MyWiFi...........
[WiFi] Connected! IP: 192.168.1.50
[RFID] Reader ready. Firmware: Version 1.0
[System] Waiting for bus RFID tags...
(3 LED blinks)
```

---

### Test 3.2: RFID Card Detected and UID Read

**Objective:** Verify MFRC522 successfully reads RFID card

**Prerequisites:**
- Serial Monitor open with ESP32 running
- RFID card/tag available
- MFRC522 powered (LED on)

**Steps:**

1. Hold RFID card approximately 2-3 cm from MFRC522 antenna
2. Move slowly across antenna
3. Observe Serial Monitor

**Expected Output:**
```
[RFID] Card detected UID: AB12CD34
```

**If UID not detected:**
- Try different card (some card types may not be supported)
- Check MFRC522 wiring (especially SDA, MOSI, MISO, SCK)
- Verify pin numbers in code match GPIO pins

---

### Test 3.3: ESP32 POSTs to Flask API Successfully

**Objective:** Verify HTTP request reaches backend and arrival is recorded

**Prerequisites:**
- ESP32 online and WiFi connected
- Flask server running on PC
- RFID UID is registered to a bus in database

**Steps:**

1. Keep Serial Monitor open
2. Scan registered RFID card
3. Observe HTTP request log

**Expected Output in Serial Monitor:**
```
[RFID] UID: 72 3C 14 5C
[HTTP] POST → {"uid":"72 3C 14 5C"}
[HTTP] Response (201): Bus: BUS-001  Route: Route A  Status: on_time
[OK] 2 quick LED blinks
```

**If HTTP Error:**
- Check IP address in code matches PC IP (`ipconfig`)
- Verify Flask running on port 5000
- Ensure ESP32 and PC on same WiFi network
- Check firewall isn't blocking localhost:5000

---

### Test 3.4: LED Feedback Patterns

**Objective:** Verify LED feedback indicates arrival status

**Prerequisites:**
- Built-in LED visible on ESP32 (GPIO 2 is typical)

**Steps:**

Trigger different scenarios:

| Scenario | Action | Expected LED |
|----------|--------|---|
| Success (201) | Scan registered card | 2 quick blinks |
| Repeat scan | Scan same card again | Normal success feedback from firmware |
| Error (404, etc) | Scan unregistered card or network fail | LED held on 500ms |
| Startup | Press RST button | 3 blinks |

---

### Test 3.5: Debounce Prevention (Hardware)

**Objective:** Verify debounce works on ESP32

**Steps:**

1. Scan RFID card once (watch HTTP 201 response)
2. Immediately scan the same card again (within 5 seconds)
3. Observe Serial Monitor

**Expected Output:**
```
[RFID] Card detected UID: AB12CD34
[HTTP] Response (201): ... Status: on_time
(2 blinks)

[DEBOUNCE] Same card within debounce window (5 s) — skipped.
(no HTTP POST)
```

---

## Test Suite 4: End-to-End Integration Tests

### Test 4.1: Complete Flow - Scan to Dashboard Display

**Objective:** Verify entire data flow from RFID scan to dashboard display

**Steps:**

1. **Step 1: Prepare**
   - Admin Dashboard open in browser at `http://127.0.0.1:5000/admin`
   - ESP32 running with Serial Monitor open
   - Bus with RFID UID registered in database

2. **Step 2: Scan RFID**
   - Hold RFID card near MFRC522
   - Note exact time of scan

3. **Step 3: Verify API Response**
   - Serial Monitor shows: `[HTTP] Response (201): ...`

4. **Step 4: Verify Database**
   - Open MySQL console:
     ```sql
     SELECT * FROM arrivals ORDER BY created_at DESC LIMIT 1;
     ```
   - Should show new record with correct bus_id, status

5. **Step 5: Verify Dashboard Update**
   - Within 2 seconds, Admin Dashboard updates
   - New arrival appears in table
   - Summary counts increase

**Final Verification:**
- ✓ Serial Monitor shows 201
- ✓ Database contains new record
- ✓ Dashboard displays arrival within 2 seconds

---

### Test 4.2: Multiple Buses on Same Network

**Objective:** Verify system handles multiple ESP32 devices (multiple gates)

**Prerequisites:**
- Two or more ESP32s flashed with same code (different bus RFIDs in database)
- All on same WiFi network

**Steps:**

1. Configure each ESP32 with different bus data (or same server)
2. Scan RFID on ESP32 #1
3. Scan RFID on ESP32 #2
4. Observe Admin Dashboard for both arrivals

**Expected Result:**
- Table shows arrivals from both buses
- Summary counts reflect all arrivals
- No conflicts or data loss

---

### Test 4.3: Status Calculation (On-Time vs Late)

**Objective:** Verify on_time/late status calculated correctly based on 9:10 AM cutoff

**Prerequisites:**
- Current time must be past 9:10 AM

**Steps:**

1. Manually insert test arrivals via Postman:

   **Test Case A: Before Cutoff (On-Time)**
   ```bash
   # Create fake arrival at 9:05 AM
   # (This tests the calculation logic)
   ```

2. Verify in database:
   ```sql
   SELECT * FROM arrivals WHERE arrival_time < '09:10:00';
   -- Should have status = 'on_time'
   ```

3. Test Case B: After Cutoff (Late)
   ```sql
   SELECT * FROM arrivals WHERE arrival_time > '09:10:00';
   -- Should have status = 'late'
   ```

**Expected Result:**
- Arrivals before 9:10 AM: status = "on_time" ✓
- Arrivals after 9:10 AM: status = "late" ✓

---

## Test Suite 5: Stress & Edge Cases

### Test 5.1: High-Frequency Scans

**Objective:** Verify system handles rapid consecutive scans

**Steps:**

1. Scan RFID card 10 times rapidly (alternating with different cards to bypass debounce)
2. Check database for correct count
3. Verify dashboard updates accurately

**Expected Result:**
- All 10 arrivals recorded (no lost data)
- Dashboard counts correct
- No crashes or errors in logs

---

### Test 5.2: Network Disconnection & Recovery

**Objective:** Verify ESP32 retries on network failure

**Steps:**

1. ESP32 running, WiFi connected
2. Disconnect PC from WiFi (simulate network outage)
3. Scan RFID immediately
4. Reconnect PC to WiFi
5. Observe Serial Monitor

**Expected Output:**
```
[WiFi] Connection lost — reconnecting...
[WiFi] Connected! IP: 192.168.1.50
[RFID] Card detected UID: AB12CD34
[HTTP] Response (201): ...
```

**Expected Result:**
- ESP32 auto-reconnects within 20 seconds
- After reconnection, next scan succeeds
- Arrival recorded in database

---

### Test 5.3: Midnight Transition (Status Reset)

**Objective:** Verify daily summary resets at midnight

**Prerequisites:**
- System running for multiple days

**Steps:**

1. Record arrival today before midnight
2. Check dashboard summary counts
3. Wait for midnight (or manually advance system time for testing)
4. Scan another RFID post-midnight
5. Check that daily summary counts reset

**Expected Result:**
- Summary counts (on_time, late, total) increment only for current day
- Previous day's data not included in today's summary
- Historical data preserved in `arrivals` table

---

## Test Suite 6: Database & Data Integrity Tests

### Test 6.1: Referential Integrity

**Objective:** Verify foreign key constraints

**Steps:**

1. Try to create arrival with non-existent bus_id:
   ```sql
   INSERT INTO arrivals (bus_id, arrival_time, status, created_at)
   VALUES (99999, NOW(), 'on_time', NOW());
   ```

**Expected Result:**
- **MySQL Error:** Foreign key constraint violation
- Record NOT inserted
- Referential integrity maintained

---

### Test 6.2: Status Enum Validation

**Objective:** Verify only valid status values allowed

**Steps:**

1. Try to insert arrival with invalid status:
   ```sql
   INSERT INTO arrivals (bus_id, arrival_time, status, created_at)
   VALUES (1, NOW(), 'invalid_status', NOW());
   ```

**Expected Result:**
- **MySQL Error:** Check constraint violation (status must be 'on_time' or 'late')
- Record NOT inserted

---

### Test 6.3: Arrival Timestamp Accuracy

**Objective:** Verify arrival times recorded with precision

**Steps:**

1. Scan RFID card and note exact time (HH:MM:SS)
2. Query database immediately:
   ```sql
   SELECT arrival_time FROM arrivals WHERE id = (SELECT MAX(id) FROM arrivals);
   ```

**Expected Result:**
- Database timestamp matches scanned time (within 1 second)
- Timestamp format: YYYY-MM-DD HH:MM:SS

---

## Test Suite 7: Logging & Monitoring

### Test 7.1: Flask Server Logs

**Objective:** Verify API requests logged correctly

**Steps:**

1. Keep terminal running `python app.py` visible
2. Send Postman requests
3. Observe Flask output logs

**Expected Output:**
```
127.0.0.1 - - [15/Jan/2024 09:05:30] "POST /api/rfid HTTP/1.1" 201 -
127.0.0.1 - - [15/Jan/2024 09:05:31] "GET /admin/api/bus-arrivals HTTP/1.1" 200 -
127.0.0.1 - - [15/Jan/2024 09:05:33] "GET /admin/api/bus-arrivals HTTP/1.1" 200 -
```

---

### Test 7.2: Browser Console for JavaScript Errors

**Objective:** Verify frontend polling has no errors

**Steps:**

1. Admin Dashboard open
2. F12 → Console tab
3. Monitor for 30 seconds

**Expected Result:**
- No red error messages
- May see network requests: `polling /admin/api/bus-arrivals`
- No exceptions or warnings related to `bus_arrivals_live.js`

---

## Summary: Test Execution Checklist

- [ ] Test 1.1: POST 201 (Success)
- [ ] Test 1.2: POST 201 (Repeat Scan)
- [ ] Test 1.3: POST 404 (Not Found)
- [ ] Test 1.4: POST 400 (Invalid)
- [ ] Test 1.5: GET /admin/api/bus-arrivals
- [ ] Test 2.1: Dashboard loads
- [ ] Test 2.2: Summary cards display
- [ ] Test 2.3: Table shows arrivals
- [ ] Test 2.4: Real-time updates (2-sec)
- [ ] Test 2.5: Management dashboard
- [ ] Test 3.1: ESP32 WiFi connect
- [ ] Test 3.2: RFID UID read
- [ ] Test 3.3: HTTP POST success
- [ ] Test 3.4: LED feedback
- [ ] Test 3.5: Debounce prevention
- [ ] Test 4.1: End-to-end flow
- [ ] Test 4.2: Multiple buses
- [ ] Test 4.3: Status calculation
- [ ] Test 5.1: High-frequency scans
- [ ] Test 5.2: Network recovery
- [ ] Test 5.3: Midnight reset
- [ ] Test 6.1: Referential integrity
- [ ] Test 6.2: Status validation
- [ ] Test 6.3: Timestamp accuracy
- [ ] Test 7.1: Flask logs
- [ ] Test 7.2: Console for JS errors

---

## Recommended Test Order

1. **Backend First** (Suite 1): Verify API foundation
2. **Frontend Second** (Suite 2): Verify dashboard displays API data
3. **Hardware Third** (Suite 3): Verify ESP32 sends data to API
4. **Integration** (Suite 4): End-to-end flow
5. **Edge Cases** (Suites 5-7): Robustness & monitoring

---

## When All Tests Pass ✓

Your system is production-ready:

- ✓ RFID cards register as bus arrivals
- ✓ On-time/late status calculated correctly
- ✓ Dashboard updates in real-time
- ✓ Data persists in database
- ✓ No data loss on network disruption
- ✓ Multiple buses/gates supported
- ✓ Full audit trail maintained

🎉 **Deployment ready!**
