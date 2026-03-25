from datetime import date

from sqlalchemy import CheckConstraint

from models import db


class Attendance(db.Model):
    """Daily attendance record for a student on a specific date."""

    __tablename__ = "attendance"
    __table_args__ = (
        CheckConstraint("status IN ('present', 'absent')", name="ck_attendance_status"),
        db.UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
    )

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date       = db.Column(db.Date,    nullable=False, default=date.today, index=True)
    status     = db.Column(db.String(20), nullable=False)   # present | absent

    # ---------------------------------------------------------------- #
    # Relationships                                                      #
    # ---------------------------------------------------------------- #
    student = db.relationship("Student", back_populates="attendance_records")

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "student_id": self.student_id,
            "date":       self.date.isoformat(),
            "status":     self.status,
        }

    def __repr__(self) -> str:
        return f"<Attendance id={self.id} student_id={self.student_id} date={self.date} status={self.status!r}>"
