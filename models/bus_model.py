from datetime import datetime

from models import db


class Bus(db.Model):
    """Physical bus - only tracks bus number, plate, driver, route, rfid."""

    __tablename__ = "buses"
    __table_args__ = (
        db.Index("idx_bus_rfid", "rfid_uid"),
    )

    id            = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    bus_number    = db.Column(db.String(50),  nullable=False, unique=True)
    license_plate = db.Column(db.String(30),  nullable=True,  unique=True)
    driver_name   = db.Column(db.String(100), nullable=True)
    route_name    = db.Column(db.String(150), nullable=True)
    rfid_uid      = db.Column(db.String(100), nullable=True,  unique=True)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    arrival_logs = db.relationship(
        "BusArrivalLog",
        back_populates="bus",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    arrivals = db.relationship(
        "Arrival",
        back_populates="bus",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "bus_number":   self.bus_number,
            "license_plate": self.license_plate,
            "driver_name":  self.driver_name,
            "route_name":   self.route_name,
            "rfid_uid":     self.rfid_uid,
            "has_rfid":     bool(self.rfid_uid),
            "created_at":   self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Bus id={self.id} number={self.bus_number!r} route={self.route_name!r}>"
