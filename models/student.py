from datetime import datetime

from models import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    bus_number = db.Column(db.String(50), nullable=False, index=True)
    pickup_stop = db.Column(db.String(150), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    attendances = db.relationship("Attendance", back_populates="student", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "year": self.year,
            "bus_number": self.bus_number,
            "pickup_stop": self.pickup_stop,
            "user_id": self.user_id,
        }
