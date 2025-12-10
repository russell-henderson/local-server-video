# Performance Monitoring and Metrics

## 1. Purpose and scope

This document defines how Local Video Server collects, aggregates, and exposes performance metrics.

It covers:

- The `PerformanceMetrics` singleton in `backend/app/admin/performance.py`
- The decorators and helpers in `performance_monitor.py`
- The JSON payload returned by `GET /admin/performance/json`
- The target schema for the planned `GET /api/admin/performance/routes` endpoint

This file works together with:

- `docs/PERFORMANCE.md` for performance goals, thresholds, and tuning strategy
- `docs/ARCHITECTURE.md` for where metrics live in the system design
- `docs/API.md` for the canonical list of admin and metrics endpoints

`PERFORMANCE.md` answers: what does good performance look like.  
`PERFORMANCE_MONITORING.md` answers: how do we measure and expose it.

---

## 2. Metrics model overview

### 2.1 Two layers of monitoring

There are two related but currently separate monitoring layers in the codebase.

1. **Admin metrics layer**

   - Implemented by `PerformanceMetrics` in `backend/app/admin/performance.py`
   - Read by admin routes in `backend/app/admin/routes.py`
   - Exposed via:
     - `GET /admin/performance` (HTML dashboard)
     - `GET /admin/performance/json` (JSON snapshot)

   This is the canonical model for the admin dashboard and for future admin APIs.

2. **Optional diagnostic layer**

   - Implemented by `PerformanceMonitor` in `performance_monitor.py`
   - Wired into the Flask app in `main.py` via `flask_route_monitor(app)`
   - Provides:
     - Generic function timing with `@performance_monitor`
     - Basic per route timing via `PerformanceMonitor.route_stats`
     - System metrics via `get_system_stats()`
     - Human readable reports via `performance_report()`
     - Load test helper via `load_test_simulation()`

   This layer is currently used for logging, ad hoc inspection, and local load testing. It does not directly back the admin JSON endpoint yet, but it is compatible with the schemas defined here.

The long term expectation is that admin metrics and diagnostic metrics either share a common schema or are bridged so that `PerformanceMetrics` and `PerformanceMonitor` do not drift apart.

### 2.2 Metric domains

Across these layers, metrics are organized into domains:

- **Route metrics**

  Latency and error counts per logical route.

- **Ratings POST metrics**

  Latency distribution and request volume for `POST /api/ratings/<media_hash>`.

- **Cache metrics**

  Cache hits, misses, and cache hit rate.

- **Database metrics**

  Query volume and fan out per request.

- **Resource metrics**

  Uptime for the server process, and optional CPU and memory usage when `psutil` is available.

Each domain has a defined schema that admin and SPA dashboards can rely on.

---

## 3. Admin metrics: `PerformanceMetrics`

### 3.1 Location and responsibility

**File:** `backend/app/admin/performance.py`  
**Class:** `PerformanceMetrics`  
**Factory:** `get_metrics()`

Responsibilities:

- Maintain process wide metrics for:
  - Cache usage
  - Endpoint latency samples
  - Database query counts
  - Ratings POST latency samples
  - Uptime
- Provide methods used by:
  - `backend/app/admin/routes.py` for HTML admin dashboard and JSON endpoint
  - Future admin API handlers under `/api/admin/performance/...`

`get_metrics()` returns a singleton instance that is shared across the app.

### 3.2 Internal fields

The current implementation maintains:

```python
class PerformanceMetrics:
    """Track cache hits, endpoint latency, DB queries."""

    def __init__(self):
        self.lock = threading.RLock()
        self.cache_hits = 0
        self.cache_misses = 0

        # Per endpoint latency samples in seconds
        self.endpoint_latencies = defaultdict(list)

        # Per request database query counts
        self.db_queries_per_request = []
        self.total_db_queries = 0

        # Start time for uptime
        self.start_time = time.time()

        # Specifically track POST /api/ratings latencies (seconds)
        self.ratings_post_latencies = []
```

All write operations and any multi field reads must be protected with `self.lock` to avoid race conditions.

The list fields are treated as rolling windows. For future work, the standard is:

- Keep at most the last 100 samples per route in `endpoint_latencies`
- Keep at most the last 100 entries in `db_queries_per_request`
- Keep at most the last 100 samples in `ratings_post_latencies`

This aligns with the rolling window used by `PerformanceMonitor` and keeps memory bounded.

### 3.3 Public methods

