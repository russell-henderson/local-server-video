"""Admin package."""
from flask import Blueprint

# Shared admin blueprint used across admin routes.
# Routes declare their full paths so no url_prefix is set here.
admin_bp = Blueprint("admin", __name__)

__all__ = ["admin_bp"]
