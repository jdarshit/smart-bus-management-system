from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template
from sqlalchemy import func
from zoneinfo import ZoneInfo

from models.attendance import Attendance
from models.student import Student
from utils.auth_helpers import login_required, role_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")
try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30))


@attendance_bp.get("/")
@login_required
@role_required("admin", "management", "driver")
def attendance_page():
    today = datetime.now(INDIA_TZ).date()

    records = (
        Attendance.query
        .order_by(Attendance.date.desc(), Attendance.time.desc())
        .limit(200)
        .all()
    )

    stop_counts = (
        Student.query.with_entities(Student.pickup_stop, func.count(Student.id))
        .group_by(Student.pickup_stop)
        .all()
    )

    today_present = Attendance.query.filter_by(date=today, status="present").count()

    return render_template(
        "attendance/index.html",
        records=records,
        stop_counts=stop_counts,
        today=today,
        today_present=today_present,
    )
