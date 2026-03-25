"""utils/auth_helpers.py
Decorators and helpers for session-based authentication.
"""
from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(f):
    """Redirect to login page if the user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Restrict a route to users whose role is in *roles.
    Must be applied AFTER @login_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("user_role") not in roles:
                flash("You do not have permission to view that page.", "danger")
                return redirect(url_for("auth.redirect_dashboard"))
            return f(*args, **kwargs)
        return decorated
    return decorator
