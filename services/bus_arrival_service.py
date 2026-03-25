"""services/bus_arrival_service.py

Bus-centric RFID gate arrival service with admin-selected active shift.

Shift rules (India time):
    shift1: Late if arrival_time.time() > 07:25
    shift2: Late if arrival_time.time() > 10:25
"""
import datetime as dt
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func
from zoneinfo import ZoneInfo

from extensions import db
from models.bus_arrival_log import BusArrivalLog
from models.bus_model import Bus
from models.system_settings_model import SystemSettings

try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    INDIA_TZ = dt.timezone(dt.timedelta(hours=5, minutes=30))

# ── Predefined buses (authoritative source of truth) ─────────────────────────
PREDEFINED_BUSES = [
    {
        "bus_number":    "BUS_01",
        "license_plate": "MP09 6271",
        "driver_name":   "Rahul Singh",
        "route_name":    "Vijay Nagar",
        "rfid_uid":      "72 3C 14 5C",
    },
    {
        "bus_number":    "BUS_02",
        "license_plate": "MP09 7123",
        "driver_name":   "Arjun Patel",
        "route_name":    "Palasia",
        "rfid_uid":      "BC 51 4B 06",
    },
    {
        "bus_number":    "BUS_03",
        "license_plate": "MP09 8892",
        "driver_name":   "Mohan Verma",
        "route_name":    "Bapat Square",
        "rfid_uid":      "82 27 39 5C",
    },
    {
        "bus_number":    "BUS_04",
        "license_plate": "MP09 4321",
        "driver_name":   "Rakesh Yadav",
        "route_name":    "Rajendra Nagar",
        "rfid_uid":      "82 1A F7 05",
    },
]

# ── Custom exceptions ─────────────────────────────────────────────────────────

class BusRFIDValidationError(ValueError):
    pass


class BusRFIDNotFoundError(LookupError):
    pass


# ── Data transfer object ──────────────────────────────────────────────────────

@dataclass
class BusArrivalResult:
    bus_id:        int
    bus_number:    str
    license_plate: str | None
    driver_name:   str | None
    route_name:    str | None
    rfid_uid:      str
    arrival_time:  str
    status:        str
    shift:         str


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_uid(raw_uid: str) -> str:
    """Normalise any UID format to 'AA BB CC DD' (space-separated uppercase hex)."""
    parts = [p for p in (raw_uid or "").replace(":", " ").replace("-", " ").split() if p]
    if len(parts) >= 4:
        out = []
        for part in parts:
            if not all(ch in "0123456789abcdefABCDEF" for ch in part) or len(part) > 2:
                raise BusRFIDValidationError("Invalid UID format")
            out.append(part.upper().zfill(2))
        return " ".join(out)

    compact = "".join(ch for ch in (raw_uid or "") if ch.lower() in "0123456789abcdef")
    if len(compact) < 8 or len(compact) % 2 != 0:
        raise BusRFIDValidationError("Invalid UID format")
    compact = compact.upper()
    return " ".join(compact[i:i + 2] for i in range(0, len(compact), 2))


def _now_india() -> dt.datetime:
    """Return current India time as a timezone-naive datetime."""
    return dt.datetime.now(INDIA_TZ).replace(tzinfo=None)


def _calculate_status(arrival_time: dt.datetime, active_shift: str) -> str:
    """Apply late rule using currently selected active shift."""
    t = arrival_time.time()
    if active_shift == "shift1":
        return "Late" if t > dt.time(7, 25) else "On Time"
    return "Late" if t > dt.time(10, 25) else "On Time"


def get_active_shift() -> str:
    row = SystemSettings.get_singleton()
    if row.active_shift not in {"shift1", "shift2"}:
        row.active_shift = "shift1"
        db.session.commit()
    return row.active_shift


def set_active_shift(shift: str) -> str:
    if shift not in {"shift1", "shift2"}:
        raise BusRFIDValidationError("shift must be 'shift1' or 'shift2'")
    row = SystemSettings.get_singleton()
    row.active_shift = shift
    db.session.commit()
    return row.active_shift


# ── Public API ────────────────────────────────────────────────────────────────

def ensure_predefined_buses() -> dict:
    """Upsert the four predefined buses on startup."""
    created = updated = 0
    for data in PREDEFINED_BUSES:
        bus = Bus.query.filter_by(bus_number=data["bus_number"]).first()
        if not bus:
            bus = Bus(bus_number=data["bus_number"])
            db.session.add(bus)
            created += 1
        else:
            updated += 1
        bus.license_plate = data["license_plate"]
        bus.driver_name   = data["driver_name"]
        bus.route_name    = data["route_name"]
        bus.rfid_uid      = data["rfid_uid"]
    db.session.commit()
    SystemSettings.get_singleton()
    return {"created": created, "updated": updated}


