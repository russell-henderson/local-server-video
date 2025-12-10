"""Admin dashboard routes."""
from __future__ import annotations

from typing import Optional

from flask import jsonify, render_template, request

from backend.app.admin import admin_bp
from backend.app.admin.performance import DEFAULT_WINDOW_SECONDS
from performance_monitor import (
    ALLOWED_WINDOWS,
    get_performance_snapshot,
    get_route_metrics,
    get_worker_metrics,
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _error_response(
    code: str,
    message: str,
    details: Optional[dict] = None,
    status: int = 400,
):
    """Return a standardized error response."""
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
    return jsonify(payload), status


def _parse_bool(value: Optional[str], default: bool) -> bool:
    """Parse boolean query parameter."""
    if value is None:
        return default
    if value.lower() in {"true", "1", "yes"}:
        return True
    if value.lower() in {"false", "0", "no"}:
        return False
    raise ValueError("must be a boolean")


def _parse_int(raw_value: Optional[str], default: int, *, allowed: Optional[set[int]] = None) -> int:
    """Parse integer query parameter with optional validation."""
    if raw_value is None:
        return default
    value = int(raw_value)
    if allowed and value not in allowed:
        raise ValueError(f"must be one of {sorted(allowed)}")
    return value


# ============================================================================
# FLASK ROUTES
# ============================================================================

@admin_bp.route("/admin/performance", methods=["GET"])
def performance_page():
    """Render performance dashboard HTML page."""
    snapshot = get_performance_snapshot()
    return render_template("admin/performance.html", perf_snapshot=snapshot)


@admin_bp.route("/admin/performance/json", methods=["GET"])
def performance_json():
    """JSON API for performance metrics."""
    try:
        window_seconds = _parse_int(
            request.args.get("window_seconds"),
            default=DEFAULT_WINDOW_SECONDS,
            allowed=ALLOWED_WINDOWS,
        )
        include_routes = _parse_bool(request.args.get("include_routes"), False)
        include_workers = _parse_bool(request.args.get("include_workers"), True)
    except (ValueError, TypeError) as exc:
        return _error_response(
            "INVALID_PARAMETER",
            str(exc),
            {"parameter": "query", "value": request.args.to_dict()},
        )
    
    snapshot = get_performance_snapshot(
        window_seconds=window_seconds,
        include_routes=include_routes,
        include_workers=include_workers,
    )
    return jsonify(snapshot)


@admin_bp.route("/api/admin/performance/routes", methods=["GET"])
def performance_routes():
    """Return per-route metrics."""
    try:
        window_seconds = _parse_int(
            request.args.get("window_seconds"),
            default=DEFAULT_WINDOW_SECONDS,
            allowed=ALLOWED_WINDOWS,
        )
        sort_by = request.args.get("sort_by", "p95_latency_ms")
        order = request.args.get("order", "desc").lower()
        limit = _parse_int(request.args.get("limit"), 100)
        if limit < 1:
            raise ValueError("limit must be >= 1")
    except (ValueError, TypeError) as exc:
        return _error_response(
            "INVALID_PARAMETER",
            str(exc),
            {"parameter": "query", "value": request.args.to_dict()},
        )
    
    try:
        routes_payload = get_route_metrics(
            window_seconds=window_seconds,
            sort_by=sort_by,
            order=order,
            limit=limit,
        )
    except ValueError as exc:
        return _error_response(
            "INVALID_PARAMETER",
            str(exc),
            {"parameter": "query", "value": request.args.to_dict()},
        )
    except Exception as exc:
        return _error_response(
            "METRICS_UNAVAILABLE",
            "Unable to compute route metrics",
            {"error": str(exc)},
            status=500,
        )
    return jsonify(routes_payload)


@admin_bp.route("/api/admin/performance/workers", methods=["GET"])
def performance_workers():
    """Return worker and queue metrics."""
    workers_payload = get_worker_metrics()
    return jsonify(workers_payload)


@admin_bp.route("/api/admin/performance/active", methods=["GET"])
def performance_active_streams():
    """Return active stream info (last few minutes of /watch,/video)."""
    try:
        from performance_monitor import get_active_streams
        window_seconds = _parse_int(request.args.get("window_seconds"), 300)
        limit = _parse_int(request.args.get("limit"), 10)
        payload = get_active_streams(window_seconds=window_seconds, limit=limit)
        return jsonify(payload)
    except (ValueError, TypeError) as exc:
        return _error_response(
            "INVALID_PARAMETER",
            str(exc),
            {"parameter": "query", "value": request.args.to_dict()},
        )
    except Exception as exc:
        return _error_response(
            "METRICS_UNAVAILABLE",
            "Unable to compute active streams",
            {"error": str(exc)},
            status=500,
        )


# ============================================================================
# REGISTRATION FUNCTION (called from main.py)
# ============================================================================

def register_admin_routes(app):
    """Register admin blueprint with Flask app."""
    app.register_blueprint(admin_bp)
    return admin_bp
