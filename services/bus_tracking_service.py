"""services/bus_tracking_service.py

Higher-level tracking service built on top of gps_service.
Keeps route/controller code thin and centralises map/parent query logic.
"""
from __future__ import annotations

from services.gps_service import get_all_latest_locations, get_student_bus_location


def get_live_bus_markers() -> list[dict]:
    """Return latest location + last scanned student for each active bus."""
    return get_all_latest_locations()


def get_parent_tracking_payload(student_id: int) -> dict | None:
    """Return parent-facing student bus location payload."""
    return get_student_bus_location(student_id)
