"""routes/admin_bus_routes.py  —  Bus arrivals dashboard & AJAX API."""
from flask import Blueprint, jsonify, render_template

from services.bus_arrival_service import get_active_shift, latest_bus_arrivals
from utils.auth_helpers import login_required, role_required

admin_bus_bp = Blueprint("admin_bus", __name__, url_prefix="/admin")


@admin_bus_bp.get("/bus-arrivals")
@login_required
@role_required("admin", "management")
def bus_arrivals_dashboard():
    """Render the live bus arrivals dashboard page."""
    return render_template("admin/bus_arrivals_dashboard.html")


@admin_bus_bp.get("/api/bus-arrivals")
@login_required
@role_required("admin", "management")
def bus_arrivals_api():
    """AJAX endpoint polled every 1 second by the dashboard."""
    return jsonify({
        "arrivals": latest_bus_arrivals(100),
        "active_shift": get_active_shift(),
    })
