"""routes/admin_rfid_routes.py

Admin panel for RFID card management:
  GET  /admin/rfid            – assignment table
  POST /admin/assign_rfid     – assign/update a student's RFID UID
  POST /admin/remove_rfid     – clear a student's RFID UID
  GET  /admin/rfid_logs       – live scan log table
"""
import datetime

from flask import Blueprint, jsonify, render_template, request, session

from models.rfid_log import RFIDLog
from models.student_model import Student
from models.bus_model import Bus
from services.rfid_assignment_service import (
    AssignmentError,
    assign_rfid_to_student,
    remove_rfid_from_student,
)
from utils.auth_helpers import login_required, role_required

admin_rfid_bp = Blueprint("admin_rfid", __name__, url_prefix="/admin")


# ------------------------------------------------------------------ #
#  GET /admin/rfid  – RFID assignment dashboard                        #
# ------------------------------------------------------------------ #

@admin_rfid_bp.get("/rfid")
@login_required
@role_required("admin")
def rfid_assignment_page():
    students = (
        Student.query
        .outerjoin(Bus, Student.bus_id == Bus.id)
        .order_by(Student.student_name)
        .all()
    )
    return render_template("admin/rfid_assignment.html", students=students)


# ------------------------------------------------------------------ #
#  POST /admin/assign_rfid  – JSON API used by browser + ESP32 scan    #
# ------------------------------------------------------------------ #

@admin_rfid_bp.post("/assign_rfid")
@login_required
@role_required("admin")
def assign_rfid():
    """Assign or update a student's RFID UID.

    Payload  (JSON):
      { "student_id": 12, "rfid_uid": "72 3C 14 5C" }

    Returns 200 on success, 400/404/500 on error.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    student_id = payload.get("student_id")
    rfid_uid   = payload.get("rfid_uid", "").strip()

    if not student_id:
        return jsonify({"status": "error", "message": "student_id is required"}), 400
    if not rfid_uid:
        return jsonify({"status": "error", "message": "rfid_uid is required"}), 400

    try:
        student = assign_rfid_to_student(int(student_id), rfid_uid)
    except AssignmentError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({
        "status":      "success",
        "message":     f"RFID {student.rfid_uid} assigned to {student.student_name}",
        "student_id":  student.id,
        "student_name": student.student_name,
        "rfid_uid":    student.rfid_uid,
    }), 200


# ------------------------------------------------------------------ #
#  POST /admin/remove_rfid  – clear a student's RFID card              #
# ------------------------------------------------------------------ #

@admin_rfid_bp.post("/remove_rfid")
@login_required
@role_required("admin")
def remove_rfid():
    payload = request.get_json(silent=True)
    if not payload or not payload.get("student_id"):
        return jsonify({"status": "error", "message": "student_id is required"}), 400

    try:
        student = remove_rfid_from_student(int(payload["student_id"]))
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({
        "status":      "success",
        "message":     f"RFID removed from {student.student_name}",
        "student_id":  student.id,
    }), 200


# ------------------------------------------------------------------ #
#  GET /admin/rfid_logs  – live scan history                           #
# ------------------------------------------------------------------ #

@admin_rfid_bp.get("/rfid_logs")
@login_required
@role_required("admin")
def rfid_logs_page():
    page     = request.args.get("page", 1, type=int)
    per_page = 50

    logs_pag = (
        RFIDLog.query
        .order_by(RFIDLog.scan_time.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "admin/rfid_logs.html",
        logs=logs_pag.items,
        pagination=logs_pag,
    )


# ------------------------------------------------------------------ #
#  GET /admin/rfid_logs/data  – JSON feed for auto-refresh             #
# ------------------------------------------------------------------ #

@admin_rfid_bp.get("/rfid_logs/data")
@login_required
@role_required("admin")
def rfid_logs_data():
    """Return the 100 most recent scan logs as JSON (for polling)."""
    logs = RFIDLog.query.order_by(RFIDLog.scan_time.desc()).limit(100).all()
    return jsonify([
        {
            "id":           log.id,
            "uid":          log.uid,
            "student_name": log.student.student_name if log.student else "Unknown",
            "bus_number":   log.bus.bus_number if log.bus else "Unknown",
            "scan_time":    log.scan_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for log in logs
    ])
