from datetime import datetime

from models import db


class Driver(db.Model):
    """
    Driver profile linked to a User account.

    NOTE: bus_id here is a display-only integer (no FK) to avoid a
    circular FK cycle with the buses table (buses.driver_id → drivers.id
    is the authoritative link). It is kept in sync at the application
    layer whenever a bus assignment changes.
    """

    __tablename__ = "drivers"

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    driver_name    = db.Column(db.String(100), nullable=False)
    phone          = db.Column(db.String(20),  nullable=True)
    license_number = db.Column(db.String(50),  nullable=True, unique=True)
    bus_id         = db.Column(db.Integer, nullable=True)    # denormalised cache — NOT a FK
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    user         = db.relationship("User", back_populates="drivers")
    buses        = db.relationship("Bus",  back_populates="driver")
    mileage_logs = db.relationship(
        "MileageLog", back_populates="driver", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "driver_name":    self.driver_name,
            "phone":          self.phone,
            "license_number": self.license_number,
            "bus_id":         self.bus_id,
            "created_at":     self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Driver id={self.id} name={self.driver_name!r} license={self.license_number!r}>"
