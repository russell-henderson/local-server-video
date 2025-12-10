# Admin Dashboard API Specification

This document defines the HTTP API that powers the admin performance dashboard.

The goal is to give a stable contract for the dashboard UI, backend implementation, and automated tests. It builds on the metrics types and collection rules defined in `docs/PERFORMANCE_MONITORING.md` and the general API rules in `API.md`.

---

## Endpoints Overview

Admin dashboard related endpoints:

* `GET /admin/performance`
  Returns the HTML admin performance dashboard page. Primarily used by browsers. Response is HTML, not JSON. Full behavior is defined in `ADMIN_DASHBOARD.md` and `ADMIN_DASHBOARD_IMPL_NOTES.md`.

* `GET /admin/performance/json`
  Returns the full performance snapshot that drives the admin dashboard UI. JSON only.

* `GET /api/admin/performance/routes`
  Returns a detailed table of route level metrics with percentile latency, error rates, and status labels.

* `GET /api/admin/performance/workers`
  Returns background worker and queue metrics used for the worker status widgets and warning badges.

* `GET /admin/cache/status`
  Returns cache status information. Already documented in `API.md`. The dashboard uses this endpoint to show preview cache health.

* `POST /admin/cache/refresh`
  Triggers a cache refresh. Already documented in `API.md`. The dashboard uses this endpoint behind the "Refresh cache" action.

This document provides full JSON contracts for the new JSON endpoints and describes how the dashboard expects to use the existing cache endpoints.

---

## Authentication

* Admin endpoints are intended for local and trusted LAN access only.
* In the current version, access control is handled by:

  * IP allowlist configuration in the server settings.
  * Optional HTTP basic auth or reverse proxy level auth if configured in deployment.
* There is no per user authentication or authorization inside this API contract. If that changes in the future, `ADMIN_API_SPEC.md` and `API.md` must be updated in sync.

All JSON endpoints accept requests without special auth headers as long as the request passes the IP and proxy level checks.

---

## Base URL

The admin dashboard endpoints share the same base URL as the main app.

* Protocol: `http` or `https` depending on deployment.
* Host: `localhost` or the LAN hostname or IP.
* Port: configurable, default `5000` in development.

Examples in this document assume:

* Base URL: `http://localhost:5000`

Adjust host and port as needed for your environment.

---

## Endpoints

### 1. GET /admin/performance/json

Returns a complete snapshot of performance metrics and system health for the admin dashboard.

#### Purpose

* Provide a single payload that the dashboard can poll on an interval.
* Avoid multiple round trips for basic summary view.
* Reuse metrics defined in `PERFORMANCE_MONITORING.md`.

#### Request

* Method: `GET`
* URL: `/admin/performance/json`
* Query parameters:

  * `window_seconds` (optional, integer)

    * Rolling time window for metrics aggregation.
    * Default: `900` (15 minutes).
    * Acceptable values: `300`, `900`, `3600`.
  * `include_routes` (optional, boolean)

    * If `true`, include full route metrics list.
    * Default: `false` to keep payload small. Use `/api/admin/performance/routes` for full table if needed.
  * `include_workers` (optional, boolean)

    * If `true`, include worker metrics summary.
    * Default: `true`.

Example:

```bash
curl "http://localhost:5000/admin/performance/json?window_seconds=900&include_routes=true&include_workers=true"
```

#### Successful Response

* Status: `200 OK`
* Content type: `application/json; charset=utf-8`
* Body: `PerformanceSnapshot` (defined in Data Types and Schemas)

Example:

