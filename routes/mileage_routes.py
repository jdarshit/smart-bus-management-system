"""routes/mileage_routes.py    Mileage log upload and management."""
import os
import datetime
from werkzeug.utils import secure_filename

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, session, url_for)

from models import db
from models.driver import Driver
from models.mileage_log_model import MileageLog
from utils.auth_helpers import login_required, role_required

mileage_bp = Blueprint("mileage", __name__, url_prefix="/mileage")


def _allowed_file(filename: str) -> bool:
    allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "pdf"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


#  Mileage Page 

@mileage_bp.route("/", methods=["GET"])
@login_required
def mileage_page():
    role    = session.get("user_role")
    user_id = session.get("user_id")

    if role == "driver":
        driver = Driver.query.filter_by(user_id=user_id).first()
        logs   = []
        if driver:
            logs = MileageLog.query.filter_by(driver_id=driver.id).order_by(MileageLog.date.desc()).all()
        return render_template("mileage/index.html", logs=logs, role=role, driver=driver)

    # Admin / management  see all logs
    logs = (
        MileageLog.query
        .join(Driver, MileageLog.driver_id == Driver.id)
        .order_by(MileageLog.date.desc())
        .all()
    )
    pending_count = MileageLog.query.filter_by(approved=False).count()
    return render_template("mileage/index.html", logs=logs, role=role, pending_count=pending_count)


#  Upload Mileage Log 

@mileage_bp.route("/upload", methods=["POST"])
@login_required
@role_required("driver")
def upload_mileage():
    user_id = session.get("user_id")
    driver  = Driver.query.filter_by(user_id=user_id).first()
    if not driver:
        flash("No driver profile linked to your account.", "danger")
        return redirect(url_for("mileage.mileage_page"))

    file = request.files.get("odometer_image")
    bus_id = request.form.get("bus_id")

    if not file or file.filename == "":
        flash("Please select an image to upload.", "danger")
        return redirect(url_for("mileage.mileage_page"))

    if not _allowed_file(file.filename):
        flash("File type not allowed. Use PNG, JPG, GIF, or PDF.", "danger")
        return redirect(url_for("mileage.mileage_page"))

    filename   = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.root_path, current_app.config.get("UPLOAD_FOLDER", "uploads/mileage"))
    os.makedirs(upload_dir, exist_ok=True)

    # Make filename unique with timestamp
    ts       = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{filename}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    image_path = f"{current_app.config.get('UPLOAD_FOLDER', 'uploads/mileage').replace('\\', '/')}/{filename}"
    log = MileageLog(
        driver_id  = driver.id,
        bus_id     = int(bus_id) if bus_id else None,
        image_path = image_path,
        date       = datetime.date.today(),
        approved   = False,
    )
    db.session.add(log)
    db.session.commit()
    flash("Mileage log uploaded and pending approval.", "success")
    return redirect(url_for("mileage.mileage_page"))


@mileage_bp.route("/files/<path:filepath>", methods=["GET"])
@login_required
def view_uploaded_file(filepath):
    uploads_root = os.path.join(current_app.root_path, current_app.config.get("UPLOAD_FOLDER", "uploads/mileage"))
    safe_path = filepath.replace("\\", "/").lstrip("/")
    if safe_path.startswith("uploads/"):
        safe_path = safe_path[len("uploads/"):]
    if not safe_path.startswith("mileage/"):
        return jsonify({"success": False, "message": "Invalid file path."}), 400
    return send_from_directory(os.path.dirname(uploads_root), safe_path)


#  Approve Mileage Log 

@mileage_bp.route("/<int:log_id>/approve", methods=["POST"])
@login_required
@role_required("admin", "management")
def approve_mileage(log_id):
    log = MileageLog.query.get_or_404(log_id)
    log.approved = not log.approved
    db.session.commit()
    status = "approved" if log.approved else "unapproved"
    flash(f"Mileage log #{log_id} {status}.", "success")
    return redirect(url_for("mileage.mileage_page"))


#  Delete Mileage Log 

@mileage_bp.route("/<int:log_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_mileage(log_id):
    log = MileageLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash("Mileage log deleted.", "warning")
    return redirect(url_for("mileage.mileage_page"))


#  JSON API 

@mileage_bp.route("/api/pending", methods=["GET"])
@login_required
@role_required("admin", "management")
def api_pending():
    logs = MileageLog.query.filter_by(approved=False).all()
    return jsonify([l.to_dict() for l in logs])
