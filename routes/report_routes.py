from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template
from sqlalchemy import func
from zoneinfo import ZoneInfo

from models.attendance import Attendance
from models.bus_arrival_log import BusArrivalLog
from models.student import Student
from utils.auth_helpers import login_required, role_required

report_bp = Blueprint("reports", __name__, url_prefix="/reports")
try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30))


@report_bp.get("/")
@login_required
@role_required("admin", "management")
def reports_page():
    today = datetime.now(INDIA_TZ).date()

    daily_arrivals = (
        BusArrivalLog.query
        .order_by(BusArrivalLog.arrival_time.desc())
        .limit(100)
        .all()
    )

    late_buses = [row for row in daily_arrivals if row.status == "Late"]

    attendance_records = (
        Attendance.query
        .order_by(Attendance.date.desc(), Attendance.time.desc())
        .limit(300)
        .all()
    )

    stop_wise_report = (
        Student.query.with_entities(Student.pickup_stop, func.count(Student.id))
        .group_by(Student.pickup_stop)
        .order_by(Student.pickup_stop.asc())
        .all()
    )

    return render_template(
        "reports.html",
        today=today,
        daily_arrivals=daily_arrivals,
        late_buses=late_buses,
        attendance_records=attendance_records,
        stop_wise_report=stop_wise_report,
    )