The key methods provided by `PerformanceMetrics` are:

```python
def record_cache_hit(self) -> None: ...
def record_cache_miss(self) -> None: ...
def get_cache_hit_rate(self) -> float: ...

def get_uptime_seconds(self) -> float: ...

# Ratings POST specific
def get_ratings_post_p95_latency(self) -> float: ...
def get_ratings_post_avg_latency(self) -> float: ...
def get_ratings_post_count(self) -> int: ...
```

Additional helper methods for route metrics and database metrics are implemented indirectly in `routes.py` by reading and aggregating raw fields under the metrics lock.

---

## 4. Diagnostic metrics: `performance_monitor.py`

### 4.1 Location and imports

**File:** `performance_monitor.py`

This module defines a higher level diagnostic monitor that is independent from `PerformanceMetrics`:

- `PerformanceMetric` dataclass
- `PerformanceMonitor` singleton (`monitor`)
- Decorators:

  - `performance_monitor(func_name: Optional[str] = None)`
  - `flask_route_monitor(app)`
- Helpers:

  - `get_system_stats()`
  - `performance_report()`
  - `load_test_simulation()`

In `main.py`, the app wires this monitor as follows:

```python
from performance_monitor import flask_route_monitor, performance_monitor
app = flask_route_monitor(app)
```

If the import fails, a no op `performance_monitor` decorator is defined to keep the app running without diagnostic metrics.

### 4.2 PerformanceMonitor behavior

`PerformanceMonitor` tracks:

- `metrics`: recent `PerformanceMetric` instances
- `route_stats`: per route timing lists
- `cache_stats`: simple cache hit and miss counters

Key methods:

```python
monitor.record_metric(metric: PerformanceMetric) -> None
monitor.record_route_time(route: str, duration: float) -> None
monitor.record_cache_hit() -> None
monitor.record_cache_miss() -> None
monitor.get_cache_hit_rate() -> float
monitor.get_route_stats() -> Dict[str, Dict[str, float]]
monitor.get_recent_metrics(n: int) -> List[PerformanceMetric]
monitor.reset_stats() -> None
```

The decorator `@performance_monitor`:

- Measures function duration
- Captures memory usage before and after
- Records a `PerformanceMetric`
- Heuristically classifies some functions as route like and forwards them into `route_stats`

The `flask_route_monitor(app)` function:

- Adds `before_request` and `after_request` handlers
- Records an accurate per request duration keyed by `"METHOD endpoint"` using `monitor.record_route_time`
- Does not integrate with `PerformanceMetrics` yet

`get_system_stats()` uses `psutil` to report CPU, memory, disk IO, open file handles, and thread count. This is currently used by `performance_report()` and by `load_test_simulation()`, but not yet wired into admin JSON.

---

## 5. Metric domain schemas

This section defines the metric schemas that admin and SPA dashboards should use. Some fields are already present in `GET /admin/performance/json`. Others are target shapes for planned extensions such as route metrics and resource metrics.

### 5.1 Route metrics

#### 5.1.1 Purpose

Route metrics capture latency and error behavior per route, for example:

- `GET /`
- `GET /watch/<filename>`
- `GET /api/ratings/<media_hash>`
- `POST /api/ratings/<media_hash>`

Currently, `PerformanceMetrics` stores per endpoint latency samples in `endpoint_latencies`, but `GET /admin/performance/json` still returns `"endpoints": {}`. The route metrics schema below is the target design for:

- Future `endpoints` content in `/admin/performance/json`
- The planned `GET /api/admin/performance/routes` API

#### 5.1.2 Aggregation rules

- Window per route: last 100 samples
- Unit of samples: seconds
- Unit in JSON: milliseconds
- Percentiles:

  - p50, p95, p99 calculated using `statistics.quantiles`
- Counters:

  - `request_count`: number of samples in the window
  - `error_count`: number of samples that were classified as errors

Error classification is defined as:

- Any response with an HTTP status in the 5xx range
- Any unhandled exception that occurs while serving the request

#### 5.1.3 Route stats schema

Target route stats object:

```json
{
  "route": "GET /watch/<filename>",
  "endpoint": "main.watch",
  "p50_ms": 20.1,
  "p95_ms": 45.9,
  "p99_ms": 80.2,
  "avg_ms": 28.3,
  "min_ms": 15.0,
  "max_ms": 110.4,
  "request_count": 89,
  "error_count": 1,
  "last_updated": "2025-12-09T17:30:15Z"
}
```

