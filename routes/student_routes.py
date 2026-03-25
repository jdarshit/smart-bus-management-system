from datetime import datetime, time, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from zoneinfo import ZoneInfo

from models import db
from models.attendance import Attendance
from models.bus_model import Bus
from models.student import Student
from models.user_model import User
from utils.auth_helpers import login_required, role_required

student_bp = Blueprint("student", __name__, url_prefix="/students")

try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30))
STOP_OPTIONS = ["Vijay Nagar", "Palasia", "Bapat Square", "Rajendra Nagar"]


def _now_india():
    return datetime.now(INDIA_TZ).replace(tzinfo=None)


def _attendance_allowed(now: datetime) -> bool:
    return time(7, 0) <= now.time() <= time(11, 0)


@student_bp.get("/dashboard")
@login_required
@role_required("student")
def dashboard_page():
    student = Student.query.filter_by(user_id=session.get("user_id")).first()
    today = _now_india().date()
    today_attendance = None
    if student:
        today_attendance = Attendance.query.filter_by(student_id=student.id, date=today).first()
    return render_template(
        "student_dashboard.html",
        student=student,
        today_attendance=today_attendance,
        stop_options=STOP_OPTIONS,
        attendance_allowed=_attendance_allowed(_now_india()),
    )


@student_bp.post("/mark-attendance")
@login_required
@role_required("student")
def mark_attendance():
    student = Student.query.filter_by(user_id=session.get("user_id")).first()
    if not student:
        flash("No student profile linked to your account.", "danger")
        return redirect(url_for("student.dashboard_page"))

    pickup_stop = (request.form.get("pickup_stop") or "").strip()
    if pickup_stop not in STOP_OPTIONS:
        flash("Please select a valid pickup stop.", "danger")
        return redirect(url_for("student.dashboard_page"))

    now = _now_india()
    if not _attendance_allowed(now):
        flash("Attendance is allowed only between 07:00 and 11:00.", "warning")
        return redirect(url_for("student.dashboard_page"))

    student.pickup_stop = pickup_stop
    today = now.date()
    record = Attendance.query.filter_by(student_id=student.id, date=today).first()
    if record:
        record.pickup_stop = pickup_stop
        record.time = now.time().replace(microsecond=0)
        record.status = "present"
        flash("Attendance updated for today.", "success")
    else:
        db.session.add(
            Attendance(
                student_id=student.id,
                student_name=student.name,
                bus_number=student.bus_number,
                pickup_stop=pickup_stop,
                date=today,
                time=now.time().replace(microsecond=0),
                status="present",
            )
        )
        flash("Attendance marked successfully.", "success")

    db.session.commit()
    return redirect(url_for("student.dashboard_page"))


@student_bp.get("/")
@login_required
@role_required("admin", "management")
def list_page():
    students = Student.query.order_by(Student.name.asc()).all()
    buses = Bus.query.order_by(Bus.bus_number.asc()).all()
    student_users = User.query.filter_by(role="student").order_by(User.name.asc()).all()
    return render_template(
        "students/index.html",
        students=students,
        buses=buses,
        stop_options=STOP_OPTIONS,
        student_users=student_users,
    )


@student_bp.post("/add")
@login_required
@role_required("admin")
def add_student():
    name = (request.form.get("name") or "").strip()
    department = (request.form.get("department") or "").strip()
    year = request.form.get("year")
    bus_number = (request.form.get("bus_number") or "").strip()
    pickup_stop = (request.form.get("pickup_stop") or "").strip()

    if not name or not department or not year or not bus_number or pickup_stop not in STOP_OPTIONS:
        flash("All student fields are required.", "danger")
        return redirect(url_for("student.list_page"))

    db.session.add(
        Student(
            name=name,
            department=department,
            year=int(year),
            bus_number=bus_number,
            pickup_stop=pickup_stop,
        )
    )
    db.session.commit()
    flash("Student added.", "success")
    return redirect(url_for("student.list_page"))


@student_bp.post("/<int:student_id>/edit")
@login_required
@role_required("admin")
def edit_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    student.name = (request.form.get("name") or student.name).strip()
    student.department = (request.form.get("department") or student.department).strip()
    year = (request.form.get("year") or str(student.year)).strip()
    student.year = int(year)
    student.bus_number = (request.form.get("bus_number") or student.bus_number).strip()
    pickup_stop = (request.form.get("pickup_stop") or student.pickup_stop).strip()
    if pickup_stop in STOP_OPTIONS:
        student.pickup_stop = pickup_stop
    db.session.commit()
    flash("Student updated.", "success")
    return redirect(url_for("student.list_page"))


@student_bp.post("/<int:student_id>/delete")
@login_required
@role_required("admin")
def delete_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted.", "warning")
    return redirect(url_for("student.list_page"))


@student_bp.post("/<int:student_id>/link-user")
@login_required
@role_required("admin")
def link_user(student_id: int):
    student = Student.query.get_or_404(student_id)
    user_id = (request.form.get("user_id") or "").strip()

    if not user_id:
        student.user_id = None
        db.session.commit()
        flash("Student account unlinked.", "info")
        return redirect(url_for("student.list_page"))

    user = User.query.filter_by(id=int(user_id), role="student").first()
    if not user:
        flash("Selected user is invalid.", "danger")
        return redirect(url_for("student.list_page"))

    Student.query.filter(Student.user_id == user.id, Student.id != student.id).update({"user_id": None})
    student.user_id = user.id
    db.session.commit()
    flash("Student account linked.", "success")
    return redirect(url_for("student.list_page"))
