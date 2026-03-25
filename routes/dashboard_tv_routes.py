"""routes/dashboard_tv_routes.py - TV control room dashboard routes."""
from flask import Blueprint, jsonify, render_template

from services.bus_arrival_service import lightweight_bus_status, tv_bus_status_snapshot


dashboard_tv_bp = Blueprint("dashboard_tv", __name__)


@dashboard_tv_bp.get("/dashboard/tv")
def dashboard_tv_page():
    return render_template("dashboard_tv.html")


@dashboard_tv_bp.get("/api/dashboard-tv/status")
def dashboard_tv_status_api():
    return jsonify(tv_bus_status_snapshot())


@dashboard_tv_bp.get("/api/bus_status")
def bus_status_api():
    return jsonify(lightweight_bus_status())
