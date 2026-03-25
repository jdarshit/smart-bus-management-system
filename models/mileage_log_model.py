from datetime import date

from models import db


class MileageLog(db.Model):
    """
    Odometer / mileage submission by a driver with photo evidence.
    An admin or management user approves the entry.
    """

    __tablename__ = "mileage_logs"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_id  = db.Column(db.Integer, db.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    bus_id     = db.Column(db.Integer, db.ForeignKey("buses.id",   ondelete="SET NULL"), nullable=True, index=True)
    image_path = db.Column(db.String(255), nullable=False)           # relative path inside /static/uploads/
    date       = db.Column(db.Date, nullable=False, default=date.today, index=True)
    approved   = db.Column(db.Boolean, nullable=False, default=False) # False = pending review

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    driver = db.relationship("Driver")
    bus    = db.relationship("Bus")

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "driver_id":  self.driver_id,
            "bus_id":     self.bus_id,
            "image_path": self.image_path,
            "date":       self.date.isoformat(),
            "approved":   self.approved,
        }

    def __repr__(self) -> str:
        return f"<MileageLog id={self.id} driver_id={self.driver_id} bus_id={self.bus_id} approved={self.approved}>"
