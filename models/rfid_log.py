from datetime import datetime

from models import db


class RFIDLog(db.Model):
    """Raw RFID scan log for audit, debugging, and integration tracing."""

    __tablename__ = "rfid_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(100), nullable=False, index=True)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    latitude  = db.Column(db.Float, nullable=True)   # GPS coords recorded at scan time (optional)
    longitude = db.Column(db.Float, nullable=True)
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    student = db.relationship("Student", lazy="joined")
    bus = db.relationship("Bus", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "uid": self.uid,
            "bus_id": self.bus_id,
            "student_id": self.student_id,
            "latitude":   self.latitude,
            "longitude":  self.longitude,
            "scan_time": self.scan_time.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"<RFIDLog id={self.id} uid={self.uid!r} "
            f"student_id={self.student_id} bus_id={self.bus_id}>"
        )