```json
{
  "generated_at": "2025-12-09T18:30:12.451Z",
  "window_seconds": 900,
  "server": {
    "version": "v1.03.0",
    "environment": "development",
    "uptime_seconds": 84213,
    "hostname": "video-server-dev"
  },
  "global": {
    "request_count": 1852,
    "error_count": 12,
    "error_rate": 0.0065,
    "p50_latency_ms": 14.2,
    "p95_latency_ms": 72.9,
    "p99_latency_ms": 143.5
  },
  "ratings": {
    "path": "/api/ratings",
    "method": "POST",
    "request_count": 621,
    "error_count": 3,
    "error_rate": 0.0048,
    "p50_latency_ms": 21.0,
    "p95_latency_ms": 55.2,
    "p99_latency_ms": 100.4,
    "status": "good"
  },
  "cache": {
    "preview_cache_bytes": 2147483648,
    "preview_cache_limit_bytes": 53687091200,
    "preview_cache_usage_ratio": 0.04,
    "preview_cache_items": 3412,
    "last_refresh_at": "2025-12-09T18:25:00.000Z",
    "status": "good"
  },
  "workers": {
    "worker_count": 2,
    "queues": [
      {
        "name": "default",
        "pending_jobs": 3,
        "in_progress_jobs": 1,
        "failed_jobs": 0,
        "oldest_pending_age_seconds": 64
      },
      {
        "name": "heavy",
        "pending_jobs": 0,
        "in_progress_jobs": 0,
        "failed_jobs": 0,
        "oldest_pending_age_seconds": 0
      }
    ],
    "status": "good"
  },
  "status": {
    "overall": "good",
    "issues": []
  },
  "routes": null
}
```

Notes:

* `routes` will be `null` unless `include_routes=true`.
* Latency statistics must follow the definitions in `PERFORMANCE_MONITORING.md`.

#### Error Responses

* `400 Bad Request`

  * Invalid `window_seconds` or query parameter.
  * Error body:

    ```json
    {
      "success": false,
      "error": {
        "code": "INVALID_PARAMETER",
        "message": "window_seconds must be one of [300, 900, 3600]",
        "details": {
          "parameter": "window_seconds",
          "value": 42
        }
      }
    }
    ```

* `429 Too Many Requests`

  * If global rate limiting is reached. See Rate Limiting section.

* `500 Internal Server Error`

  * Unexpected error computing metrics.

---

### 2. GET /api/admin/performance/routes

Returns detailed route level metrics used by the "Per route performance table" in the dashboard.

#### Purpose

* Allow drill down into individual endpoints.
* Show latency percentiles, volumes, and status per route.

#### Request

* Method: `GET`
* URL: `/api/admin/performance/routes`
* Query parameters:

  * `window_seconds` (optional, integer, same semantics as above).
  * `sort_by` (optional, string)

    * Accepted values: `p95_latency_ms`, `error_rate`, `request_count`, `path`.
    * Default: `p95_latency_ms`.
  * `order` (optional, string)

    * Accepted values: `asc`, `desc`.
    * Default: `desc`.
  * `limit` (optional, integer)

    * Maximum number of routes to return.
    * Default: `100`.

Example:

```bash
curl "http://localhost:5000/api/admin/performance/routes?window_seconds=900&sort_by=p95_latency_ms&order=desc&limit=50"
```

#### Successful Response

* Status: `200 OK`
* Content type: `application/json; charset=utf-8`
* Body:

```json
{
  "generated_at": "2025-12-09T18:31:05.102Z",
  "window_seconds": 900,
  "routes": [
    {
      "path": "/api/ratings",
      "method": "POST",
      "name": "ratings_submit",
      "request_count": 621,
      "error_count": 3,
      "error_rate": 0.0048,
      "p50_latency_ms": 21.0,
      "p95_latency_ms": 55.2,
      "p99_latency_ms": 100.4,
      "status": "good"
    },
    {
      "path": "/preview/<video_id>",
      "method": "GET",
      "name": "preview_page",
      "request_count": 312,
      "error_count": 4,
      "error_rate": 0.0128,
      "p50_latency_ms": 40.5,
      "p95_latency_ms": 160.2,
      "p99_latency_ms": 280.1,
      "status": "warning"
    }
  ]
}
```

`status` uses the same thresholds that power the color coding in `ADMIN_DASHBOARD.md`.

#### Error Responses

Same format as `/admin/performance/json`, with these error codes:

* `INVALID_PARAMETER`
* `METRICS_UNAVAILABLE`

---

### 3. GET /api/admin/performance/workers

Returns the background worker and queue metrics for the admin dashboard.

#### Purpose

* Show worker count and queue lengths.
* Surface stalled or failing workers.

#### Request

* Method: `GET`
* URL: `/api/admin/performance/workers`
* Query parameters: none in v1.

Example:

