"""Admin package."""
from flask import Blueprint

# Shared admin blueprint used across admin routes.
# Mapped under /dashboard as per Phase 1 directive.
admin_bp = Blueprint("admin", __name__, url_prefix="/dashboard")

__all__ = ["admin_bp"]
