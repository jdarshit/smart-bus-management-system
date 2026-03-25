"""services/gps_service.py

Business logic for:
  - Storing incoming GPS fixes from ESP32+NEO-6M
  - Serving the latest position per bus
  - Parent-facing student-bus location lookup
"""
from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.bus_location import BusLocation
from models.bus_model import Bus
from models.rfid_log import RFIDLog
from models.student import Student

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Exceptions                                                          #
# ------------------------------------------------------------------ #

class GPSValidationError(ValueError):
    """Raised for invalid GPS payload."""


class BusNotFoundError(LookupError):
    """Raised when the bus identifier cannot be resolved."""


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _resolve_bus(bus_identifier: str | None) -> Bus:
    """Resolve bus by numeric id or bus_number string."""
    value = (bus_identifier or "").strip()
    if not value:
        raise GPSValidationError("bus_id is required")

    if value.isdigit():
        bus = Bus.query.filter_by(id=int(value)).first()
        if bus:
            return bus

    bus = Bus.query.filter_by(bus_number=value).first()
    if bus:
        return bus

    raise BusNotFoundError(f"Bus '{value}' not found")


def _parse_timestamp(raw: str | None) -> dt.datetime:
    if not raw or str(raw).strip().lower() in ("", "auto"):
        return dt.datetime.utcnow()

    value = str(raw).strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise GPSValidationError("Invalid timestamp format") from exc

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return parsed


def _validate_coords(lat, lng) -> tuple[float, float]:
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        raise GPSValidationError("latitude and longitude must be numbers")

    if not (-90 <= lat <= 90):
        raise GPSValidationError(f"latitude {lat} out of range [-90, 90]")
    if not (-180 <= lng <= 180):
        raise GPSValidationError(f"longitude {lng} out of range [-180, 180]")

    return lat, lng


# ------------------------------------------------------------------ #
#  Core: store a GPS fix                                               #
# ------------------------------------------------------------------ #

def store_gps_fix(
    bus_identifier: str,
    latitude,
    longitude,
    raw_timestamp: str | None = None,
) -> BusLocation:
    """Validate and persist one GPS position fix.

    Raises GPSValidationError, BusNotFoundError, or RuntimeError.
    """
    bus = _resolve_bus(bus_identifier)
    lat, lng = _validate_coords(latitude, longitude)
    ts = _parse_timestamp(raw_timestamp)

    location = BusLocation(
        bus_id=bus.id,
        latitude=lat,
        longitude=lng,
        timestamp=ts,
    )
    db.session.add(location)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Database error while saving GPS fix") from exc

    logger.info("[GPS] bus=%s  lat=%.5f  lng=%.5f  ts=%s", bus.bus_number, lat, lng, ts)
    return location


# ------------------------------------------------------------------ #
#  Query: latest position per bus                                      #
# ------------------------------------------------------------------ #

def get_latest_location(bus_identifier: str) -> dict | None:
    """Return the most recent GPS fix for one bus, or None."""
    bus = _resolve_bus(bus_identifier)

    row = (
        BusLocation.query
        .filter_by(bus_id=bus.id)
        .order_by(BusLocation.timestamp.desc())
        .first()
    )
    if row is None:
        return None

    return {
        "bus_id":      bus.bus_number,
        "latitude":    row.latitude,
        "longitude":   row.longitude,
        "last_update": row.timestamp.strftime("%Y-%m-%d %H:%M"),
    }


def get_all_latest_locations() -> list[dict]:
    """Return the latest GPS fix for every bus that has sent a fix.

    Uses a subquery to pick the max timestamp per bus_id.
    """
    sub = (
        db.session.query(
            BusLocation.bus_id,
            db.func.max(BusLocation.timestamp).label("max_ts"),
        )
        .group_by(BusLocation.bus_id)
        .subquery()
    )

    rows = (
        BusLocation.query
        .join(sub, db.and_(
            BusLocation.bus_id    == sub.c.bus_id,
            BusLocation.timestamp == sub.c.max_ts,
        ))
        .all()
    )

    results = []
    for row in rows:
        last_rfid = (
            RFIDLog.query
            .filter_by(bus_id=row.bus_id)
            .order_by(RFIDLog.scan_time.desc())
            .first()
        )
        results.append({
            "bus_id":       row.bus.bus_number if row.bus else str(row.bus_id),
            "latitude":     row.latitude,
            "longitude":    row.longitude,
            "last_update":  row.timestamp.strftime("%Y-%m-%d %H:%M"),
            "last_student": (
                last_rfid.student.student_name
                if last_rfid and last_rfid.student
                else None
            ),
        })

    return results


# ------------------------------------------------------------------ #
#  Query: parent-facing student bus location                           #
# ------------------------------------------------------------------ #

def get_student_bus_location(student_id: int) -> dict | None:
    """Return bus location for the bus the student is assigned to.

    Returns None if the student has no bus assignment or no GPS data.
    Raises LookupError if student_id does not exist.
    """
    student = Student.query.get(student_id)
    if student is None:
        raise LookupError(f"Student {student_id} not found")

    bus_number = (student.bus_number or "").strip() if hasattr(student, "bus_number") else ""
    if not bus_number:
        return None

    bus = Bus.query.filter_by(bus_number=bus_number).first()
    if bus is None:
        return None

    location = (
        BusLocation.query
        .filter_by(bus_id=bus.id)
        .order_by(BusLocation.timestamp.desc())
        .first()
    )
    if location is None:
        return None

    today = dt.date.today()
    last_scan = (
        RFIDLog.query
        .filter_by(student_id=student_id, bus_id=bus.id)
        .filter(db.func.date(RFIDLog.scan_time) == today)
        .order_by(RFIDLog.scan_time.desc())
        .first()
    )
    status = "On Bus" if last_scan else "Not yet boarded"

    student_label = getattr(student, "student_name", None) or getattr(student, "name", None) or f"Student {student.id}"

    return {
        "student":     student_label,
        "bus_id":      bus.bus_number,
        "latitude":    location.latitude,
        "longitude":   location.longitude,
        "last_update": location.timestamp.strftime("%Y-%m-%d %H:%M"),
        "status":      status,
    }
