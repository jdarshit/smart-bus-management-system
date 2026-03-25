"""IoT RFID bus arrival APIs."""

import datetime

from flask import Blueprint, current_app, jsonify, request

from models import db
from models.arrival_model import Arrival
from models.bus_model import Bus

iot_bp = Blueprint("iot", __name__, url_prefix="/api")


def _normalize_rfid_uid(raw_uid: str) -> str:
    return "".join((raw_uid or "").strip().upper().split())


def _arrival_cutoff(now: datetime.datetime) -> datetime.datetime:
    return now.replace(
        hour=current_app.config.get("BUS_ARRIVAL_CUTOFF_HOUR", 9),
        minute=current_app.config.get("BUS_ARRIVAL_CUTOFF_MINUTE", 10),
        second=0,
        microsecond=0,
    )


def _calculate_status(arrival_dt: datetime.datetime) -> str:
    return "on_time" if arrival_dt <= _arrival_cutoff(arrival_dt) else "late"


def _is_duplicate(bus_id: int, now: datetime.datetime) -> bool:
    threshold = now - datetime.timedelta(
        seconds=current_app.config.get("BUS_ARRIVAL_DEBOUNCE_SECONDS", 15)
    )
    latest = (
        Arrival.query
        .filter(Arrival.bus_id == bus_id, Arrival.arrival_time >= threshold)
        .order_by(Arrival.arrival_time.desc())
        .first()
    )
    return latest is not None


def _serialize_arrival(arrival: Arrival) -> dict:
    bus = arrival.bus
    driver_name = bus.driver_name if bus and bus.driver_name else "Unassigned"
    return {
        "id": arrival.id,
        "bus_id": arrival.bus_id,
        "bus_number": bus.bus_number if bus else "Unknown",
        "route_name": bus.route_name if bus and bus.route_name else "N/A",
        "driver_name": driver_name,
        "arrival_time": arrival.arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": arrival.status,
    }


def _today_summary() -> dict:
    today = datetime.date.today()
    today_arrivals = Arrival.query.filter(db.func.date(Arrival.arrival_time) == today).all()
    on_time_count = sum(1 for item in today_arrivals if item.status == "on_time")
    late_count = sum(1 for item in today_arrivals if item.status == "late")
    return {
        "on_time_buses": on_time_count,
        "late_buses": late_count,
        "total_arrivals_today": len(today_arrivals),
        "cutoff_time": f"{current_app.config.get('BUS_ARRIVAL_CUTOFF_HOUR', 9):02d}:{current_app.config.get('BUS_ARRIVAL_CUTOFF_MINUTE', 10):02d}",
    }


@iot_bp.route("/bus-arrival", methods=["POST"])
def bus_arrival():
    payload = request.get_json(silent=True) or {}
    rfid_uid = _normalize_rfid_uid(payload.get("rfid_uid", ""))

    if not rfid_uid:
        return jsonify({"message": "rfid_uid is required"}), 400

    bus = Bus.query.filter_by(rfid_uid=rfid_uid).first()
    if not bus:
        return jsonify({"message": "Unknown RFID UID", "rfid_uid": rfid_uid}), 404

    now = datetime.datetime.now()
    if _is_duplicate(bus.id, now):
        latest = (
            Arrival.query.filter_by(bus_id=bus.id)
            .order_by(Arrival.arrival_time.desc())
            .first()
        )
        return jsonify(
            {
                "message": "Duplicate scan ignored",
                "bus_number": bus.bus_number,
                "route_name": bus.route_name or "N/A",
                "arrival_time": latest.arrival_time.strftime("%Y-%m-%d %H:%M:%S") if latest else now.strftime("%Y-%m-%d %H:%M:%S"),
                "status": latest.status if latest else _calculate_status(now),
            }
        ), 409

    arrival = Arrival(
        bus_id=bus.id,
        arrival_time=now,
        status=_calculate_status(now),
    )
    db.session.add(arrival)
    db.session.commit()

    return jsonify(
        {
            "message": "Bus arrival recorded successfully",
            "bus_number": bus.bus_number,
            "route_name": bus.route_name or "N/A",
            "arrival_time": arrival.arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": arrival.status,
        }
    ), 201


@iot_bp.route("/latest-arrivals", methods=["GET"])
@iot_bp.route("/arrivals/recent", methods=["GET"])
def latest_arrivals():
    try:
        limit = min(int(request.args.get("limit", 10)), 100)
    except ValueError:
        limit = 10

    arrivals = Arrival.query.order_by(Arrival.arrival_time.desc()).limit(limit).all()
    return jsonify({"count": len(arrivals), "arrivals": [_serialize_arrival(item) for item in arrivals]})


@iot_bp.route("/bus-status-summary", methods=["GET"])
def bus_status_summary():
    return jsonify(_today_summary())


@iot_bp.route("/bus-status", methods=["GET"])
def bus_status():
    buses = Bus.query.order_by(Bus.bus_number).all()
    result = []
    for bus in buses:
        latest = bus.arrivals.order_by(Arrival.arrival_time.desc()).first()
        result.append(
            {
                "bus_id": bus.id,
                "bus_number": bus.bus_number,
                "route_name": bus.route_name or "N/A",
                "rfid_uid": bus.rfid_uid,
                "last_arrival": latest.arrival_time.strftime("%Y-%m-%d %H:%M:%S") if latest else None,
                "current_status": latest.status if latest else "pending",
            }
        )
    return jsonify({"buses": result, **_today_summary()})
