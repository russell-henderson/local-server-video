# Admin Dashboard Implementation Notes

Purpose: Capture practical implementation details for the admin performance dashboard.  
This file connects the UI spec in `docs/ADMIN_DASHBOARD.md` to real endpoints, templates, and metrics.

Source of truth for layout and visuals: `docs/ADMIN_DASHBOARD.md`  
Source of truth for metric shapes and field names: `docs/PERFORMANCE_MONITORING.md`  
Endpoint contracts: `docs/API.md`  
Backend wiring: `docs/IMPLEMENTATION.md`, `docs/ARCHITECTURE.md`

Use this file for implementation notes and low level checklists only.  
Do not duplicate the full UI spec here.

---

## 1. Scope

The admin dashboard covers:

- Overall server health and uptime.
- Cache efficiency.
- Request latency and route performance.
- Database load and query volume.
- Ratings specific performance.

Primary endpoints:

- `GET /admin/performance`  
  Renders the dashboard HTML from `templates/admin/performance.html`.

- `GET /admin/performance/json`  
  Returns a JSON snapshot that the dashboard and external tools consume.

Planned but not yet required:

- `GET /api/admin/performance/routes`  
  Machine friendly per route metrics for future use.

These endpoints must follow the schemas in `docs/PERFORMANCE_MONITORING.md`.

---

## 2. Template and layout wiring

Template file:

- `templates/admin/performance.html`

Key expectations from the UI spec:

- Top row of KPI cards that displays:
  - Overall health indicator.
  - Cache hit rate.
  - Ratings p95 latency band.
  - Error rate summary.
  - Uptime summary.

- Summary panels that group:
  - Cache and index health.
  - Database load.
  - Background worker status.

- Route performance table:
  - Sortable by latency and error rate.
  - Shows p50 and p95 latency per route.
  - Shows request and error counts.

- Efficiency charts:
  - Sparklines or small charts for latency, cache hit rate, database queries, and error rate.

Implementation notes:

- Use the JSON snapshot from `/admin/performance/json` as the single data source for charts and tables.
- Keep Jinja logic minimal. Prefer small JavaScript helpers in `static/` to render charts and dynamic state.
- Respect WCAG AA and the global design tokens defined in `docs/UI.md`.

---

## 3. Metrics data flow

High level pipeline:

1. Request enters Flask.
2. `performance_monitor.py` and `PerformanceMetrics` record:
   - Route latency.
   - Database query count.
   - Ratings specific timings when relevant.
3. Route handler completes.
4. `PerformanceMetrics` keeps windowed samples in memory.
5. `/admin/performance.json` assembles a summary document that matches `docs/PERFORMANCE_MONITORING.md`.

Key components:

- `backend/app/admin/performance.py`
  - Contains `PerformanceMetrics` and related helpers.

- `performance_monitor.py`
  - Provides decorators and request hooks that feed metrics into `PerformanceMetrics`.

- `backend/app/admin/routes.py`
  - Builds the snapshot for `/admin/performance.json`.
  - Passes data into `templates/admin/performance.html`.

Implementation guardrails:

- Keep `PerformanceMetrics` lightweight and in memory only.
- Use numeric types that match the monitoring schema (for example milliseconds for latency).
- Avoid expensive aggregation inside request handlers. Pre aggregate where possible.

---

## 4. JSON snapshot structure

`/admin/performance/json` should return a document that logically mirrors the dashboard sections.  
Exact field names and types are defined in `docs/PERFORMANCE_MONITORING.md`.  

Expected top level keys (conceptual):

- `summary`
  - `uptime_seconds`
  - `overall_status`
  - `health_reasons` or similar explanation fields.

- `cache`
  - `hit_rate`
  - `hits`
  - `misses`
  - optional window information if available.

- `database`
  - `queries_per_second`
  - `avg_queries_per_request`
  - `recent_query_counts`

- `ratings_post`
  - `count`
  - `p95_ms`
  - `avg_ms`

- `routes`
  - Map keyed by route identifier, where each entry contains:
    - `p50_ms`
    - `p95_ms`
    - `request_count`
    - `error_count`

- `charts`
  - Simple time series arrays for latency, cache hit rate, and error rate.

Implementation notes:

- When a metric is not available yet, return a clear placeholder such as `null` or an empty array.  
  The UI should treat this as "no data" rather than an error.
- Maintain stable field names.  
  Any rename must be reflected in `docs/PERFORMANCE_MONITORING.md` and the UI code.

---

## 5. Route performance expansion

Initial implementation can keep `routes` minimal. For example:

- Start with a small set of core routes:
  - `/`
  - `/watch/<id>`
  - `/api/ratings`
  - `/api/tags/*`

- Store per route statistics in `PerformanceMonitor` and feed them into `PerformanceMetrics`.

Future expansion:

- Add a dedicated `/api/admin/performance/routes` endpoint that exposes the same `routes` data in a more detailed machine friendly format.
- Allow filtering by route prefix, method, and time window.

All route metrics must still conform to the schemas in `docs/PERFORMANCE_MONITORING.md`.

---

## 6. Testing and verification

Testing goals:

- `/admin/performance` returns HTTP 200 and renders without template errors.
- `/admin/performance/json` returns HTTP 200 with a JSON body that matches the monitoring schema.
- Cache and ratings metrics update when:
  - `/api/ratings` is called.
  - Cache interactions occur in `cache_manager.py`.

Suggested tests:

- Admin routes:
  - Request `/admin/performance` and assert HTML contains expected placeholders or labels.
  - Request `/admin/performance/json` and validate keys and types.

- Metrics behavior:
  - Call the ratings API multiple times and assert:
    - `ratings_post.count` increases.
    - `ratings_post.p95_ms` is greater than zero.
  - Hit gallery and watch routes and assert that:
    - `routes` contains entries for those paths.
    - Latency fields are present.

- Error handling:
  - Simulate an exception in a monitored route and assert error counts increase in route metrics.

Keep tests focused on behavior that the dashboard actually consumes.

---

## 7. Implementation checklist

This checklist mirrors and extends the admin dashboard section in `docs/TODOS.md`.  
Keep it in sync when you complete work.

- [ ] Confirm `PerformanceMetrics` exposes all fields required by `docs/PERFORMANCE_MONITORING.md`.
- [ ] Ensure `performance_monitor.py` records route level timings in a way that `PerformanceMetrics` can consume.
- [ ] Implement `/admin/performance.json` using only the monitoring schema fields.
- [ ] Implement `templates/admin/performance.html` layout according to `docs/ADMIN_DASHBOARD.md`.
- [ ] Connect the template to `/admin/performance.json` as its single data source for:
  - KPI cards.
  - Summary panels.
  - Route performance table.
  - Efficiency charts.
- [ ] Add at least one real KPI card backed by live data (for example cache hit rate or ratings p95 latency).
- [ ] Add tests that cover:
  - Successful rendering of `/admin/performance`.
  - Schema compliance of `/admin/performance/json`.
  - Basic metric updates through typical user actions.

When you complete an item here, also update the matching entry in `docs/TODOS.md`.

---

## 8. References

Use these documents together for admin work:

- UI spec: `docs/ADMIN_DASHBOARD.md`
- Implementation notes: `docs/ADMIN_DASHBOARD_IMPL_NOTES.md` (this file)
- Metric schemas: `docs/PERFORMANCE_MONITORING.md`
- Performance goals and thresholds: `docs/PERFORMANCE.md`
- API contracts: `docs/API.md`
- Overall system implementation: `docs/IMPLEMENTATION.md`
