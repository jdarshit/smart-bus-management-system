"""routes/gps_routes.py

GPS position API consumed by ESP32+NEO-6M firmware and by parents.

  POST /api/gps                                 – store a GPS fix
  GET  /api/bus_location/<bus_number>           – latest fix for one bus
  GET  /api/all_bus_locations                   – latest fix for all buses (map AJAX)
  GET  /api/student_bus_location/<student_id>   – parent tracking endpoint
"""
from flask import Blueprint, jsonify, request

from services.bus_tracking_service import (
    get_live_bus_markers,
    get_parent_tracking_payload,
)
from services.gps_service import (
    BusNotFoundError,
    GPSValidationError,
    get_latest_location,
    store_gps_fix,
)

gps_bp = Blueprint("gps", __name__, url_prefix="/api")


# ------------------------------------------------------------------ #
#  POST /api/gps  – ESP32 sends position here                          #
# ------------------------------------------------------------------ #

@gps_bp.post("/gps")
def receive_gps():
    """Accept a GPS fix from an ESP32+NEO-6M module.

    Payload (JSON):
      {
        "bus_id":    "BUS_01",
        "latitude":  22.7196,
        "longitude": 75.8577,
        "timestamp": "2026-03-15 11:50"   // optional; omit for server time
      }

    Returns 200 on success, 400/404/500 on error.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    bus_id    = payload.get("bus_id")
    latitude  = payload.get("latitude")
    longitude = payload.get("longitude")
    timestamp = payload.get("timestamp")

    print(f"[GPS ] Received fix → bus={bus_id!r}  lat={latitude}  lng={longitude}")

    if not bus_id:
        return jsonify({"status": "error", "message": "bus_id is required"}), 400

    try:
        location = store_gps_fix(
            bus_identifier=bus_id,
            latitude=latitude,
            longitude=longitude,
            raw_timestamp=timestamp,
        )
    except GPSValidationError as exc:
        print(f"[GPS ] 400 Validation: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 400
    except BusNotFoundError as exc:
        print(f"[GPS ] 404 Bus not found: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 404
    except RuntimeError as exc:
        print(f"[GPS ] 500 DB error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({
        "status":     "success",
        "message":    "GPS fix stored",
        "bus_id":     bus_id,
        "latitude":   location.latitude,
        "longitude":  location.longitude,
        "timestamp":  location.timestamp.isoformat(),
    }), 200


# ------------------------------------------------------------------ #
#  GET /api/bus_location/<bus_number>                                  #
# ------------------------------------------------------------------ #

@gps_bp.get("/bus_location/<string:bus_number>")
def bus_location(bus_number: str):
    """Return the most recent GPS fix for a specific bus.

    Response:
      { "bus_id": "BUS_01", "latitude": 22.7196, "longitude": 75.8577,
        "last_update": "2026-03-15 11:50" }
    """
    try:
        data = get_latest_location(bus_number)
    except BusNotFoundError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except GPSValidationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    if data is None:
        return jsonify({
            "status":  "no_data",
            "message": f"No GPS data available yet for bus '{bus_number}'",
        }), 404

    return jsonify(data)


# ------------------------------------------------------------------ #
#  GET /api/all_bus_locations  – AJAX feed for Leaflet map             #
# ------------------------------------------------------------------ #

@gps_bp.get("/all_bus_locations")
def all_bus_locations():
    """Return latest GPS fixes for ALL buses as a JSON array.

    Used by the admin Leaflet map to update markers every 5 seconds.
    Each entry also contains the last scanned student name.
    """
    return jsonify(get_live_bus_markers())


# ------------------------------------------------------------------ #
#  GET /api/student_bus_location/<student_id>  – parent tracking       #
# ------------------------------------------------------------------ #

@gps_bp.get("/student_bus_location/<int:student_id>")
def student_bus_location(student_id: int):
    """Parent-facing endpoint: returns bus location + boarding status.

    Response:
      { "student": "Rahul Sharma", "bus_id": "BUS_01",
        "latitude": 22.7196, "longitude": 75.8577,
        "last_update": "2026-03-15 11:50", "status": "On Bus" }
    """
    try:
        data = get_parent_tracking_payload(student_id)
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404

    if data is None:
        return jsonify({
            "status":  "no_data",
            "message": "No GPS data available for this student's bus",
        }), 404

    return jsonify(data)
