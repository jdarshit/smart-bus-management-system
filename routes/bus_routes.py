"""routes/bus_routes.py    HTML page routes for buses."""
from flask import (Blueprint, flash, jsonify, redirect,
                   render_template, request, url_for)

from models import db
from models.bus_model import Bus
from models.driver import Driver
from utils.auth_helpers import login_required, role_required

bus_bp = Blueprint("bus", __name__, url_prefix="/buses")


#  List Buses 

@bus_bp.route("/")
@login_required
@role_required("admin", "management", "driver")
def list_buses():
    buses = Bus.query.order_by(Bus.bus_number).all()
    return render_template("buses/index.html", buses=buses)


#  Add Bus 

@bus_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_bus():
    drivers = Driver.query.order_by(Driver.driver_name).all()
    if request.method == "POST":
        bus_number  = (request.form.get("bus_number")  or "").strip()
        license_plate = (request.form.get("license_plate") or "").strip() or None
        route_name  = (request.form.get("route_name")  or "").strip()
        rfid_uid    = (request.form.get("rfid_uid")    or "").strip() or None
        driver_name = (request.form.get("driver_name") or "").strip() or None

        if not bus_number:
            flash("Bus number is required.", "danger")
            return render_template("buses/form.html", drivers=drivers, action="add")

        existing = Bus.query.filter_by(bus_number=bus_number).first()
        if existing:
            flash(f"Bus number '{bus_number}' already exists.", "danger")
            return render_template("buses/form.html", drivers=drivers, action="add")

        bus = Bus(
            bus_number=bus_number,
            license_plate=license_plate,
            driver_name=driver_name,
            route_name=route_name or None,
            rfid_uid=rfid_uid,
        )
        db.session.add(bus)
        db.session.commit()

        # Keep driver.bus_number in sync for dashboards that rely on driver assignment.
        if driver_name:
            drv = Driver.query.filter_by(driver_name=driver_name).first()
            if drv:
                drv.bus_number = bus.bus_number
                db.session.commit()

        flash(f"Bus '{bus_number}' added successfully.", "success")
        return redirect(url_for("bus.list_buses"))

    return render_template("buses/form.html", drivers=drivers, action="add", bus=None)


#  Edit Bus 

@bus_bp.route("/<int:bus_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_bus(bus_id):
    bus     = Bus.query.get_or_404(bus_id)
    drivers = Driver.query.order_by(Driver.driver_name).all()

    if request.method == "POST":
        bus.bus_number = (request.form.get("bus_number") or bus.bus_number).strip()
        bus.license_plate = (request.form.get("license_plate") or bus.license_plate or "").strip() or None
        bus.driver_name = (request.form.get("driver_name") or bus.driver_name or "").strip() or None
        bus.route_name = request.form.get("route_name") or bus.route_name
        rfid_uid       = (request.form.get("rfid_uid") or "").strip()
        bus.rfid_uid   = rfid_uid if rfid_uid else None

        if bus.driver_name:
            drv = Driver.query.filter_by(driver_name=bus.driver_name).first()
            if drv:
                drv.bus_number = bus.bus_number

        db.session.commit()
        flash("Bus updated successfully.", "success")
        return redirect(url_for("bus.list_buses"))

    return render_template("buses/form.html", drivers=drivers, action="edit", bus=bus)


#  Delete Bus 

@bus_bp.route("/<int:bus_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_bus(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    num = bus.bus_number
    db.session.delete(bus)
    db.session.commit()
    flash(f"Bus '{num}' deleted.", "warning")
    return redirect(url_for("bus.list_buses"))


#  JSON API 

@bus_bp.route("/api", methods=["GET"])
def api_list():
    return jsonify([b.to_dict() for b in Bus.query.order_by(Bus.bus_number).all()])

@bus_bp.route("/api/<int:bus_id>", methods=["GET"])
def api_get(bus_id):
    return jsonify(Bus.query.get_or_404(bus_id).to_dict())

@bus_bp.route("/api/<int:bus_id>/arrivals", methods=["GET"])
def api_arrivals(bus_id):
    from models.arrival_model import Arrival
    bus      = Bus.query.get_or_404(bus_id)
    arrivals = bus.arrivals.order_by(Arrival.arrival_time.desc()).limit(20).all()
    return jsonify([a.to_dict() for a in arrivals])
