"""Service layer for RFID student attendance and bus arrival processing."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from models import db
from models.arrival_model import Arrival
from models.attendance_model import Attendance
from models.bus_model import Bus
from models.bus_location import BusLocation
from models.rfid_log import RFIDLog
from models.student_model import Student
# Imported lazily inside process_rfid_scan to avoid potential circular import
# from services.bus_status_service import update_bus_status, send_boarding_email

class RFIDValidationError(ValueError):
    """Raised when RFID payload validation fails."""


class RFIDNotFoundError(LookupError):
    """Raised when a scanned RFID UID is not mapped to a student."""


class BusResolutionError(LookupError):
    """Raised when the provided bus identifier cannot be resolved."""


@dataclass
class RFIDResult:
    student_id: int
    student_name: str
    bus_id: str
    attendance_marked: bool
    attendance_status: str
    arrival_recorded: bool
    notification_sent: bool
    scan_time: str


def normalize_uid(raw_uid: str) -> str:
    """Normalize UID to uppercase, space-separated 2-char hex bytes.

    Handles ESP32 output like '82 1a f7 5' where HEX print omits the
    leading zero for values < 0x10 (e.g. '5' should be '05').
    Also accepts compact strings like '821af705'.
    """
    raw = (raw_uid or "").strip()
    if not raw:
        raise RFIDValidationError("uid is required")

    # Try splitting by common separators first (handles '82 1a f7 5' style)
    parts = re.split(r"[\s:,\-]+", raw)
    parts = [p for p in parts if p]

    if len(parts) >= 4:
        normalized = []
        for part in parts:
            if not re.fullmatch(r"[A-Fa-f0-9]{1,2}", part):
                raise RFIDValidationError(f"Invalid hex byte in UID: '{part}'")
            normalized.append(part.upper().zfill(2))
        return " ".join(normalized)

    # Fallback: treat as compact hex string (e.g. '821af705')
    cleaned = re.sub(r"[^A-Fa-f0-9]", "", raw)
    if len(cleaned) >= 8 and len(cleaned) % 2 == 0:
        cleaned = cleaned.upper()
        return " ".join(cleaned[i:i + 2] for i in range(0, len(cleaned), 2))

    raise RFIDValidationError("Invalid UID format: expected at least 4 hex bytes")


def validate_uid(raw_uid: str) -> str:
    candidate = (raw_uid or "").strip()
    if not candidate:
        raise RFIDValidationError("uid is required")
    return normalize_uid(candidate)


def parse_scan_time(raw_timestamp: str | None) -> dt.datetime:
    if not raw_timestamp or raw_timestamp.strip().lower() == "auto":
        return dt.datetime.utcnow()

    value = raw_timestamp.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise RFIDValidationError("Invalid timestamp format") from exc

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return parsed


def resolve_bus(bus_identifier: str | None) -> Bus:
    value = (bus_identifier or "").strip()
    if not value:
        raise RFIDValidationError("bus_id is required")

    if value.isdigit():
        bus = Bus.query.filter_by(id=int(value)).first()
        if bus:
            return bus

    bus = Bus.query.filter_by(bus_number=value).first()
    if bus:
        return bus

    raise BusResolutionError("Unknown bus")


def _arrival_status(scan_time: dt.datetime, cutoff_hour: int, cutoff_minute: int) -> str:
    cutoff = scan_time.replace(hour=cutoff_hour, minute=cutoff_minute, second=0, microsecond=0)
    return "on_time" if scan_time <= cutoff else "late"


def process_rfid_scan(
    *,
    uid: str,
    bus_identifier: str,
    timestamp: str | None,
    cutoff_hour: int,
    cutoff_minute: int,
    latitude: float | None = None,
    longitude: float | None = None,
) -> RFIDResult:
    normalized_uid = validate_uid(uid)
    scan_time = parse_scan_time(timestamp)

    student = Student.query.filter_by(rfid_uid=normalized_uid).first()
    if not student:
        raise RFIDNotFoundError("Unknown RFID")

    bus = resolve_bus(bus_identifier)

    lat_value = None
    lng_value = None
    if latitude is not None and longitude is not None:
        try:
            lat_value = float(latitude)
            lng_value = float(longitude)
        except (TypeError, ValueError) as exc:
            raise RFIDValidationError("latitude and longitude must be numeric") from exc

    if lat_value is None or lng_value is None:
        latest_location = (
            BusLocation.query
            .filter_by(bus_id=bus.id)
            .order_by(BusLocation.timestamp.desc())
            .first()
        )
        if latest_location:
            lat_value = latest_location.latitude
            lng_value = latest_location.longitude

    attendance = Attendance.query.filter_by(student_id=student.id, date=scan_time.date()).first()
    attendance_marked = False

    if attendance is None:
        attendance = Attendance(student_id=student.id, date=scan_time.date(), status="present")
        db.session.add(attendance)
        attendance_marked = True
    elif attendance.status != "present":
        attendance.status = "present"
        attendance_marked = True

    arrival = Arrival(
        bus_id=bus.id,
        arrival_time=scan_time,
        status=_arrival_status(scan_time, cutoff_hour, cutoff_minute),
    )
    db.session.add(arrival)

    scan_log = RFIDLog(
        uid=normalized_uid,
        student_id=student.id,
        bus_id=bus.id,
        latitude=lat_value,
        longitude=lng_value,
        scan_time=scan_time,
    )
    db.session.add(scan_log)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Failed to save RFID scan") from exc

    # Post-commit side-effects (non-fatal – never crash a scan due to these)
    try:
        from services.bus_status_service import update_bus_status, send_boarding_email
        update_bus_status(bus, student, scan_time)
        emailed = send_boarding_email(student, bus, scan_time)
    except Exception:
        emailed = False

    return RFIDResult(
        student_id=student.id,
        student_name=student.student_name,
        bus_id=bus.bus_number,
        attendance_marked=attendance_marked,
        attendance_status=attendance.status,
        arrival_recorded=True,
        notification_sent=emailed,
        scan_time=scan_time.isoformat(sep=" ", timespec="seconds"),
    )
