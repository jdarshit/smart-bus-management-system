"""reset_db.py — Wipe and recreate the Smart Bus database.

Usage:
    python reset_db.py

This script will:
  1. Drop ALL existing tables
  2. Recreate the schema from current models
  3. Seed the 4 predefined buses
  4. Print a summary
"""

from app import create_app
from extensions import db
from sqlalchemy import text
from models.bus_model import Bus
from models.system_settings_model import SystemSettings

PREDEFINED_BUSES = [
    {
        "bus_number":    "BUS_01",
        "license_plate": "MP09 AB 1234",
        "driver_name":   "Rahul Singh",
        "route_name":    "Vijay Nagar",
        "rfid_uid":      "72 3C 14 5C",
    },
    {
        "bus_number":    "BUS_02",
        "license_plate": "MP09 CD 5678",
        "driver_name":   "Arjun Patel",
        "route_name":    "Palasia",
        "rfid_uid":      "BC 51 4B 06",
    },
    {
        "bus_number":    "BUS_03",
        "license_plate": "MP09 EF 9012",
        "driver_name":   "Mohan Verma",
        "route_name":    "Bapat Square",
        "rfid_uid":      "82 27 39 5C",
    },
    {
        "bus_number":    "BUS_04",
        "license_plate": "MP09 GH 3456",
        "driver_name":   "Rakesh Yadav",
        "route_name":    "Rajendra Nagar",
        "rfid_uid":      "82 1A F7 05",
    },
]


def reset():
    app = create_app()
    with app.app_context():
        print("⚠  Dropping all tables (FK checks disabled)...")
        with db.engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            conn.commit()
        db.drop_all()
        with db.engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()
        print("✓  All tables dropped.")

        print("⚙  Creating tables from models...")
        db.create_all()
        print("✓  Tables created.")

        print("🚌 Seeding 4 predefined buses...")
        for data in PREDEFINED_BUSES:
            bus = Bus(**data)
            db.session.add(bus)

        db.session.add(SystemSettings(active_shift="shift1"))
        db.session.commit()
        print("✓  Buses seeded:")
        for b in Bus.query.all():
            print(f"   [{b.id}] {b.bus_number} | {b.driver_name} | {b.route_name} | RFID: {b.rfid_uid}")
        print("✓  Active shift initialized: SHIFT1")

        print()
        print("=" * 55)
        print("  DB reset complete!")
        print("  Next steps:")
        print("  1. Start the app:  python app.py")
        print("  2. Create an admin user via /auth/signup")
        print("  3. Test RFID scan:")
        print('     curl -X POST http://localhost:5000/api/rfid \\')
        print('          -H "Content-Type: application/json" \\')
        print('          -d \'{"uid": "72 3C 14 5C"}\'')
        print("=" * 55)


if __name__ == "__main__":
    reset()
