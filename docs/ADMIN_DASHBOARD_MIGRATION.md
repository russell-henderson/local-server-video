# Admin Dashboard Migration Guide

This document provides a step by step guide to introduce the admin performance dashboard into an existing Local Video Server deployment.

It describes prerequisites, ordered migration steps, verification checkpoints, and rollback guidance.

---

## Prerequisites

Before starting:

* [ ] `docs/ADMIN_DASHBOARD.md` exists and is marked complete.
* [ ] `docs/ADMIN_DASHBOARD_IMPL_NOTES.md` exists and matches the current code state.
* [ ] Performance metrics collection is implemented as described in `docs/PERFORMANCE_MONITORING.md`.
* [ ] The ratings endpoint and preview system are running without known critical issues.
* [ ] IP allowlist or equivalent protection for admin routes is configured or planned.
* [ ] You have a test environment that matches production closely enough to validate performance changes.

---

## Migration Steps

### Step 1: Add backend admin endpoints

**Action**

* Implement and register the new admin endpoints described in `ADMIN_API_SPEC.md` using the patterns in `ADMIN_DASHBOARD_BACKEND.md`.

**Files to modify**

* `main.py`
* `admin/__init__.py` (new)
* `admin/routes.py` (new)
* `performance_monitor.py` (extend with snapshot helpers if needed)

**Code to add**

* Admin blueprint registration in `main.py`.
* Route handlers for:

  * `/admin/performance`
  * `/admin/performance/json`
  * `/api/admin/performance/routes`
  * `/api/admin/performance/workers`
* Helper functions in `performance_monitor.py` that produce the JSON payloads.

**Verify**

* Run unit tests:

  * Add and run tests for admin routes as described in `ADMIN_DASHBOARD_TESTING.md`.
* Manually hit JSON endpoints using `curl`:

  * `curl http://localhost:5000/admin/performance/json`
  * `curl http://localhost:5000/api/admin/performance/routes`
  * `curl http://localhost:5000/api/admin/performance/workers`
* Confirm responses match the schemas defined in `ADMIN_API_SPEC.md`.

**Rollback**

* Comment out or remove the admin blueprint registration from `main.py`.
* Remove or ignore `admin/` and any new imports.
* Revert `performance_monitor.py` to the previous version.

---

### Step 2: Add admin dashboard template and JavaScript

**Action**

* Create the template and JavaScript files that implement the dashboard UI.

**Files to modify or create**

* Create `templates/admin/performance.html`.
* Create `static/js/admin_dashboard.js`.
* Optionally create `static/css/admin_dashboard.css`.
* Update `templates/base.html` (or equivalent) to add a navigation link to `/admin/performance`.

**Code to add**

* HTML structure described in `ADMIN_DASHBOARD_FRONTEND.md`.
* JavaScript for:

  * Fetching metrics.
  * Rendering KPI cards.
  * Populating tables.
  * Drawing charts with Chart.js.
  * Handling cache refresh.

**Verify**

* Start the server in development mode.
* Open `/admin/performance` in a browser.
* Confirm:

  * Page loads without template errors.
  * Global KPIs show numeric values.
  * Chart placeholders appear.
  * No errors are logged in the browser console.

**Rollback**

* Remove `performance.html` from `templates/admin/` or comment out its link in the navigation.
* Remove or comment out the `<script src="...admin_dashboard.js">` line.
* Delete or revert `admin_dashboard.js`.

---

### Step 3: Wire metrics to live data

**Action**

* Ensure that the admin dashboard fetches live metrics instead of stub or mocked data.

**Files to modify**

* `performance_monitor.py`
* `static/js/admin_dashboard.js`

**Code considerations**

* Replace any placeholder metrics in `performance_monitor.py` with real aggregation logic.
* Remove any hard coded data in `admin_dashboard.js` used for initial prototyping.

**Verify**

* Restart the server.
* Interact with the app:

  * Play previews.
  * Rate videos.
* Confirm that:

  * Counts and latency values in the dashboard change over time.
  * Error rate reflects real failures if you trigger them in a controlled way.

**Rollback**

* Temporarily revert to stubbed metrics if production metrics storage is not ready.
* Keep the dashboard behind a feature flag if necessary.

---

### Step 4: Integrate cache status and refresh

**Action**

* Connect the cache widget to the existing cache endpoints.

**Files to modify**

* `static/js/admin_dashboard.js`
* `templates/admin/performance.html` if you need to adjust the widget layout.

**Code to add**

* Calls to:

  * `GET /admin/cache/status`
  * `POST /admin/cache/refresh`

**Verify**

* Load `/admin/performance`.
* Confirm:

  * Cache usage percentage displays correctly.
  * "Refresh cache" button triggers a refresh and updates status.
  * No unexpected spikes in CPU or disk usage when testing refresh.

**Rollback**

* Hide or disable the cache widget in `performance.html`.
* Remove or comment out calls to cache endpoints in `admin_dashboard.js`.

---

### Step 5: Harden security and network behavior

**Action**

* Make sure admin endpoints are not exposed to untrusted clients.

**Files to update**

* Configuration files that control IP allowlist or reverse proxy settings.
* Documentation:

  * Update `IMPLEMENTATION.md` or deployment notes if needed.

**Verify**

* Test access from:

  * Local machine where the server runs.
  * Trusted LAN device.
  * Non trusted device if available.
* Confirm that:

  * Admin endpoints respond only from trusted locations.
  * Blocked clients receive `403` or equivalent response.

**Rollback**

* Tighten firewall rules temporarily.
* Remove or adjust the admin blueprint registration if needed.

---

### Step 6: Validate performance impact

**Action**

* Ensure that the metrics endpoints themselves do not degrade server performance.

**Files to reference**

* `PERFORMANCE.md`
* `PERFORMANCE_MONITORING.md`
* `ADMIN_API_SPEC.md`

**Verification steps**

* Use a simple load tool or script to:

  * Hit `/admin/performance/json` at realistic intervals.
  * Watch CPU and memory usage.
* Verify:

  * No significant increase in response time for user facing pages.
  * Admin endpoints stay within target latency thresholds.

**Rollback**

* Reduce polling frequency in `admin_dashboard.js`.
* Add short lived caching in `performance_monitor.py`.

---

## Testing Checklist

After migration, confirm the following:

* [ ] All new tests for admin endpoints pass.
* [ ] Existing tests still pass without modification.
* [ ] `/admin/performance` loads correctly in a browser.
* [ ] `/admin/performance/json` returns valid JSON and correct fields.
* [ ] `/api/admin/performance/routes` lists expected routes and metrics.
* [ ] `/api/admin/performance/workers` reflects background worker state.
* [ ] Cache status and refresh behave as intended.
* [ ] Admin endpoints are reachable only from trusted clients.
* [ ] The dashboard does not introduce noticeable latency for user facing routes.

---

## Troubleshooting

Common issues and fixes:

* **Issue**: `/admin/performance` returns 404
  **Check**: Ensure the admin blueprint is registered and the route path is correct.

* **Issue**: JSON endpoints return 500
  **Check**: Verify that `performance_monitor.py` does not assume metrics exist when they do not. Add defensive checks for empty data.

* **Issue**: Charts show zeros or do not update
  **Check**: Confirm that `admin_dashboard.js` is loaded, that `loadDashboardData` is called, and that CORS is not blocking requests in your deployment.

* **Issue**: Admin endpoints time out under load
  **Check**: Add short lived snapshot caching inside `performance_monitor.py` and reduce poll frequency on the frontend.

Document any environment specific fixes in `ADMIN_DASHBOARD_IMPL_NOTES.md` for future reference.