```bash
curl "http://localhost:5000/api/admin/performance/workers"
```

#### Successful Response

* Status: `200 OK`
* Content type: `application/json; charset=utf-8`
* Body:

```json
{
  "generated_at": "2025-12-09T18:32:44.991Z",
  "worker_count": 2,
  "workers": [
    {
      "name": "worker-1",
      "queues": ["default", "heavy"],
      "last_heartbeat_at": "2025-12-09T18:32:30.000Z",
      "status": "healthy"
    },
    {
      "name": "worker-2",
      "queues": ["default"],
      "last_heartbeat_at": "2025-12-09T18:32:28.000Z",
      "status": "healthy"
    }
  ],
  "queues": [
    {
      "name": "default",
      "pending_jobs": 3,
      "in_progress_jobs": 1,
      "failed_jobs": 0,
      "oldest_pending_age_seconds": 64,
      "status": "healthy"
    },
    {
      "name": "heavy",
      "pending_jobs": 0,
      "in_progress_jobs": 0,
      "failed_jobs": 0,
      "oldest_pending_age_seconds": 0,
      "status": "idle"
    }
  ],
  "status": "good"
}
```

If the app does not use workers, this endpoint should still exist and return:

```json
{
  "generated_at": "2025-12-09T18:32:44.991Z",
  "worker_count": 0,
  "workers": [],
  "queues": [],
  "status": "disabled"
}
```

---

### 4. Existing Cache Endpoints Used by the Dashboard

These endpoints already exist and are documented in `API.md`. The admin dashboard uses them as follows:

* `GET /admin/cache/status`

  * Called when the dashboard loads and when the user clicks "Refresh" on the cache status widget.
  * Expected to return a JSON body with at least:

    * `preview_cache_bytes`
    * `preview_cache_limit_bytes`
    * `preview_cache_items`
    * `status`
* `POST /admin/cache/refresh`

  * Called when the user confirms a cache refresh action.
  * Expected to return a JSON body with:

    * `success` boolean
    * Optional `message` string.

If these response shapes change, update both `API.md` and this section.

---

## Error Handling

All JSON endpoints use a shared error response format.

### Standard Error JSON

```json
{
  "success": false,
  "error": {
    "code": "STRING_IDENTIFIER",
    "message": "Human readable description",
    "details": {
      "optional": "context specific data"
    }
  }
}
```

* `code` is a short machine friendly constant such as:

  * `INVALID_PARAMETER`
  * `METRICS_UNAVAILABLE`
  * `INTERNAL_ERROR`
* `message` is safe to show in the UI.
* `details` is optional and may hold additional context useful for debugging.

### HTTP Status Codes

* `200 OK`
  Successful response with valid JSON body.

* `400 Bad Request`
  Invalid query parameter or request format.

* `401 Unauthorized` or `403 Forbidden`
  Only if an additional auth layer is introduced. Not expected in the current pure IP allowlist design.

* `404 Not Found`
  Endpoint not registered. The dashboard should treat this as a misconfiguration.

* `429 Too Many Requests`
  Rate limit exceeded. The response must include a `Retry-After` header as configured in the global rate limiter.

* `500 Internal Server Error`
  Unexpected backend failure.

---

## Rate Limiting

The admin endpoints are primarily for use by a single user or a small group of trusted admins.

Recommended behavior:

* Share the global IP based rate limiter configuration.
* Do not add stricter limits for these endpoints unless needed.
* The dashboard front end should:

  * Poll `/admin/performance/json` at most once every 5 seconds.
  * Use manual refresh buttons for heavy views like full route tables.

If rate limiting is triggered:

* Backend returns `429 Too Many Requests`.
* Body uses the standard error JSON with code `RATE_LIMITED`.
* A `Retry-After` header indicates the cooldown in seconds.

