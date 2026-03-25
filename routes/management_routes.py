from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template
from sqlalchemy import func
from zoneinfo import ZoneInfo

from models.attendance import Attendance
from models.driver import Driver
from models.student import Student
from utils.auth_helpers import login_required, role_required

management_bp = Blueprint("management", __name__, url_prefix="/management")
try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30))


@management_bp.get("/dashboard")
@login_required
@role_required("management")
def dashboard_page():
    today = datetime.now(INDIA_TZ).date()
    total_drivers = Driver.query.count()
    today_attendance = Attendance.query.filter_by(date=today, status="present").count()
    stop_counts = (
        Student.query.with_entities(Student.pickup_stop, func.count(Student.id))
        .group_by(Student.pickup_stop)
        .order_by(Student.pickup_stop.asc())
        .all()
    )

    return render_template(
        "management_dashboard.html",
        total_drivers=total_drivers,
        today_attendance=today_attendance,
        stop_counts=stop_counts,
    )