For the first implementation:

- `min_ms`, `max_ms`, and `last_updated` can be omitted if not convenient
- `p50_ms`, `p95_ms`, `p99_ms`, `avg_ms`, `request_count`, and `error_count` should be considered core

The planned `GET /api/admin/performance/routes` endpoint will return an array of these objects.

### 5.2 Ratings POST metrics

#### 5.2.1 Purpose

Ratings POST metrics track the latency and volume of `POST /api/ratings/<media_hash>`, which is a key write operation used by the Quest rating widget and other clients.

`PerformanceMetrics` already maintains:

- `ratings_post_latencies` in seconds
- Helper methods:

  - `get_ratings_post_p95_latency()` returns p95 latency in milliseconds
  - `get_ratings_post_avg_latency()` returns average latency in milliseconds
  - `get_ratings_post_count()` returns the number of samples

#### 5.2.2 Aggregation rules

- Window: last 100 POST samples
- Unit of samples: seconds
- Unit in JSON: milliseconds
- Percentile: p95 using `statistics.quantiles`
- Average: arithmetic mean using `statistics.mean`

#### 5.2.3 JSON schema

`GET /admin/performance/json` uses the following block:

```json
"ratings_post": {
  "p95_latency_ms": 42.7,
  "avg_latency_ms": 31.2,
  "request_count": 58
}
```

Fields:

- `p95_latency_ms`
  P95 latency over the current window in milliseconds
- `avg_latency_ms`
  Average latency over the current window in milliseconds
- `request_count`
  Number of POST requests in the window

This block is already live and backed by the current `PerformanceMetrics` implementation.

### 5.3 Cache metrics

#### 5.3.1 Purpose

Cache metrics describe how well the metadata and ratings caches are working. They are used to:

- Validate that the cache is being hit instead of disk or database
- Detect regressions where changes reduce cache effectiveness

In the admin metrics layer, `PerformanceMetrics` tracks:

- `cache_hits`
- `cache_misses`

and provides:

```python
def record_cache_hit(self) -> None: ...
def record_cache_miss(self) -> None: ...
def get_cache_hit_rate(self) -> float: ...
```

`get_cache_hit_rate()` returns a percentage between 0 and 100.

The diagnostic monitor in `performance_monitor.py` maintains similar fields in `cache_stats` and uses the same percentage semantics for `get_cache_hit_rate()`.

#### 5.3.2 Aggregation rules

- `cache_hits` and `cache_misses` are monotonic counters from process start

- `hit_rate` is defined as:

  ```text
  100 * hits / (hits + misses)
  ```

- If there are no requests yet (no hits and no misses), hit rate is `0.0`

#### 5.3.3 JSON schema

`GET /admin/performance/json` currently exposes:

```json
"cache_hit_rate": 93.0
```

This is interpreted as:

- `93.0` percent cache hit rate since process start

A future extended schema could be:

```json
"cache": {
  "hits": 1234,
  "misses": 91,
  "hit_rate_percent": 93.1
}
```

If and when this extension is introduced, the admin UI should continue to support the legacy top level `cache_hit_rate` field for compatibility.

### 5.4 Database metrics

#### 5.4.1 Purpose

Database metrics capture how many queries are executed per request and in total, so that:

- Inefficient endpoints can be identified
- Regressions in query fan out can be caught

`PerformanceMetrics` maintains:

- `db_queries_per_request`: list of integers
- `total_db_queries`: cumulative integer count

`backend/app/admin/routes.py` computes summary statistics inside `performance_json` while holding `metrics.lock`.

#### 5.4.2 Aggregation rules

- Window: `db_queries_per_request` is treated as a rolling window, with a planned cap of 100 entries to keep memory bounded
- `total_db_queries`: sum of counts in the current window
- `count`: number of entries in `db_queries_per_request`
- `avg_per_request`: `total_db_queries / count` or `0` if `count` is zero
- `max_per_request`: maximum value in `db_queries_per_request` or `0` if the list is empty

#### 5.4.3 JSON schema

`GET /admin/performance/json` returns:

```json
"database": {
  "total_queries": 420,
  "avg_per_request": 4.2,
  "max_per_request": 12,
  "count": 100
}
```

Fields:

- `total_queries`
  Sum of queries across the current window
- `avg_per_request`
  Average queries per request in the window
- `max_per_request`
  Maximum queries for a single request in the window
- `count`
  Number of requests represented in this window

### 5.5 Resource metrics