Example:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests for admin performance metrics",
    "details": {
      "retry_after_seconds": 8
    }
  }
}
```

---

## Data Types and Schemas

This section defines reusable JSON structures. These should align conceptually with the metric types described in `PERFORMANCE_MONITORING.md`, but field names and formats here are the contract for the dashboard.

### PerformanceSnapshot

Used as the root object in `/admin/performance/json`.

Fields:

* `generated_at` (string, ISO 8601 UTC timestamp)
* `window_seconds` (integer)
* `server` (ServerInfo)
* `global` (GlobalMetrics)
* `ratings` (RouteMetrics or `null`)
* `cache` (CacheMetrics)
* `workers` (WorkerSummary)
* `status` (AdminStatus)
* `routes` (array of RouteMetrics or `null`)

### ServerInfo

* `version` (string)
  Application version string.

* `environment` (string)
  Example: `"development"`, `"production"`.

* `uptime_seconds` (integer)
  Seconds since the process started.

* `hostname` (string)

### GlobalMetrics

* `request_count` (integer)
* `error_count` (integer)
* `error_rate` (number, fraction between 0 and 1)
* `p50_latency_ms` (number)
* `p95_latency_ms` (number)
* `p99_latency_ms` (number)

### RouteMetrics

Used in `routes` arrays and the `ratings` field.

* `path` (string)
* `method` (string, upper case HTTP method)
* `name` (string, internal route name)
* `request_count` (integer)
* `error_count` (integer)
* `error_rate` (number)
* `p50_latency_ms` (number)
* `p95_latency_ms` (number)
* `p99_latency_ms` (number)
* `status` (string, enumeration)

  * Allowed values: `"good"`, `"warning"`, `"poor"`, `"unknown"`.

### CacheMetrics

* `preview_cache_bytes` (integer)
* `preview_cache_limit_bytes` (integer)
* `preview_cache_usage_ratio` (number, fraction between 0 and 1)
* `preview_cache_items` (integer)
* `last_refresh_at` (string, ISO 8601 UTC timestamp or `null`)
* `status` (string)

  * Allowed values: `"good"`, `"warning"`, `"full"`, `"unknown"`.

### WorkerSummary

* `worker_count` (integer)
* `workers` (array of WorkerInfo)
* `queues` (array of QueueInfo)
* `status` (string)

  * Allowed values: `"good"`, `"warning"`, `"error"`, `"disabled"`.

### WorkerInfo

* `name` (string)
* `queues` (array of string)
* `last_heartbeat_at` (string, ISO 8601 UTC timestamp or `null`)
* `status` (string)

  * Allowed values: `"healthy"`, `"stalled"`, `"unknown"`.

### QueueInfo

* `name` (string)
* `pending_jobs` (integer)
* `in_progress_jobs` (integer)
* `failed_jobs` (integer)
* `oldest_pending_age_seconds` (integer)
* `status` (string)

  * Allowed values: `"healthy"`, `"slow"`, `"stuck"`, `"idle"`.

### AdminStatus

* `overall` (string)

  * Allowed values: `"good"`, `"warning"`, `"critical"`, `"unknown"`.
* `issues` (array of string)

  * Human readable notes for the admin UI.

---

### Notes for Implementers

* All numeric fields should be safe for JSON number types in JavaScript.
* For latency values, use floating point with one decimal place where possible.
* Keep field names stable. If any change is needed, bump the version in `CHANGELOG.md` and update `ADMIN_DASHBOARD_FRONTEND.md` and `ADMIN_DASHBOARD_TESTING.md`.

---

=== UPDATE: Add this line to docs/DOCS_INVENTORY.md near the ADMIN_DASHBOARD_IMPL_NOTES.md row ===
`| 69 | docs/ | ADMIN_API_SPEC.md | Working | Feature | Admin dashboard API contract for JSON endpoints |`

---

=== NEW FILE: docs/ADMIN_DASHBOARD_BACKEND.md ===

# Admin Dashboard Backend Implementation

This document guides the backend implementation of the admin performance dashboard endpoints and their integration with the existing performance monitoring system.

It assumes:

* A Flask based application with the entry point `main.py`.
* Metrics collection logic described in `docs/PERFORMANCE_MONITORING.md`.
* Existing implementation notes in `docs/ADMIN_DASHBOARD_IMPL_NOTES.md`.

---

## File Structure

Recommended files and directories for the admin backend:

* `main.py`

  * Application factory or main Flask app instance.
  * Registers the admin routes or blueprint.

* `admin/__init__.py`

  * Optional module that defines a Flask blueprint named `admin_bp`.

* `admin/routes.py`

  * Contains all admin endpoints:

    * `/admin/performance`
    * `/admin/performance/json`
    * `/api/admin/performance/routes`
    * `/api/admin/performance/workers`

* `performance_monitor.py`

  * Provides functions or classes to access aggregated metrics and snapshots.
  * Already exists or should be implemented following `PERFORMANCE_MONITORING.md`.

If you prefer not to use a blueprint, you can place the routes directly in `main.py`. This document uses a blueprint pattern for clarity and better separation.

---

## Integration Points

The admin backend ties into the existing code in three main places.

1. **Application setup in `main.py`**

   * Import and register the admin blueprint.
   * Ensure URL prefixes match what the UI expects.

2. **Metrics access via `performance_monitor.py`**

   * Use a shared object or functions to read latency and error statistics:

     * Global metrics.
     * Route level metrics.
     * Worker and queue metrics if available.

3. **Cache management**

   * Reuse the existing cache status and refresh routes defined in `API.md`.
   * Do not duplicate cache logic in admin routes. The dashboard should call the existing endpoints.

---

## Step by Step Implementation

### 1. Register admin blueprint in `main.py`

Add code similar to the following in `main.py`:

```python
from flask import Flask
from admin.routes import admin_bp

