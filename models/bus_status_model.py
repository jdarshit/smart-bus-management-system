"""models/bus_status_model.py

Stores the latest RFID scan state per bus.
One row per bus – upserted on every successful student card scan.
"""
from datetime import datetime

from models import db


class BusStatus(db.Model):
    """Live status snapshot of each bus – updated on every RFID scan."""

    __tablename__ = "bus_status"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bus_id          = db.Column(
        db.Integer,
        db.ForeignKey("buses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # one row per bus
        index=True,
    )
    last_scan_time  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    updated_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    bus          = db.relationship("Bus",     lazy="joined")
    last_student = db.relationship("Student", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "bus_number":   self.bus.bus_number if self.bus else None,
            "last_scan":    self.last_scan_time.strftime("%Y-%m-%d %H:%M") if self.last_scan_time else None,
            "student":      self.last_student.student_name if self.last_student else None,
            "student_id":   self.last_student_id,
            "updated_at":   self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<BusStatus bus_id={self.bus_id} "
            f"last_student_id={self.last_student_id} "
            f"last_scan={self.last_scan_time}>"
        )
