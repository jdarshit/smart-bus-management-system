"""services/bus_status_service.py

Two responsibilities:
  1. Upsert BusStatus after every successful RFID student scan.
  2. Send a parent / guardian boarding-alert e-mail.
"""
from __future__ import annotations

import datetime as dt
import logging

from flask import current_app
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError

from extensions import db, mail
from models.bus_location import BusLocation
from models.bus_model import Bus
from models.bus_status_model import BusStatus
from models.student import Student

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Bus Status                                                          #
# ------------------------------------------------------------------ #

def update_bus_status(bus: Bus, student: Student, scan_time: dt.datetime) -> BusStatus:
    """Upsert the BusStatus row for *bus*.

    Keeps exactly one row per bus; every new scan overwrites
    last_scan_time and last_student_id.
    """
    status = BusStatus.query.filter_by(bus_id=bus.id).first()

    if status is None:
        status = BusStatus(
            bus_id=bus.id,
            last_scan_time=scan_time,
            last_student_id=student.id,
            updated_at=scan_time,
        )
        db.session.add(status)
    else:
        status.last_scan_time  = scan_time
        status.last_student_id = student.id
        status.updated_at      = scan_time

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Failed to update BusStatus for bus_id=%s", bus.id)

    return status


def get_all_bus_status() -> list[dict]:
    """Return all BusStatus rows as plain dicts, newest scan first."""
    rows = BusStatus.query.order_by(BusStatus.last_scan_time.desc()).all()
    return [row.to_dict() for row in rows]


def get_bus_status_by_number(bus_number: str) -> dict | None:
    """Return BusStatus dict for a specific bus_number, or None."""
    row = (
        BusStatus.query
        .join(Bus)
        .filter(Bus.bus_number == bus_number)
        .first()
    )
    return row.to_dict() if row else None


def get_bus_status_snapshot(bus_identifier: str) -> dict | None:
    """Return a GPS-optional status payload for one bus.

    Shape matches the GPS-optional contract:
    {
      "bus_id": "BUS_01",
      "last_rfid_scan": "2026-03-15 12:20",
      "latitude": null,
      "longitude": null
    }
    """
    value = (bus_identifier or "").strip()
    if not value:
        return None

    if value.isdigit():
        bus = Bus.query.filter_by(id=int(value)).first()
    else:
        bus = Bus.query.filter_by(bus_number=value).first()

    if bus is None:
        return None

    status_row = BusStatus.query.filter_by(bus_id=bus.id).first()
    location_row = (
        BusLocation.query
        .filter_by(bus_id=bus.id)
        .order_by(BusLocation.timestamp.desc())
        .first()
    )

    return {
        "bus_id": bus.bus_number,
        "last_rfid_scan": (
            status_row.last_scan_time.strftime("%Y-%m-%d %H:%M")
            if status_row and status_row.last_scan_time
            else None
        ),
        "latitude": location_row.latitude if location_row else None,
        "longitude": location_row.longitude if location_row else None,
    }


# ------------------------------------------------------------------ #
#  Parent / Guardian E-mail Notification                               #
# ------------------------------------------------------------------ #

def send_boarding_email(student: Student, bus: Bus, scan_time: dt.datetime) -> bool:
    """Send a bus-boarding alert to the student's registered e-mail.

    The 'registered e-mail' is taken from student.user.email when
    the student account is linked to a User record.  If no linked user
    is found the function logs a warning and returns False without
    raising.

    Returns True on success, False if skipped / failed.

    WhatsApp webhook placeholder:
        To add WhatsApp, post to your Twilio / WA Cloud API URL here
        using the same student / bus / scan_time data.
    """
    # ---------- resolve recipient e-mail ----------
    recipient: str | None = None
    try:
        if student.user_id and student.user:
            recipient = student.user.email
    except Exception:
        pass

    if not recipient:
        logger.warning(
            "[RFID notify] Student id=%s has no linked user email – skipping notification",
            student.id,
        )
        return False

    # ---------- compose message ----------
    formatted_time = scan_time.strftime("%I:%M %p")          # e.g. "11:40 AM"
    formatted_date = scan_time.strftime("%B %d, %Y")          # e.g. "March 15, 2026"
    student_name = getattr(student, "student_name", None) or getattr(student, "name", "Student")
    pickup_point = getattr(student, "pickup_point", None) or getattr(student, "pickup_stop", None) or "N/A"

    subject = "Bus Boarding Alert"
    body = (
        f"Dear Parent / Guardian,\n\n"
        f"Your child {student_name} has boarded Bus {bus.bus_number} "
        f"at {formatted_time} on {formatted_date}.\n\n"
        f"Bus Route : {bus.route_name or 'N/A'}\n"
        f"Pickup Point: {pickup_point}\n\n"
        f"This is an automated notification from the Smart Bus Management System.\n"
        f"Please do not reply to this e-mail."
    )

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#1a73e8;padding:20px 24px">
        <h2 style="color:#fff;margin:0">&#128652; Bus Boarding Alert</h2>
      </div>
      <div style="padding:24px">
        <p>Dear Parent / Guardian,</p>
        <p>
                    <strong>{student_name}</strong> has boarded
          <strong>Bus {bus.bus_number}</strong> at
          <strong>{formatted_time}</strong> on {formatted_date}.
        </p>
        <table style="width:100%;border-collapse:collapse;margin-top:16px">
          <tr style="background:#f5f5f5">
            <td style="padding:8px 12px;font-weight:bold">Bus Number</td>
            <td style="padding:8px 12px">{bus.bus_number}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;font-weight:bold">Bus Route</td>
            <td style="padding:8px 12px">{bus.route_name or "N/A"}</td>
          </tr>
          <tr style="background:#f5f5f5">
            <td style="padding:8px 12px;font-weight:bold">Pickup Point</td>
                        <td style="padding:8px 12px">{pickup_point}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;font-weight:bold">Scan Time</td>
            <td style="padding:8px 12px">{formatted_time}, {formatted_date}</td>
          </tr>
        </table>
        <p style="margin-top:24px;color:#666;font-size:13px">
          This is an automated message. Please do not reply.
        </p>
      </div>
    </div>
    """

    # ---------- send ----------
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body,
            html=html_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )
        mail.send(msg)
        logger.info(
            "[RFID notify] Boarding email sent to %s for student %s",
            recipient, student_name,
        )
        return True

    except Exception as exc:          # never crash an RFID scan due to email failure
        logger.warning(
            "[RFID notify] Failed to send boarding email to %s: %s",
            recipient, exc,
        )
        return False


# ------------------------------------------------------------------ #
#  WhatsApp webhook placeholder                                        #
# ------------------------------------------------------------------ #

def send_whatsapp_notification(student: Student, bus: Bus, scan_time: dt.datetime) -> bool:
    """Placeholder for WhatsApp integration (e.g. Twilio / Meta Cloud API).

    Replace the body of this function with an HTTP POST to your
    WhatsApp API endpoint.  Returns True on success.

    Example (Twilio):
        import requests
        payload = {
            "To":   f"whatsapp:{parent_phone}",
            "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            "Body": f"{student.student_name} boarded {bus.bus_number} at ..."
        }
        requests.post(TWILIO_MESSAGES_URL, data=payload,
                      auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    """
    logger.info(
        "[WhatsApp placeholder] Would notify about %s boarding %s at %s",
        student.student_name, bus.bus_number, scan_time,
    )
    return False   # change to True once real integration is wired up