def create_app():
    app = Flask(__name__)
    # Existing setup...
    app.register_blueprint(admin_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
```

If you already have an `app` instance at module level, register the blueprint on that instance instead.

### 2. Implement admin blueprint in `admin/__init__.py`

```python
from flask import Blueprint

admin_bp = Blueprint("admin", __name__)
```

### 3. Implement admin routes in `admin/routes.py`

This module should:

* Import the `admin_bp` blueprint.
* Import any metrics helpers from `performance_monitor.py`.
* Implement the four endpoints described in `ADMIN_API_SPEC.md`.

Skeleton:

```python
from flask import jsonify, render_template, request
from . import admin_bp
from performance_monitor import get_performance_snapshot, get_route_metrics, get_worker_metrics


@admin_bp.route("/admin/performance", methods=["GET"])
def admin_performance_page():
    """Render the HTML admin dashboard page."""
    return render_template("admin/performance.html")


@admin_bp.route("/admin/performance/json", methods=["GET"])
def admin_performance_json():
    """Return the JSON snapshot used by the dashboard."""
    window_seconds = _parse_window_seconds(request.args.get("window_seconds"))
    include_routes = request.args.get("include_routes", "false").lower() == "true"
    include_workers = request.args.get("include_workers", "true").lower() == "true"

    snapshot = get_performance_snapshot(
        window_seconds=window_seconds,
        include_routes=include_routes,
        include_workers=include_workers,
    )
    return jsonify(snapshot)


@admin_bp.route("/api/admin/performance/routes", methods=["GET"])
def admin_performance_routes():
    """Return per route metrics."""
    window_seconds = _parse_window_seconds(request.args.get("window_seconds"))
    sort_by = request.args.get("sort_by", "p95_latency_ms")
    order = request.args.get("order", "desc")
    limit = _parse_int(request.args.get("limit"), default=100)

    routes_payload = get_route_metrics(
        window_seconds=window_seconds,
        sort_by=sort_by,
        order=order,
        limit=limit,
    )
    return jsonify(routes_payload)


@admin_bp.route("/api/admin/performance/workers", methods=["GET"])
def admin_performance_workers():
    """Return worker and queue metrics."""
    workers_payload = get_worker_metrics()
    return jsonify(workers_payload)
```

Helper parsing functions:

```python
def _parse_window_seconds(raw_value, default=900):
    allowed = {300, 900, 3600}
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value not in allowed:
        return default
    return value


def _parse_int(raw_value, default):
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default
```

### 4. Implement metrics helpers in `performance_monitor.py`

This module is the bridge between low level metrics collection and the JSON shapes defined in `ADMIN_API_SPEC.md`.

Existing metrics collection should already be in place as described in `PERFORMANCE_MONITORING.md`. Extend it with three helper functions:

* `get_performance_snapshot(window_seconds: int, include_routes: bool, include_workers: bool) -> dict`
* `get_route_metrics(window_seconds: int, sort_by: str, order: str, limit: int) -> dict`
* `get_worker_metrics() -> dict`

These functions should:

1. Call your existing metrics storage or aggregator.
2. Compute percentiles using the same method used elsewhere in the codebase.
3. Compose dictionaries that match:

   * `PerformanceSnapshot`
   * The payload for `/api/admin/performance/routes`
   * The payload for `/api/admin/performance/workers`

as defined in `ADMIN_API_SPEC.md`.

Pseudo code for `get_performance_snapshot`:

```python
from datetime import datetime, timezone

def get_performance_snapshot(window_seconds, include_routes, include_workers):
    now = datetime.now(timezone.utc)

    global_metrics = compute_global_metrics(window_seconds)
    ratings_metrics = compute_route_metrics("/api/ratings", "POST", window_seconds)
    cache_metrics = read_cache_metrics()
    worker_summary = compute_worker_summary() if include_workers else empty_worker_summary()

    snapshot = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "window_seconds": window_seconds,
        "server": read_server_info(),
        "global": global_metrics,
        "ratings": ratings_metrics,
        "cache": cache_metrics,
        "workers": worker_summary,
        "status": compute_overall_status(
            global_metrics=global_metrics,
            ratings_metrics=ratings_metrics,
            cache_metrics=cache_metrics,
            worker_summary=worker_summary,
        ),
        "routes": None,
    }

    if include_routes:
        snapshot["routes"] = compute_all_route_metrics(window_seconds)

    return snapshot
