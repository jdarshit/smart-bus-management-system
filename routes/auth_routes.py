"""routes/auth_routes.py
Session authentication with email OTP verification.
All AUTH routes live under /auth.
"""
from datetime import datetime, timedelta

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from sqlalchemy.exc import IntegrityError

from email_service import generate_otp, send_otp_email
from models import db
from models.otp_model import OTPVerification
from models.user_model import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
ALLOWED_ROLES = {"student", "driver", "admin", "management"}
OTP_EXPIRY_MINUTES = 5


def _set_session(user) -> None:
    session.permanent = True
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role
    session["user_email"] = user.email


def _issue_otp(email: str) -> OTPVerification:
    active_otps = OTPVerification.query.filter_by(email=email, used=False).all()
    for otp_record in active_otps:
        otp_record.used = True

    otp_record = OTPVerification(
        email=email,
        otp_code=generate_otp(),
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        used=False,
    )
    db.session.add(otp_record)
    db.session.flush()
    return otp_record


@auth_bp.route("/dashboard-redirect")
def redirect_dashboard():
    role = session.get("user_role")
    destinations = {
        "admin": "admin.dashboard_page",
        "management": "management.dashboard_page",
        "driver": "driver.dashboard_page",
        "student": "student.dashboard_page",
    }
    endpoint = destinations.get(role)
    if endpoint:
        return redirect(url_for(endpoint))
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("auth.redirect_dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if not user.verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("auth.verify_otp_page", email=email))

        _set_session(user)
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("auth.redirect_dashboard"))

    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup_page():
    if session.get("user_id"):
        return redirect(url_for("auth.redirect_dashboard"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "").strip().lower()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if role not in ALLOWED_ROLES:
            errors.append(f"Role must be one of: {', '.join(sorted(ALLOWED_ROLES))}.")

        if errors:
            for error_message in errors:
                flash(error_message, "danger")
            return render_template("signup.html", roles=sorted(ALLOWED_ROLES))

        user = User.query.filter_by(email=email).first()
        if user and user.verified:
            flash("An account with that email already exists. Please log in.", "danger")
            return render_template("signup.html", roles=sorted(ALLOWED_ROLES))

        try:
            if not user:
                user = User(name=name, email=email, role=role, verified=False)
                user.set_password(password)
                db.session.add(user)
            else:
                user.name = name
                user.role = role
                user.verified = False
                user.set_password(password)

            otp_record = _issue_otp(email)
            db.session.commit()

            email_sent, send_message = send_otp_email(email=email, otp=otp_record.otp_code)

            if email_sent:
                flash("Signup successful. OTP sent to your email.", "success")
            else:
                flash(f"Signup successful, but OTP email failed: {send_message}", "warning")

            return redirect(url_for("auth.verify_otp_page", email=email))
        except IntegrityError:
            db.session.rollback()
            flash("An account with that email already exists.", "danger")
            return render_template("signup.html", roles=sorted(ALLOWED_ROLES))

    return render_template("signup.html", roles=sorted(ALLOWED_ROLES))


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp_page():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        otp_code = (request.form.get("otp_code") or "").strip()

        if not email or not otp_code:
            flash("Email and OTP are required.", "danger")
            return render_template("otp_verification.html", prefill_email=email)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No user found for this email.", "danger")
            return render_template("otp_verification.html", prefill_email=email)

        if user.verified:
            flash("Email already verified. Please log in.", "info")
            return redirect(url_for("auth.login_page"))

        otp_record = (
            OTPVerification.query
            .filter_by(email=email, otp_code=otp_code, used=False)
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not otp_record:
            flash("Invalid OTP. Please try again.", "danger")
            return render_template("otp_verification.html", prefill_email=email)

        if otp_record.is_expired():
            otp_record.used = True
            db.session.commit()
            flash("OTP expired. Please request a new OTP.", "warning")
            return render_template("otp_verification.html", prefill_email=email)

        user.verified = True
        otp_record.used = True

        other_otps = OTPVerification.query.filter_by(email=email, used=False).all()
        for item in other_otps:
            item.used = True

        db.session.commit()
        flash("Email verified successfully. Please log in.", "success")
        return redirect(url_for("auth.login_page"))

    prefill_email = (request.args.get("email") or "").strip().lower()
    return render_template("otp_verification.html", prefill_email=prefill_email)


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = (request.form.get("email") or "").strip().lower()
    if not email:
        flash("Email is required to resend OTP.", "danger")
        return redirect(url_for("auth.verify_otp_page"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No account found for that email.", "danger")
        return redirect(url_for("auth.verify_otp_page", email=email))

    if user.verified:
        flash("Email already verified. Please log in.", "info")
        return redirect(url_for("auth.login_page"))

    otp_record = _issue_otp(email)
    db.session.commit()

    email_sent, send_message = send_otp_email(email=email, otp=otp_record.otp_code)
    if email_sent:
        flash("A new OTP has been sent.", "success")
    else:
        flash(f"Could not send OTP email: {send_message}", "danger")

    return redirect(url_for("auth.verify_otp_page", email=email))


@auth_bp.route("/logout")
def logout():
    name = session.get("user_name", "User")
    session.clear()
    flash(f"Goodbye, {name}! You have been logged out.", "info")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/api/signup", methods=["POST"])
def signup_api():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "").strip().lower()

    if not name or not email or len(password) < 6 or role not in ALLOWED_ROLES:
        return jsonify({"success": False, "message": "Invalid input."}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.verified:
        return jsonify({"success": False, "message": "Email already exists."}), 409

    try:
        if not user:
            user = User(name=name, email=email, role=role, verified=False)
            user.set_password(password)
            db.session.add(user)
        else:
            user.name = name
            user.role = role
            user.verified = False
            user.set_password(password)

        otp_record = _issue_otp(email)
        db.session.commit()

        mail_sent, send_message = send_otp_email(email=email, otp=otp_record.otp_code)

        return jsonify({
            "success": True,
            "user": user.to_dict(),
            "mail_sent": mail_sent,
            "mail_message": send_message,
            "message": "Signup successful. Verify OTP to activate account.",
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "Email already exists."}), 409


@auth_bp.route("/api/login", methods=["POST"])
def login_api():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    if not user.verified:
        return jsonify({"success": False, "message": "Please verify your email before logging in."}), 403

    return jsonify({"success": True, "user": user.to_dict()}), 200
