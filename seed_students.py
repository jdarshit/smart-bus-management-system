"""Seed predefined RFID test students for IoT validation.

Usage:
  python seed_students.py
  flask --app app seed_students
"""
from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.bus_model import Bus
from models.student_model import Student
from services.rfid_service import RFIDValidationError, normalize_uid

TEST_STUDENTS = [
    {
        "student_name": "Darshit Jain",
        "department": "CSIT",
        "year": 3,
        "bus_number": "BUS_01",
        "rfid_uid": "72 3C 14 5C",
        "pickup_point": "Vijay Nagar",
    },
    {
        "student_name": "Dipendra Gami",
        "department": "CSIT",
        "year": 3,
        "bus_number": "BUS_01",
        "rfid_uid": "BC 51 4B 6",
        "pickup_point": "Bapat Square",
    },
    {
        "student_name": "Ashwin Carpenter",
        "department": "CSIT",
        "year": 3,
        "bus_number": "BUS_01",
        "rfid_uid": "82 27 39 5C",
        "pickup_point": "Palasia",
    },
    {
        "student_name": "Kripa Raghuwanshi",
        "department": "CSIT",
        "year": 3,
        "bus_number": "BUS_01",
        "rfid_uid": "82 1A F7 5",
        "pickup_point": "Rajendra Nagar",
    },
]


def _ensure_bus(bus_number: str, output=print) -> Bus:
    bus = Bus.query.filter_by(bus_number=bus_number).first()
    if bus:
        return bus

    bus = Bus(bus_number=bus_number, route_name="RFID Test Route")
    db.session.add(bus)
    db.session.flush()  # ensure bus.id is available before student insert
    output(f"Bus {bus_number} created for RFID seeding")
    return bus


def seed_test_students(output=print) -> dict:
    """Insert test students if missing; skip if UID already exists."""
    inserted = 0
    skipped = 0

    try:
        bus_cache: dict[str, Bus] = {}

        for item in TEST_STUDENTS:
            raw_uid = item["rfid_uid"]
            try:
                normalized_uid = normalize_uid(raw_uid)
            except RFIDValidationError as exc:
                skipped += 1
                output(f"Skipping {item['student_name']}: invalid UID '{raw_uid}' ({exc})")
                continue

            existing = Student.query.filter_by(rfid_uid=normalized_uid).first()
            if existing:
                skipped += 1
                output(
                    f"Student already exists: {existing.student_name} "
                    f"(UID: {normalized_uid})"
                )
                continue

            bus_number = item["bus_number"]
            bus = bus_cache.get(bus_number)
            if bus is None:
                bus = _ensure_bus(bus_number, output=output)
                bus_cache[bus_number] = bus

            student = Student(
                student_name=item["student_name"],
                department=item["department"],
                year=item["year"],
                bus_id=bus.id,
                rfid_uid=normalized_uid,
                pickup_point=item["pickup_point"],
            )
            db.session.add(student)
            inserted += 1
            output(f"Student {item['student_name']} inserted")

        db.session.commit()
        output(f"Seeding complete: inserted={inserted}, skipped={skipped}")
        return {"inserted": inserted, "skipped": skipped}

    except SQLAlchemyError as exc:
        db.session.rollback()
        raise RuntimeError(f"Database error while seeding students: {exc}") from exc


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_test_students()
