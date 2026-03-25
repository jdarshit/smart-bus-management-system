import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func
from werkzeug.utils import secure_filename

from models import db
from models.attendance import Attendance
from models.driver import Driver
from models.student import Student
from models.user_model import User
from utils.auth_helpers import login_required, role_required


driver_bp = Blueprint("driver", __name__, url_prefix="/drivers")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _is_allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@driver_bp.get("/dashboard")
@login_required
@role_required("driver")
def dashboard_page():
    driver = Driver.query.filter_by(user_id=session.get("user_id")).first()
    if not driver:
        return render_template("driver_dashboard.html", driver=None, stop_counts=[], attendance_logs=[])

    stop_counts = (
        Student.query.with_entities(Student.pickup_stop, func.count(Student.id))
        .filter(Student.bus_number == driver.bus_number)
        .group_by(Student.pickup_stop)
        .order_by(Student.pickup_stop.asc())
        .all()
    )

    attendance_logs = (
        Attendance.query
        .filter(Attendance.bus_number == driver.bus_number)
        .order_by(Attendance.date.desc(), Attendance.time.desc())
        .limit(200)
        .all()
    )

    return render_template(
        "driver_dashboard.html",
        driver=driver,
        stop_counts=stop_counts,
        attendance_logs=attendance_logs,
    )


@driver_bp.get("/")
@login_required
@role_required("admin", "management")
def list_page():
    drivers = Driver.query.order_by(Driver.driver_name.asc()).all()
    driver_users = User.query.filter_by(role="driver").order_by(User.name.asc()).all()
    return render_template("drivers/index.html", drivers=drivers, driver_users=driver_users)


@driver_bp.post("/add")
@login_required
@role_required("admin")
def add_driver():
    driver_name = (request.form.get("driver_name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    license_number = (request.form.get("license_number") or "").strip()
    bus_number = (request.form.get("bus_number") or "").strip()

    if not driver_name or not license_number or not bus_number:
        flash("Driver name, license number and bus number are required.", "danger")
        return redirect(url_for("driver.list_page"))

    photo_rel = None
    file = request.files.get("photo")
    if file and file.filename:
        if not _is_allowed(file.filename):
            flash("Invalid photo format. Use png/jpg/jpeg/webp.", "danger")
            return redirect(url_for("driver.list_page"))

        filename = secure_filename(file.filename)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        filename = f"{stamp}_{filename}"
        abs_dir = os.path.join(current_app.root_path, "static", "uploads", "drivers")
        os.makedirs(abs_dir, exist_ok=True)
        file.save(os.path.join(abs_dir, filename))
        photo_rel = f"uploads/drivers/{filename}"

    db.session.add(
        Driver(
            driver_name=driver_name,
            phone=phone or None,
            license_number=license_number,
            bus_number=bus_number,
            photo=photo_rel,
        )
    )
    db.session.commit()
    flash("Driver added.", "success")
    return redirect(url_for("driver.list_page"))


@driver_bp.post("/<int:driver_id>/edit")
@login_required
@role_required("admin")
def edit_driver(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    driver.driver_name = (request.form.get("driver_name") or driver.driver_name).strip()
    driver.phone = (request.form.get("phone") or driver.phone or "").strip() or None
    driver.license_number = (request.form.get("license_number") or driver.license_number).strip()
    driver.bus_number = (request.form.get("bus_number") or driver.bus_number).strip()

    file = request.files.get("photo")
    if file and file.filename:
        if _is_allowed(file.filename):
            filename = secure_filename(file.filename)
            stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            filename = f"{stamp}_{filename}"
            abs_dir = os.path.join(current_app.root_path, "static", "uploads", "drivers")
            os.makedirs(abs_dir, exist_ok=True)
            file.save(os.path.join(abs_dir, filename))
            driver.photo = f"uploads/drivers/{filename}"

    db.session.commit()
    flash("Driver updated.", "success")
    return redirect(url_for("driver.list_page"))


@driver_bp.post("/<int:driver_id>/delete")
@login_required
@role_required("admin")
def delete_driver(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    flash("Driver deleted.", "warning")
    return redirect(url_for("driver.list_page"))


@driver_bp.post("/<int:driver_id>/link-user")
@login_required
@role_required("admin")
def link_user(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    user_id = (request.form.get("user_id") or "").strip()

    if not user_id:
        driver.user_id = None
        db.session.commit()
        flash("Driver account unlinked.", "info")
        return redirect(url_for("driver.list_page"))

    user = User.query.filter_by(id=int(user_id), role="driver").first()
    if not user:
        flash("Selected user is invalid.", "danger")
        return redirect(url_for("driver.list_page"))

    Driver.query.filter(Driver.user_id == user.id, Driver.id != driver.id).update({"user_id": None})
    driver.user_id = user.id
    db.session.commit()
    flash("Driver account linked.", "success")
    return redirect(url_for("driver.list_page"))
