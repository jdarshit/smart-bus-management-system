from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template
from zoneinfo import ZoneInfo

from models.attendance import Attendance
from models.bus_arrival_log import BusArrivalLog
from models.bus_model import Bus
from models.student import Student
from models.user_model import User
from utils.auth_helpers import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30))


@admin_bp.get("/")
@admin_bp.get("/dashboard")
@login_required
@role_required("admin")
def dashboard_page():
    today = datetime.now(INDIA_TZ).date()
    total_buses = Bus.query.count()
    total_students = Student.query.count()
    today_attendance = Attendance.query.filter_by(date=today, status="present").count()

    late_buses = (
        BusArrivalLog.query
        .filter(BusArrivalLog.status == "Late")
        .filter(BusArrivalLog.arrival_time >= datetime.combine(today, datetime.min.time()))
        .count()
    )

    return render_template(
        "admin_dashboard.html",
        total_buses=total_buses,
        total_students=total_students,
        today_attendance=today_attendance,
        late_buses=late_buses,
    )


@admin_bp.get("/users")
@login_required
@role_required("admin")
def users_page():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.get("/buses")
@login_required
@role_required("admin", "management")
def buses_page():
    buses = Bus.query.order_by(Bus.bus_number.asc()).all()
    return render_template("buses/index.html", buses=buses)


@admin_bp.get("/rfid_logs")
@login_required
@role_required("admin")
def rfid_logs_page():
    logs = BusArrivalLog.query.order_by(BusArrivalLog.arrival_time.desc()).limit(300).all()
    return render_template("admin/rfid_logs.html", logs=logs)
