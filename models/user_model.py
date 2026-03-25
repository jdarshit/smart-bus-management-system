from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from models import db

# ------------------------------------------------------------------ #
# Allowed roles - used for validation throughout the application       #
# ------------------------------------------------------------------ #
ALLOWED_ROLES = {"student", "driver", "admin", "management"}


class User(db.Model):
    """Authentication identity for every person in the system."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)          # student | driver | admin | management
    verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ---------------------------------------------------------------- #
    # Password helpers                                                   #
    # ---------------------------------------------------------------- #
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # ---------------------------------------------------------------- #
    # Serialisation helper (used by JSON APIs)                          #
    # ---------------------------------------------------------------- #
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "verified": self.verified,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
