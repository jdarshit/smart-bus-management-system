from datetime import datetime

from models import db


class BusArrivalLog(db.Model):
    """Immutable gate-arrival record snapshot with two-shift status."""

    __tablename__ = "bus_arrival_logs"
    __table_args__ = (
        db.Index("idx_arrival_time", "arrival_time"),
    )

    id            = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    bus_id        = db.Column(db.Integer,    db.ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True)
    bus_number    = db.Column(db.String(50),  nullable=False, index=True)
    license_plate = db.Column(db.String(30),  nullable=True)
    driver_name   = db.Column(db.String(100), nullable=True)
    route_name    = db.Column(db.String(150), nullable=True)
    rfid_uid      = db.Column(db.String(100), nullable=False, index=True)
    arrival_time  = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow, index=True)
    status        = db.Column(db.String(20),  nullable=False, default="On Time")
    shift         = db.Column(db.String(20),  nullable=False, default="shift1")

    bus = db.relationship("Bus", back_populates="arrival_logs", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "bus_id":       self.bus_id,
            "bus_number":   self.bus_number,
            "license_plate": self.license_plate,
            "driver_name":  self.driver_name,
            "route_name":   self.route_name,
            "rfid_uid":     self.rfid_uid,
            "arrival_time": self.arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status":       self.status,
            "shift":        self.shift,
        }
