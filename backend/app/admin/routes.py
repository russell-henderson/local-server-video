"""Admin routes for performance monitoring."""
from flask import Blueprint, render_template, jsonify
from backend.app.admin.performance import get_metrics

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/performance", methods=["GET"])
def performance_dashboard():
    """Render performance dashboard."""
    metrics = get_metrics()
    return render_template(
        "admin/performance.html",
        cache_hit_rate=metrics.get_cache_hit_rate(),
        uptime_seconds=metrics.get_uptime_seconds(),
        ratings_post_p95=metrics.get_ratings_post_p95_latency(),
        ratings_post_avg=metrics.get_ratings_post_avg_latency(),
        ratings_post_count=metrics.get_ratings_post_count()
    )


@admin_bp.route("/performance/json", methods=["GET"])
def performance_json():
    """JSON API for performance metrics."""
    metrics = get_metrics()
    
    # Calculate database stats
    with metrics.lock:
        total_db_queries = metrics.total_db_queries
        db_queries_count = len(metrics.db_queries_per_request)
        avg_per_request = (total_db_queries / db_queries_count
                           if db_queries_count else 0)
        max_per_request = (max(metrics.db_queries_per_request)
                           if metrics.db_queries_per_request else 0)
    
    return jsonify({
        "cache_hit_rate": metrics.get_cache_hit_rate(),
        "uptime_seconds": metrics.get_uptime_seconds(),
        "database": {
            "total_queries": total_db_queries,
            "avg_per_request": avg_per_request,
            "max_per_request": max_per_request,
            "count": db_queries_count
        },
        "ratings_post": {
            "p95_latency_ms": metrics.get_ratings_post_p95_latency(),
            "avg_latency_ms": metrics.get_ratings_post_avg_latency(),
            "request_count": metrics.get_ratings_post_count()
        },
        "endpoints": {}
    })


def register_admin_routes(app):
    """Register admin blueprint with Flask app."""
    app.register_blueprint(admin_bp)