def process_bus_rfid_scan(uid: str) -> BusArrivalResult:
    """Validate UID, find bus, calculate status, write BusArrivalLog."""
    if not uid:
        raise BusRFIDValidationError("uid is required")

    normalized_uid = normalize_uid(uid)
    bus = (
        Bus.query
        .with_entities(Bus.id, Bus.bus_number, Bus.license_plate, Bus.driver_name, Bus.route_name)
        .filter(Bus.rfid_uid == normalized_uid)
        .first()
    )
    if not bus:
        raise BusRFIDNotFoundError("Unknown bus RFID UID")

    arrival_time = _now_india()
    active_shift = get_active_shift()
    status       = _calculate_status(arrival_time, active_shift)

    log = BusArrivalLog(
        bus_id        = bus.id,
        bus_number    = bus.bus_number,
        license_plate = bus.license_plate,
        driver_name   = bus.driver_name,
        route_name    = bus.route_name,
        rfid_uid      = normalized_uid,
        arrival_time  = arrival_time,
        status        = status,
        shift         = active_shift,
    )
    db.session.add(log)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Failed to store bus arrival") from exc

    return BusArrivalResult(
        bus_id        = bus.id,
        bus_number    = bus.bus_number,
        license_plate = bus.license_plate,
        driver_name   = bus.driver_name,
        route_name    = bus.route_name,
        rfid_uid      = normalized_uid,
        arrival_time  = arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
        status        = status,
        shift         = active_shift,
    )


def latest_bus_arrivals(limit: int = 100) -> list[dict]:
    """Return most-recent bus arrival logs ordered newest-first."""
    rows = (
        BusArrivalLog.query
        .order_by(BusArrivalLog.arrival_time.desc())
        .limit(limit)
        .all()
    )
    return [row.to_dict() for row in rows]


def tv_bus_status_snapshot() -> dict:
    """Return card-friendly status for all buses for the TV dashboard."""
    buses = Bus.query.order_by(Bus.bus_number.asc()).all()
    today_india = _now_india().date()
    active_shift = get_active_shift()
    latest_subquery = (
        db.session.query(
            BusArrivalLog.bus_id.label("bus_id"),
            func.max(BusArrivalLog.arrival_time).label("max_arrival_time"),
        )
        .group_by(BusArrivalLog.bus_id)
        .subquery()
    )
    latest_rows = (
        db.session.query(BusArrivalLog)
        .join(
            latest_subquery,
            and_(
                BusArrivalLog.bus_id == latest_subquery.c.bus_id,
                BusArrivalLog.arrival_time == latest_subquery.c.max_arrival_time,
            ),
        )
        .all()
    )
    latest_by_bus = {row.bus_id: row for row in latest_rows}

    data = []
    for bus in buses:
        latest = latest_by_bus.get(bus.id)

        if latest is None or latest.arrival_time.date() != today_india:
            data.append({
                "bus_id": bus.id,
                "bus_number": bus.bus_number,
                "license_plate": bus.license_plate,
                "driver_name": bus.driver_name,
                "route_name": bus.route_name,
                "arrival_time": None,
                "status": "Waiting",
                "shift": active_shift,
            })
            continue

        data.append({
            "bus_id": bus.id,
            "bus_number": bus.bus_number,
            "license_plate": bus.license_plate,
            "driver_name": bus.driver_name,
            "route_name": bus.route_name,
            "arrival_time": latest.arrival_time.strftime("%H:%M:%S"),
            "status": latest.status,
            "shift": latest.shift,
        })

    return {
        "active_shift": active_shift,
        "buses": data,
    }


def lightweight_bus_status() -> dict:
    """Ultra-light polling payload for dashboard cards."""
    snapshot = tv_bus_status_snapshot()
    return {
        "active_shift": snapshot["active_shift"],
        "buses": [
            {
                "bus_number": b["bus_number"],
                "license_plate": b["license_plate"],
                "driver_name": b["driver_name"],
                "route_name": b["route_name"],
                "arrival_time": b["arrival_time"],
                "status": b["status"],
                "shift": b["shift"],
            }
            for b in snapshot["buses"]
        ],
    }