#### 5.5.1 Purpose

Resource metrics describe server health and capacity. At minimum, we track uptime. Optionally, the diagnostic layer can report system resources such as:

- CPU usage
- Memory usage
- Disk IO

#### 5.5.2 Uptime

`PerformanceMetrics` sets `start_time` in `__init__` using `time.time()` and provides:

```python
def get_uptime_seconds(self) -> float:
    """Return uptime in seconds."""
```

`GET /admin/performance/json` exposes this as:

```json
"uptime_seconds": 3600.5
```

This field is considered stable and should not change semantics in future versions.

#### 5.5.3 Optional CPU and memory

`performance_monitor.py` provides `get_system_stats()` using `psutil`, which returns fields such as:

- `cpu_percent`
- `memory_mb`
- `memory_percent`
- Disk IO counters
- Open file count
- Thread count

These fields are currently used for human readable reports in `performance_report()` and for debugging during load tests. They are not yet wired into `GET /admin/performance/json`.

If and when CPU and memory metrics are exposed to the admin UI, the recommended schema is:

```json
"resources": {
  "uptime_seconds": 3600.5,
  "cpu_percent": 12.5,
  "memory_percent": 48.3
}
```

At that point `uptime_seconds` can either remain as a top level field or live only under `resources`, but the change should be coordinated with `docs/API.md` and the admin dashboard implementation.

---

## 6. JSON APIs and response shapes

### 6.1 `GET /admin/performance/json` (current canonical endpoint)

**Route path:** `/admin/performance/json`
**Blueprint:** `admin_bp` in `backend/app/admin/routes.py`
**Purpose:** Provide a compact snapshot for the HTML admin dashboard and simple JSON clients.

Current response structure:

```json
{
  "cache_hit_rate": 93.0,
  "uptime_seconds": 3600.5,
  "database": {
    "total_queries": 420,
    "avg_per_request": 4.2,
    "max_per_request": 12,
    "count": 100
  },
  "ratings_post": {
    "p95_latency_ms": 42.7,
    "avg_latency_ms": 31.2,
    "request_count": 58
  },
  "endpoints": {}
}
```

Notes:

- `cache_hit_rate` is a percentage between 0 and 100
- `uptime_seconds` is seconds since process start
- `database` is fully backed by current code
- `ratings_post` is fully backed by current code
- `endpoints` is currently an empty object and is reserved for future per route metrics as described in section 5.1

If `docs/API.md` currently lists `GET /admin/performance.json` as the JSON endpoint, the code and documentation should converge on `/admin/performance/json` as canonical, with `/admin/performance.json` treated as a possible future alias.

### 6.2 `GET /api/admin/performance/routes` (planned)

**Route path:** `/api/admin/performance/routes`
**Purpose:** Provide a richer data source for SPA admin dashboards and advanced analytics.

This endpoint is not implemented yet, but its target shape is:

**Query parameters (optional):**

- `limit` (int, default 50)
  Maximum number of routes to return.
- `sort_by` (string, default `p95_ms`)
  One of `p95_ms`, `p99_ms`, `avg_ms`, `request_count`.
- `order` (string, default `desc`)
  `asc` or `desc`.

**Response shape:**

```json
{
  "routes": [
    {
      "route": "GET /",
      "endpoint": "main.index",
      "p50_ms": 12.3,
      "p95_ms": 25.4,
      "p99_ms": 40.7,
      "avg_ms": 15.8,
      "min_ms": 8.1,
      "max_ms": 51.2,
      "request_count": 134,
      "error_count": 2,
      "last_updated": "2025-12-09T17:30:15Z"
    }
  ]
}
```

Internally, this endpoint will:

- Use `PerformanceMetrics.endpoint_latencies` as the primary data source
- Or bridge to `PerformanceMonitor.route_stats` if that provides better granularity
- Apply a sorting and limiting step based on the query parameters

The exact internal source should be documented in `ARCHITECTURE.md` once implementation is in place.

---

## 7. Collection and exposure workflow

### 7.1 Recording metrics

The system records metrics at several points:

1. **Cache usage**

   - In `cache_manager.py`:

     - On successful cache read, call `get_metrics().record_cache_hit()`
     - On cache miss, call `get_metrics().record_cache_miss()`

2. **Database queries**

   - In the database access layer:

     - Track the number of queries executed per request
     - At the end of the request, append the count to `db_queries_per_request` and increment `total_db_queries`
     - These updates must hold `metrics.lock`

