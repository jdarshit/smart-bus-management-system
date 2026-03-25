from datetime import datetime

from sqlalchemy import CheckConstraint

from models import db


class Arrival(db.Model):
    """
    Records each physical arrival event of a bus at the college gate.
    Designed for real-time RFID IoT detection integration.
    """

    __tablename__ = "arrivals"
    __table_args__ = (
        CheckConstraint("status IN ('on_time', 'late')", name="ck_arrival_status"),
    )

    id           = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    bus_id       = db.Column(db.Integer,  db.ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True)
    arrival_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status       = db.Column(db.String(20), nullable=False)   # on_time | late
    created_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    bus = db.relationship("Bus", back_populates="arrivals")

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "bus_id":       self.bus_id,
            "arrival_time": self.arrival_time.isoformat(),
            "status":       self.status,
            "created_at":   self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Arrival id={self.id} bus_id={self.bus_id} status={self.status!r} time={self.arrival_time}>"
