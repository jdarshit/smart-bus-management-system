"""services/rfid_assignment_service.py

Admin-facing service: assign or update the RFID UID stored
against a Student record.
"""
from __future__ import annotations

import re

from sqlalchemy.exc import SQLAlchemyError

from models import db
from models.student_model import Student


class AssignmentError(ValueError):
    """Raised when an RFID assignment cannot be completed."""


def normalize_uid_for_assignment(raw_uid: str) -> str:
    """Normalise an admin-entered or card-scan UID.

    Accepts any of:
      - "72 3C 14 5C"   (spaced hex)
      - "72:3C:14:5C"   (colon-sep)
      - "723C145C"       (compact)
      - "72 3c 14 5c"   (mixed case)
    Returns uppercase space-separated form, e.g. "72 3C 14 5C".
    """
    raw = (raw_uid or "").strip()
    if not raw:
        raise AssignmentError("rfid_uid is required")

    # Split on any separator
    parts = re.split(r"[\s:,\-]+", raw)
    parts = [p for p in parts if p]

    if len(parts) >= 4:
        normalized: list[str] = []
        for part in parts:
            if not re.fullmatch(r"[A-Fa-f0-9]{1,2}", part):
                raise AssignmentError(f"Invalid hex byte '{part}' in UID")
            normalized.append(part.upper().zfill(2))
        return " ".join(normalized)

    # Compact hex fallback
    cleaned = re.sub(r"[^A-Fa-f0-9]", "", raw)
    if len(cleaned) >= 8 and len(cleaned) % 2 == 0:
        cleaned = cleaned.upper()
        return " ".join(cleaned[i : i + 2] for i in range(0, len(cleaned), 2))

    raise AssignmentError("UID must be at least 4 hex bytes (e.g. 72 3C 14 5C)")


def assign_rfid_to_student(student_id: int, raw_uid: str) -> Student:
    """Set students.rfid_uid for the given student.

    Raises
    ------
    AssignmentError   – bad UID format or UID already owned by another student.
    LookupError       – student_id not found.
    RuntimeError      – database commit failure.
    """
    uid = normalize_uid_for_assignment(raw_uid)

    student = Student.query.get(student_id)
    if student is None:
        raise LookupError(f"Student {student_id} not found")

    # Reject if another student already owns this UID
    existing = Student.query.filter(
        Student.rfid_uid == uid, Student.id != student_id
    ).first()
    if existing:
        raise AssignmentError(
            f"UID {uid} is already assigned to {existing.student_name} (id={existing.id})"
        )

    student.rfid_uid = uid
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Database error while saving RFID assignment") from exc

    return student


def remove_rfid_from_student(student_id: int) -> Student:
    """Clear the rfid_uid field for a student."""
    student = Student.query.get(student_id)
    if student is None:
        raise LookupError(f"Student {student_id} not found")

    student.rfid_uid = None
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError("Database error while removing RFID assignment") from exc

    return student