3. **Ratings POST**

   - In `backend/app/api/ratings.py`:

     - For `POST /api/ratings/<media_hash>`, measure duration
     - Append the duration in seconds to `ratings_post_latencies` under `metrics.lock`
     - Use the helper methods to report p95 and average in milliseconds

4. **Route latency (planned admin integration)**

   - `PerformanceMonitor` already captures route times via `flask_route_monitor(app)`
   - For admin metrics, one of the following is recommended:

     - Option A: Introduce `PerformanceMetrics.record_endpoint_latency(route, duration, is_error)` and call it from a lightweight Flask hook
     - Option B: Periodically copy summary data from `PerformanceMonitor.route_stats` into `PerformanceMetrics`

   Until this is implemented, `endpoints` in `/admin/performance/json` remains empty.

5. **Uptime**

   - `PerformanceMetrics.start_time` is set at construction time
   - Uptime is computed on demand without extra hooks

### 7.2 Reading metrics

1. **HTML dashboard**

   - `GET /admin/performance` in `backend/app/admin/routes.py`:

     ```python
     metrics = get_metrics()
     return render_template(
         "admin/performance.html",
         cache_hit_rate=metrics.get_cache_hit_rate(),
         uptime_seconds=metrics.get_uptime_seconds(),
         ratings_post_p95=metrics.get_ratings_post_p95_latency(),
         ratings_post_avg=metrics.get_ratings_post_avg_latency(),
         ratings_post_count=metrics.get_ratings_post_count()
     )
     ```

   - The template is responsible for:

     - Formatting percentages and durations
     - Applying thresholds and color coding defined in `PERFORMANCE.md`

2. **JSON snapshot**

   - `GET /admin/performance/json` builds the JSON payload using:

     - `metrics.get_cache_hit_rate()`
     - `metrics.get_uptime_seconds()`
     - Raw database fields aggregated under `metrics.lock`
     - Ratings POST helper methods

   - `endpoints` is currently hard coded to `{}` as a placeholder for future route metrics.

3. **Future SPA endpoints**

   - `GET /api/admin/performance/routes` and related admin APIs described in `API.md` will:

     - Read directly from `PerformanceMetrics` or a bridged view of `PerformanceMonitor`
     - Return data structured according to the schemas in section 5

---

## 8. Relationship to other docs

- `PERFORMANCE.md`

  - Defines latency targets for key routes such as `GET /`, `GET /watch/<filename>`, and `POST /api/ratings/<media_hash>`
  - Specifies thresholds for status classification:

    - Example: p95 less than 50 ms is good, 50 to 200 ms is warning, above 200 ms is poor
  - These thresholds should inform color coding and badges in the admin UI

- `ARCHITECTURE.md`

  - Documents:

    - Where `PerformanceMetrics` lives in the backend
    - How `backend/app/admin/routes.py` exposes metrics to templates and JSON
    - Where `performance_monitor.py` sits as an optional layer for diagnostics and testing

- `API.md`

  - Lists:

    - `GET /admin/performance`
    - `GET /admin/performance/json`
    - Planned `/api/admin/performance/...` endpoints
  - Should reference this file for detailed field level schemas

`PERFORMANCE_MONITORING.md` is the single reference for metric field names, aggregation windows, and response shapes. Other docs should refer to it instead of redefining these details.

---

## 9. Implementation checklist

When updating or extending performance monitoring, ensure the following:

1. `PerformanceMetrics` remains the source of truth for admin metrics.
2. `get_cache_hit_rate()` continues to return a percentage between 0 and 100.
3. Ratings POST metrics:

   - Record durations in seconds
   - Return p95 and average in milliseconds
   - Use a window size of at most 100 samples
4. Database metrics:

   - Maintain `db_queries_per_request` and `total_db_queries` under `metrics.lock`
   - Use the schema in section 5.4 for JSON output
5. Route metrics:

   - When implemented, populate `endpoints` in `/admin/performance/json` and support `GET /api/admin/performance/routes` using the schema in section 5.1
6. Resource metrics:

   - Keep `uptime_seconds` accurate and stable
   - Only add CPU and memory fields once `get_system_stats()` is wired into the admin layer and `API.md` is updated
7. Admin UI:

   - Reads data only through:

     - `GET /admin/performance` template context
     - `GET /admin/performance/json` or future `/api/admin/performance/...` endpoints
   - Uses thresholds from `PERFORMANCE.md` for visual status
