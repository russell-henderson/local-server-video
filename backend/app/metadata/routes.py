"""Metadata/analytics/admin runtime route blueprint."""

from flask import Blueprint

from backend.app import legacy_runtime as legacy

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route("/admin/cache/status")
def cache_status():
    return legacy.cache_status()


@metadata_bp.route("/admin/cache/refresh", methods=["POST"])
def refresh_cache():
    return legacy.refresh_cache()


@metadata_bp.route("/admin/metadata/prune", methods=["POST"])
def admin_metadata_prune():
    return legacy.admin_metadata_prune()


@metadata_bp.route("/analytics/save", methods=["POST"])
def save_analytics():
    return legacy.save_analytics()


@metadata_bp.route("/analytics/get/<path:filename>")
def get_analytics(filename: str):
    return legacy.get_analytics(filename)


@metadata_bp.route("/analytics/export")
def export_analytics():
    return legacy.export_analytics()


@metadata_bp.route("/analytics/stats")
def analytics_stats():
    return legacy.analytics_stats()
