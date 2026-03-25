"""
models/__init__.py

Active models for Bus Arrival System only.
All student / attendance / driver / mileage / RFID-card tables are removed.
"""

from extensions import db, migrate  # noqa: F401

from .user_model      import User             # noqa: F401  (auth)
from .otp_model       import OTPVerification  # noqa: F401  (email OTP)
from .bus_model       import Bus              # noqa: F401
from .arrival_model   import Arrival          # noqa: F401
from .bus_arrival_log import BusArrivalLog    # noqa: F401
from .system_settings_model import SystemSettings  # noqa: F401
from .student import Student  # noqa: F401
from .driver import Driver  # noqa: F401
from .attendance import Attendance  # noqa: F401

__all__ = [
    "db",
    "migrate",
    "User",
    "OTPVerification",
    "Bus",
    "Arrival",
    "BusArrivalLog",
    "SystemSettings",
    "Student",
    "Driver",
    "Attendance",
]
