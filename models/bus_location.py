"""models/bus_location.py

Records every GPS position fix received from a bus-mounted ESP32+NEO-6M.
Keeps full history — use the service layer to get the latest fix per bus.
"""
from datetime import datetime

from extensions import db


class BusLocation(db.Model):
    """GPS position record for a bus at a point in time."""

    __tablename__ = "bus_locations"

    id        = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    bus_id    = db.Column(
        db.Integer,
        db.ForeignKey("buses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    latitude  = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    bus = db.relationship("Bus", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "bus_id":      self.bus_id,
            "bus_number":  self.bus.bus_number if self.bus else None,
            "latitude":    self.latitude,
            "longitude":   self.longitude,
            "last_update": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "timestamp":   self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"<BusLocation id={self.id} bus_id={self.bus_id} "
            f"lat={self.latitude} lng={self.longitude} ts={self.timestamp}>"
        )
