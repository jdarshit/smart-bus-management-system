"""routes/admin_bus_map_routes.py

Admin bus map page.

  GET /admin/bus_map  – live Leaflet map of all buses
"""
from flask import Blueprint, render_template

from models.bus_model import Bus
from services.gps_service import get_all_latest_locations
from utils.auth_helpers import login_required, role_required

admin_bus_map_bp = Blueprint("admin_bus_map", __name__, url_prefix="/admin")


@admin_bus_map_bp.get("/bus_map")
@login_required
@role_required("admin")
def bus_map_page():
    """Admin live map – initial data loaded server-side, then polled via AJAX."""
    buses = Bus.query.order_by(Bus.bus_number).all()
    initial_locations = get_all_latest_locations()
    return render_template(
        "admin/bus_map.html",
        buses=buses,
        initial_locations=initial_locations,
    )
