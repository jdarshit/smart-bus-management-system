# College Implementation Guide - Smart Bus IoT Operations

This guide explains how to physically deploy and operate the RFID + ESP32 bus arrival system on a college campus.

## 1) Gate hardware placement

RFID reader placement:
- Install RFID reader at each bus entry gate where every bus passes.
- Keep reader at driver-window height for consistent scans.
- Use weather-protected enclosure if outdoors.
- Keep wiring short and secured in conduit.

ESP32 placement:
- Install ESP32 in lockable weather-safe electrical box near RFID reader.
- Power through stable 5V USB adapter with surge protection.
- Label each device by gate name (e.g., `Gate-A-ESP32`).

## 2) WiFi requirements at transport gate

Network requirements:
- Strong 2.4 GHz WiFi signal at every gate.
- Internet access allowed from ESP32 to deployed backend domain.
- DHCP enabled for ESP32 devices.
- Optional MAC allowlist for known ESP32 units.

Operational best practices:
- Deploy a dedicated SSID for transport IoT where possible.
- Monitor signal strength and packet loss during peak arrival times.

## 3) Bus and RFID mapping process

One-time setup per bus:
1. Assign one RFID tag/card to each bus.
2. Record tag UID using ESP32 serial output.
3. In admin module, map RFID UID to the correct bus record.
4. Verify route and assigned driver are correct.

Validation:
- Perform one scan per bus.
- Confirm arrival appears in admin dashboard live table.

## 4) On-ground scan flow

At arrival gate:
1. Bus presents mapped RFID tag.
2. Reader captures UID.
3. ESP32 sends request to deployed API `/api/bus-arrival`.
4. Server stores arrival and status (`on_time`/`late`).
5. Admin and management dashboards update in real time.

## 5) Admin operations

Admin team responsibilities:
- Create and maintain student/driver/bus records.
- Map RFID tags to buses.
- Review live arrival stream on admin dashboard.
- Resolve unknown RFID events (404) by correct mapping.
- Review duplicate scan events (409) for gate behavior tuning.

Daily checks:
- Verify `/health` endpoint.
- Verify at least one successful gate scan in morning run.
- Verify OTP and mileage upload systems are operational.

## 6) Management operations

Management dashboard usage:
- Monitor on-time vs late trend each day.
- Review attendance and transport performance reports.
- Use summary KPIs for transport policy decisions.

Reporting rhythm:
- Daily: arrivals and delays review.
- Weekly: route-level trend analysis.
- Monthly: fleet punctuality and operational planning.

## 7) Security and governance in campus environment

Minimum controls:
- Use strong production `SECRET_KEY`.
- Keep `SESSION_COOKIE_SECURE=True` in production.
- Restrict admin credentials and enforce role-based access.
- Store production secrets only in deployment platform env vars.
- Keep `.env` out of source control.

Recommended controls:
- Rotate email/app passwords periodically.
- Maintain gate device inventory with physical serial numbers.
- Restrict DB access to private networking and least privilege.

## 8) Incident handling

If gate scans fail:
1. Check ESP32 power and WiFi.
2. Check deployment health endpoint.
3. Check backend logs for API errors.
4. Validate RFID UID mapping for the bus.
5. Reboot ESP32 if needed and retest with one known UID.

If uploaded files are missing after redeploy:
- This is expected on ephemeral storage.
- Migrate file storage to Cloudinary or Amazon S3 for durable production use.

## 9) Recommended rollout plan for a college

Phase 1: Pilot (1 gate, 3-5 buses)
- Validate network reliability and dashboard behavior.
- Train transport admin users.

Phase 2: Controlled rollout (all gates, subset of routes)
- Add remaining buses and route mappings.
- Monitor morning peak throughput.

Phase 3: Full rollout (all routes)
- Use weekly KPIs to tune gate operations and schedule discipline.

## 10) Success criteria

Implementation is successful when:
- Every active bus has mapped RFID UID.
- Gate scans are consistently recorded in deployed backend.
- Admin dashboard reflects arrivals in near real-time.
- Management receives accurate punctuality trends.
- Transport team can support operations with minimal manual intervention.
