"""Admin routes for performance monitoring."""
from flask import Blueprint, render_template, jsonify
from backend.app.admin.performance import get_metrics

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/performance", methods=["GET"])
def performance_dashboard():
    """Render performance dashboard."""
    metrics = get_metrics()
    return render_template("admin/performance.html")


@admin_bp.route("/performance/json", methods=["GET"])
def performance_json():
    """JSON API for performance metrics."""
    metrics = get_metrics()
    return jsonify({
        "cache_hit_rate": metrics.get_cache_hit_rate(),
        "uptime_seconds": metrics.get_uptime_seconds()
    })


def register_admin_routes(app):
    """Register admin blueprint with Flask app."""
    app.register_blueprint(admin_bp)
