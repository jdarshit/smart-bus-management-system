from datetime import datetime

from models import db


class Student(db.Model):
    """Student profile linked to a User account."""

    __tablename__ = "students"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    student_name  = db.Column(db.String(100), nullable=False)
    department    = db.Column(db.String(100), nullable=False)
    year          = db.Column(db.Integer, nullable=True)          # academic year: 1-4
    bus_id        = db.Column(db.Integer, db.ForeignKey("buses.id", ondelete="SET NULL"), nullable=True, index=True)
    rfid_uid      = db.Column(db.String(100), nullable=True, unique=True, index=True)
    pickup_point  = db.Column(db.String(150), nullable=True)      # e.g. "Gate 1 - Main Entrance"
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    user = db.relationship("User", back_populates="students")
    bus  = db.relationship("Bus",  back_populates="students")
    attendance_records = db.relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "user_id":      self.user_id,
            "student_name": self.student_name,
            "department":   self.department,
            "year":         self.year,
            "bus_id":       self.bus_id,
            "rfid_uid":     self.rfid_uid,
            "pickup_point": self.pickup_point,
            "created_at":   self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Student id={self.id} name={self.student_name!r} dept={self.department!r}>"
