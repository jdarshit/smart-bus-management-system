from datetime import date, datetime, time

from models import db


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    student_name = db.Column(db.String(120), nullable=False)
    bus_number = db.Column(db.String(50), nullable=False, index=True)
    pickup_stop = db.Column(db.String(150), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    time = db.Column(db.Time, nullable=False, default=lambda: datetime.utcnow().time())
    status = db.Column(db.String(20), nullable=False, default="present", index=True)

    student = db.relationship("Student", back_populates="attendances", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "bus_number": self.bus_number,
            "pickup_stop": self.pickup_stop,
            "date": self.date.isoformat(),
            "time": self.time.strftime("%H:%M:%S") if isinstance(self.time, time) else str(self.time),
            "status": self.status,
        }
