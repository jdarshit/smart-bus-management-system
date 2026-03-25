"""routes/rfid_api.py  —  ESP32 gate RFID endpoint.

POST /api/rfid
  Body: {"uid": "72 3C 14 5C"}
  Returns 201 with arrival details on success.
"""
from flask import Blueprint, jsonify, request
from time import perf_counter

from services.bus_arrival_service import (
    BusRFIDNotFoundError,
    BusRFIDValidationError,
    get_active_shift,
    process_bus_rfid_scan,
    set_active_shift,
)
from utils.auth_helpers import login_required, role_required

rfid_bp = Blueprint("rfid", __name__, url_prefix="/api")


@rfid_bp.post("/rfid")
def handle_rfid_scan():
    started_at = perf_counter()
    payload = request.get_json(silent=True) or {}
    uid = payload.get("uid")

    try:
        result = process_bus_rfid_scan(uid=uid)
    except BusRFIDValidationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except BusRFIDNotFoundError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

    elapsed_ms = round((perf_counter() - started_at) * 1000.0, 2)
    return jsonify({
        "result":        "success",
        "message":       "Bus arrival recorded",
        "bus_id":        result.bus_id,
        "bus_number":    result.bus_number,
        "license_plate": result.license_plate,
        "driver_name":   result.driver_name,
        "route_name":    result.route_name,
        "rfid_uid":      result.rfid_uid,
        "arrival_time":  result.arrival_time,
        "status":        result.status,
        "shift":         result.shift,
        "processing_ms": elapsed_ms,
    }), 201


@rfid_bp.post("/set_shift")
@login_required
@role_required("admin")
def set_shift():
    payload = request.get_json(silent=True) or {}
    shift = (payload.get("shift") or "").strip().lower()

    try:
        active_shift = set_active_shift(shift)
    except BusRFIDValidationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({
        "status": "success",
        "active_shift": active_shift,
    }), 200


@rfid_bp.get("/active_shift")
@login_required
@role_required("admin", "management")
def active_shift():
    return jsonify({"active_shift": get_active_shift()}), 200
