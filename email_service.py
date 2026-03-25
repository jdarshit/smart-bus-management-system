import secrets
import logging
from typing import Tuple

from flask import current_app
from flask_mail import Message

from extensions import mail

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 5


def generate_otp() -> str:
    """Return a cryptographically secure 6-digit OTP string."""
    return f"{secrets.randbelow(1000000):06d}"


def _validate_mail_config() -> Tuple[bool, str]:
    """Return (True, 'ok') when all required mail keys are present and non-empty."""
    required = ["MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER"]
    missing = [k for k in required if not current_app.config.get(k)]
    if missing:
        return False, f"Missing mail config keys: {', '.join(missing)}"
    return True, "ok"


def send_otp_email(email: str, otp: str) -> Tuple[bool, str]:
    """
    Send an OTP verification email.

    Returns:
        (True, success_message) on success
        (False, error_reason)   on failure
    """
    config_ok, config_message = _validate_mail_config()
    if not config_ok:
        logger.error("Mail config invalid: %s", config_message)
        return False, config_message

    subject = "Smart Bus System – Email Verification"

    text_body = (
        "Smart Bus Management System\n"
        "Email Verification\n\n"
        f"Your OTP code is: {otp}\n\n"
        f"This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.\n\n"
        "If you did not request this, you can safely ignore this email."
    )

    html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;
            padding:24px;border:1px solid #e5e7eb;border-radius:8px;">
  <h2 style="margin:0 0 6px 0;color:#0f172a;">Smart Bus Management System</h2>
  <p style="margin:0 0 18px 0;color:#475569;font-size:14px;">Email Verification</p>
  <div style="padding:18px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;text-align:center;">
    <p style="margin:0 0 8px 0;color:#334155;font-size:14px;">Your one-time password:</p>
    <div style="font-size:32px;font-weight:700;letter-spacing:6px;color:#0f172a;
                font-family:monospace;">{otp}</div>
    <p style="margin:12px 0 0 0;color:#64748b;font-size:13px;">
      Valid for <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
    </p>
  </div>
  <p style="margin:18px 0 0 0;color:#94a3b8;font-size:12px;">
    If you did not create an account, please ignore this email.
  </p>
</div>
"""

    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            body=text_body,
            html=html_body,
        )
        mail.send(msg)
        logger.info("OTP email sent to %s", email)
        return True, "OTP email sent successfully"
    except Exception as exc:
        logger.exception("OTP email send failed for %s", email)
        return False, f"Failed to send OTP email: {exc}"
