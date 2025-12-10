=== NEW FILE: docs/ADMIN_DASHBOARD_TESTING.md ===

# Admin Dashboard Testing Guide

This document defines the testing strategy for the admin performance dashboard.

It covers:

* Required coverage levels.
* Backend and frontend unit tests.
* Integration and end to end scenarios.
* Performance and accessibility checks.

Use this guide together with `QA_TESTING_GUIDE.md`, `ADMIN_API_SPEC.md`, and `ADMIN_DASHBOARD_BACKEND.md`.

---

## Test Coverage Requirements

Minimum goals:

* Backend admin endpoints:

  * 90 percent or higher line coverage for route handlers and metrics helpers.
* Frontend dashboard script:

  * Automated tests for core logic where practical.
  * Manual verification checklist for UI behavior.
* Integration scenarios:

  * All admin endpoints exercised in at least one end to end flow.

---

## Unit Tests

### Backend Tests

Create a dedicated test file, for example:

* `tests/test_admin_performance_routes.py`

Recommended tests:

1. **`/admin/performance/json` basic success**

   * Arrange:

     * Seed metrics for a simple scenario.
   * Act:

     * `client.get("/admin/performance/json")`
   * Assert:

     * Status `200`.
     * Response JSON has keys:

       * `generated_at`
       * `server`
       * `global`
       * `cache`
       * `workers`
       * `status`.
     * `global.p95_latency_ms` is a number.

2. **`/admin/performance/json` respects query parameters**

   * Test `window_seconds` with allowed values.
   * Test `include_routes=true` yields non null `routes`.
   * Test `include_workers=false` yields an empty or minimal `workers` object.

3. **`/api/admin/performance/routes` sorting and limiting**

   * Seed different route metrics.
   * Request with:

     * `sort_by=p95_latency_ms&order=desc`
   * Assert:

     * Returned list is sorted.
     * `len(routes)` respects `limit`.

4. **`/api/admin/performance/workers` healthy and disabled cases**

   * With workers:

     * Ensure `worker_count` > 0.
     * Ensure at least one queue entry.
   * Without workers:

     * Simulate no worker configuration.
     * Endpoint returns `worker_count` 0 and `status` `"disabled"`.

5. **Error paths**

   * Invalid `window_seconds`:

     * Option 1: ensure it falls back to default.
     * Option 2: if you choose strict behavior, ensure `400` with `INVALID_PARAMETER`.

Example pytest pattern:

```python
def test_admin_performance_json_basic(client):
  response = client.get("/admin/performance/json")
  assert response.status_code == 200
  data = response.get_json()
  assert "global" in data
  assert isinstance(data["global"]["p95_latency_ms"], (int, float))
```

Use fixtures to seed metrics if possible.

---

### Frontend Tests

If you have a JavaScript test framework in place (for example Vitest or Jest for small modules), add tests for pure functions in `admin_dashboard.js` such as:

* Formatting helpers for KPI values.
* Mapping status strings to CSS class names.

If you do not have a JavaScript test harness set up, focus on manual tests and keep `admin_dashboard.js` simple and deterministic.

---

## Integration Tests

Integration tests ensure that the full admin stack behaves correctly:

* Routes are registered.
* Templates render.
* JSON endpoints and UI work together.

Recommended integration checks:

1. **Admin page loads**

   * Use a browser based tool such as Playwright or Cypress, or a manual checklist.
   * Steps:

     * Navigate to `/admin/performance`.
     * Confirm HTTP 200 and basic HTML rendered.
     * Verify that KPI cards show numbers instead of placeholders within a few seconds.

2. **Metrics user journey**

   * Trigger real app activity:

     * Load a video preview.
     * Submit a rating.
   * After a short delay:

     * Refresh the dashboard.
     * Confirm:

       * `request_count` for relevant routes increases.
       * Latency values change.

3. **Workers and queues**

   * Queue one or more background jobs.
   * Confirm:

     * `/api/admin/performance/workers` reports the jobs as pending or in progress.
     * Dashboard queue table reflects this.

4. **Cache operations**

   * Open the dashboard.
   * Note reported cache usage.
   * Click "Refresh cache".
   * Confirm:

     * Endpoint returns `success: true`.
     * Cache usage updates if relevant.

Document integration steps in `QA_TESTING_GUIDE.md` if they need to become part of regular regression runs.

---

## Performance Tests

The admin dashboard itself should be light, but metrics aggregation can be expensive if not implemented carefully.

Basic performance validation:

1. **Latency of metrics endpoints**

   * Using a simple script or tool, send:

     * 20 requests to `/admin/performance/json`.
     * 20 requests to `/api/admin/performance/routes`.
   * Record:

     * Median and p95 response times.
   * Targets:

     * Median under 100 ms.
     * p95 under 250 ms in a typical development or staging environment.

2. **Impact on user facing routes**

   * With the dashboard open and polling every 10 seconds:

     * Measure response times for a typical video preview and rating submission.
   * Confirm:

     * No noticeable increase compared to baseline without the dashboard.

If performance issues are detected:

* Consider caching the snapshot in `performance_monitor.py`.
* Reduce polling frequency in `admin_dashboard.js`.

---

## Accessibility Tests

Even though the admin dashboard is internal, it should meet basic accessibility expectations and follow WCAG principles alongside the rest of the app.

Checklist:

* [ ] All actionable controls (buttons, links) are reachable with keyboard only navigation.
* [ ] Each button has an accessible label that explains its action.
* [ ] Tables include `<thead>` and column headers for screen readers.
* [ ] Charts include:

  * Clear titles.
  * Textual summaries of key values for users who cannot see the chart.
* [ ] Color alone is not the only indicator of status.

  * For example, status text such as `"good"`, `"warning"`, `"critical"` is also shown.

Tools:

* Use browser dev tools accessibility panel.
* Optionally run Lighthouse or similar audits and verify there are no critical issues specific to the admin page.

---

## Example Test Code Snippet

Example of a pytest integration style test that verifies both routing and basic schema:

```python
def test_admin_performance_endpoints_wired(client):
  # HTML page
  html_response = client.get("/admin/performance")
  assert html_response.status_code == 200
  assert b"Admin Performance Dashboard" in html_response.data

  # JSON snapshot
  json_response = client.get("/admin/performance/json")
  assert json_response.status_code == 200
  data = json_response.get_json()
  assert isinstance(data["global"]["p95_latency_ms"], (int, float))

  # Routes table
  routes_response = client.get("/api/admin/performance/routes")
  assert routes_response.status_code == 200
  routes_data = routes_response.get_json()
  assert "routes" in routes_data
  assert isinstance(routes_data["routes"], list)

  # Workers
  workers_response = client.get("/api/admin/performance/workers")
  assert workers_response.status_code == 200
  workers_data = workers_response.get_json()
  assert "worker_count" in workers_data
```

---

## Regression and Release Gates

Before releasing a version that includes the admin dashboard:

* [ ] All new backend and frontend tests pass.
* [ ] No regressions in existing test suites.
* [ ] Manual smoke tests on `/admin/performance` pass.
* [ ] Performance targets for metrics endpoints are met.
* [ ] Accessibility checklist items for the admin page are confirmed.

Record any deviations from these gates and their justification in the relevant release notes under `docs/releases`