```

All of the helper functions such as `compute_global_metrics` should reuse or wrap the existing metrics logic so there is a single source of truth.

---

## Database and Storage

The admin dashboard reads metrics only. It does not write to application tables.

* Metrics can be stored in memory, SQLite, or another store as defined in `PERFORMANCE_MONITORING.md`.
* The admin endpoints should:

  * Never mutate video metadata or user favorites.
  * Treat the metrics store as read only.
* Worker metrics may come from:

  * RQ or Celery APIs.
  * Custom monitoring tables.
  * Log based summaries.

Document any backend specific details in `ADMIN_DASHBOARD_IMPL_NOTES.md` rather than here.

---

## Caching Strategy

For admin metrics:

* Prefer to compute metrics from recent samples in memory or from a metrics table.
* If aggregation is expensive, you may cache the snapshot in process for a short time (for example 2 to 5 seconds) and reuse it between requests.
* Cache keys should include `window_seconds` and whether routes or workers are included.

Do not cache responses for longer periods by default. The dashboard should reflect near real time state.

---

## Error Handling Patterns

All admin routes returning JSON should:

* Catch predictable user errors (invalid parameters) and return `400` with `INVALID_PARAMETER`.
* Allow unexpected exceptions to be caught by a shared error handler that converts them into the standard error JSON with `500` status.

Example pattern:

```python
from werkzeug.exceptions import BadRequest

@admin_bp.route("/admin/performance/json", methods=["GET"])
def admin_performance_json():
    try:
        window_seconds = _parse_window_seconds_or_raise(request.args.get("window_seconds"))
    except BadRequest as exc:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": str(exc),
                    "details": {},
                },
            }
        ), 400

    # normal path...
```

A global error handler can be used instead if you prefer to centralize error formatting.

---

## Testing Strategy (Backend Focus)

Backend tests are described in more detail in `ADMIN_DASHBOARD_TESTING.md`. This section lists the minimal backend coverage required.

* Tests for `/admin/performance/json`

  * Returns `200` and valid JSON.
  * Respects `window_seconds` parameter.
  * Includes or omits `routes` and `workers` based on query parameters.

* Tests for `/api/admin/performance/routes`

  * Sorting by `p95_latency_ms`, `error_rate`, and `request_count` works as expected.
  * Limits results with `limit`.
  * Handles empty metrics gracefully.

* Tests for `/api/admin/performance/workers`

  * Correct structure when workers are enabled.
  * Correct structure when workers are not configured.

* Error cases

  * Invalid `window_seconds` returns `400` or falls back cleanly according to your chosen behavior.
  * Global error handler returns standard error JSON.

Use pytest and the existing test project structure as described in `QA_TESTING_GUIDE.md`.