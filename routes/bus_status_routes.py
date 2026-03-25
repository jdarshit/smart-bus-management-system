"""routes/bus_status_routes.py

Public JSON API for bus status.

  GET /api/bus_status            – all buses (legacy payload)
  GET /api/bus_status/<bus_id>   – GPS-optional snapshot payload
"""
from flask import Blueprint, jsonify

from services.bus_status_service import get_all_bus_status, get_bus_status_snapshot

bus_status_bp = Blueprint("bus_status", __name__, url_prefix="/api")


@bus_status_bp.get("/bus_status")
def all_bus_status():
    """Return live status for every bus that has had at least one scan."""
    return jsonify(get_all_bus_status())


@bus_status_bp.get("/bus_status/<string:bus_id>")
def single_bus_status(bus_id: str):
    """GPS-optional status endpoint.

    Response:
    {
      "bus_id": "BUS_01",
      "last_rfid_scan": "2026-03-15 12:20",
      "latitude": null,
      "longitude": null
    }
    """
    data = get_bus_status_snapshot(bus_id)
    if data is None:
        return jsonify({
            "status": "not_found",
            "message": f"Bus '{bus_id}' not found",
        }), 404
    return jsonify(data)
