"""app.py - Smart Bus Management System - Application Entry Point"""

import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, jsonify, session, url_for
try:
    from flask_cors import CORS
except ModuleNotFoundError:  # pragma: no cover
    CORS = None

from config import get_config_class
from extensions import db, mail, migrate

load_dotenv(override=True)


def create_app(config_object=None):
    """Application factory."""
    if config_object is None:
        config_object = get_config_class()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)
    app.config.setdefault("SEND_FILE_MAX_AGE_DEFAULT", 86400)

    config_object.validate()

    app.secret_key = app.config["SECRET_KEY"]
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        seconds=app.config.get("PERMANENT_SESSION_LIFETIME_SECONDS", 7200)
    )

    if CORS is not None:
        CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Ensure upload directory exists
    upload_dir = os.path.join(app.root_path, app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_dir, exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    with app.app_context():
        import models  # register ORM models
        try:
            from services.bus_arrival_service import ensure_predefined_buses
            ensure_predefined_buses()
        except Exception as exc:  # pragma: no cover
            print(f"[startup] Bus seed skipped: {exc}")

    # Blueprints
    from routes.auth_routes import auth_bp
    from routes.attendance_routes import attendance_bp
    from routes.admin_routes import admin_bp
    from routes.admin_bus_map_routes import admin_bus_map_bp
    from routes.admin_bus_routes import admin_bus_bp
    from routes.bus_routes import bus_bp
    from routes.bus_status_routes import bus_status_bp
    from routes.dashboard_tv_routes import dashboard_tv_bp
    from routes.driver_routes import driver_bp
    from routes.gps_routes import gps_bp
    from routes.iot_routes import iot_bp
    from routes.management_routes import management_bp
    from routes.mileage_routes import mileage_bp
    from routes.report_routes import report_bp
    from routes.rfid_api import rfid_bp
    from routes.student_routes import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_bus_map_bp)
    app.register_blueprint(admin_bus_bp)
    app.register_blueprint(bus_bp)
    app.register_blueprint(bus_status_bp)
    app.register_blueprint(dashboard_tv_bp)
    app.register_blueprint(gps_bp)
    app.register_blueprint(iot_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(mileage_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(rfid_bp)

    # Public page routes
    @app.route("/")
    def home():
        if session.get("user_id"):
            return redirect(url_for("auth.redirect_dashboard"))
        return render_template("index.html")

    # Login / Signup redirects
    @app.route("/login")
    def login_redirect():
        return redirect(url_for("auth.login_page"))

    @app.route("/signup")
    def signup_redirect():
        return redirect(url_for("auth.signup_page"))

    @app.route("/logout")
    def logout_redirect():
        return redirect(url_for("auth.logout"))

    # Dashboard redirect based on role
    @app.route("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect(url_for("auth.login_page"))
        return redirect(url_for("auth.redirect_dashboard"))

    @app.route("/test-email")
    def test_email():
        from email_service import send_otp_email
        recipient = request.args.get("to", app.config.get("MAIL_USERNAME", ""))
        if not recipient:
            return jsonify({"success": False, "message": "Provide ?to=your@email.com"}), 400
        ok, msg = send_otp_email(recipient, "999999")
        status = 200 if ok else 500
        return jsonify({"success": ok, "message": msg,
                        "mail_username": app.config.get("MAIL_USERNAME"),
                        "mail_server": app.config.get("MAIL_SERVER"),
                        "mail_port": app.config.get("MAIL_PORT"),
                        "mail_use_tls": app.config.get("MAIL_USE_TLS")}), status

    @app.get("/health")
    def health_check():
        return "ok", 200

    @app.get("/api/health")
    def api_health_check():
        return jsonify({"status": "ok", "service": "smart-bus-backend"}), 200

    return app


app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", "5000")))
    debug = os.getenv("FLASK_ENV", "development").lower() != "production"
    app.run(host=host, port=port, debug=debug)