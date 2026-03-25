from datetime import datetime

from models import db


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    license_number = db.Column(db.String(80), nullable=False, unique=True, index=True)
    bus_number = db.Column(db.String(50), nullable=False, index=True)
    photo = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "driver_name": self.driver_name,
            "phone": self.phone,
            "license_number": self.license_number,
            "bus_number": self.bus_number,
            "photo": self.photo,
            "user_id": self.user_id,
        }
