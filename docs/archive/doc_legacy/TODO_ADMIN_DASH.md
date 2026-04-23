# TODO_ADMIN_DASH.md

## Status (Dec 10, 2025)

- Frontend (Next/Tailwind) is live on port 3000. CSP header removed to avoid eval blocks.
- Proxies in dashboard: `/api/performance/json|routes|workers|active`, `/api/system/storage`, `/api/cache/status`, `/api/tags/popular`.
- Storage donut shows Videos/Images/Other/Free with legend (statfs).
- Active Streams + Now Playing use `/api/admin/performance/active`; **video-server must be rebuilt/restarted to enable this endpoint**. Otherwise the proxy returns empty.
- Pulse/Golden Hour read live perf snapshots (rpm + p95).
- Link Sentinel still stub; shows cache status only (no link crawl yet).
- Sidebar links wired: dashboard, video library, gallery, links, Flask admin perf.

### Next actions
- Rebuild/restart `video-server` so `/api/admin/performance/active` exists (needed for Active Streams/Now Playing IPs): `docker-compose build video-server && docker-compose up -d video-server`.
- Rebuild/restart `admin-dashboard`: `docker-compose build admin-dashboard && docker-compose up -d admin-dashboard`.
- Implement Link Sentinel backend probe to crawl bookmarks/gallery/embeds and return failures.
- If true “currently playing” is needed beyond recent requests, add backend tracking of active byte-range streams and expose in `/api/admin/performance/active`.

Admin Dashboard Implementation Checklist

References:

- `docs/ADMIN_DASHBOARD.md` - UI specification
- `docs/ADMIN_API_SPEC.md` - API contracts
- `docs/ADMIN_DASHBOARD_BACKEND.md` - Backend guide
- `docs/ADMIN_DASHBOARD_FRONTEND.md` - Frontend guide
- `docs/ADMIN_DASHBOARD_MIGRATION.md` - Integration steps
- `docs/ADMIN_DASHBOARD_TESTING.md` - Testing requirements

---

## Phase 1: Backend Foundation

### 1.1 Metrics Infrastructure

- [ ] Verify `performance_monitor.py` tracks route latency, errors, request counts
- [ ] Verify `PerformanceMetrics` singleton stores windowed samples (15 min default)
- [ ] Add helper: `get_performance_snapshot(window_seconds, include_routes, include_workers) -> dict`
- [ ] Add helper: `get_route_metrics(window_seconds, sort_by, order, limit) -> dict`
- [ ] Add helper: `get_worker_metrics() -> dict`
- [ ] Ensure all helpers return schema from `ADMIN_API_SPEC.md` (PerformanceSnapshot, RouteMetrics, WorkerSummary)

### 1.2 Admin Endpoints

- [ ] Create `admin/__init__.py` with `admin_bp` Blueprint
- [ ] Create `admin/routes.py` with route handlers
- [ ] Implement `GET /admin/performance` - renders `templates/admin/performance.html`
- [ ] Implement `GET /admin/performance/json` - returns PerformanceSnapshot with query params: `window_seconds`, `include_routes`, `include_workers`
- [ ] Implement `GET /api/admin/performance/routes` - returns sorted route table with query params: `window_seconds`, `sort_by`, `order`, `limit`
- [ ] Implement `GET /api/admin/performance/workers` - returns worker/queue status
- [ ] Register `admin_bp` in `main.py`
- [ ] Add query parameter parsing helpers (`_parse_window_seconds`, `_parse_int`)
- [ ] Add error handling for invalid params (return 400 with `INVALID_PARAMETER`)

### 1.3 Backend Testing

- [ ] Create `tests/test_admin_performance_routes.py`
- [ ] Test `/admin/performance/json` returns 200 and valid schema
- [ ] Test `window_seconds` parameter (300, 900, 3600)
- [ ] Test `include_routes=true` returns non-null routes array
- [ ] Test `include_workers=false` returns minimal workers object
- [ ] Test `/api/admin/performance/routes` sorting (by p95, error_rate, request_count)
- [ ] Test `/api/admin/performance/routes` respects `limit` parameter
- [ ] Test `/api/admin/performance/workers` with workers enabled/disabled
- [ ] Test error cases (invalid window_seconds, missing metrics)
- [ ] Verify 90%+ line coverage for admin routes

---

## Phase 2: Frontend Template & Assets

### 2.1 Template Structure

- [ ] Create `templates/admin/` directory
- [ ] Create `templates/admin/performance.html` extending `base.html`
- [ ] Add header with title "Admin Performance Dashboard" and refresh button
- [ ] Add KPI cards container (`#admin-kpis`) for 4 cards
- [ ] Add charts section with canvases: `#latency-chart`, `#traffic-chart`
- [ ] Add routes table (`#routes-table`) with thead/tbody
- [ ] Add workers panel (`#workers-panel`) with summary div and queues table (`#queues-table`)
- [ ] Add cache panel (`#cache-panel`) with usage text, progress bar, refresh button, status text
- [ ] Include Chart.js from CDN: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- [ ] Include dashboard script: `<script src="{{ url_for('static', filename='js/admin_dashboard.js') }}"></script>`

### 2.2 JavaScript Implementation

- [ ] Create `static/js/admin_dashboard.js`
- [ ] Define API endpoints object with URLs for: `performanceJsonUrl`, `routesUrl`, `workersUrl`, `cacheStatusUrl`, `cacheRefreshUrl`
- [ ] Implement `fetchJson(url)` helper with error handling
- [ ] Implement `renderKpis(perfSnapshot)` - populates 4 KPI cards (global p95, ratings p95, error rate, cache usage)
- [ ] Implement `renderRoutesTable(routesPayload)` - populates table with route metrics
- [ ] Implement `renderWorkers(workersPayload)` - populates worker summary and queues table
- [ ] Implement `refreshCacheStatus()` - fetches and displays cache status
- [ ] Implement `handleCacheRefreshClick()` - POST to cache refresh, update UI
- [ ] Implement `renderLatencyChart(ctx, perfSnapshot)` - Chart.js bar chart for p50/p95/p99
- [ ] Implement `loadDashboardData(forceRoutes)` - orchestrates all fetch/render calls
- [ ] Implement `initDashboard()` - wire event listeners, initial load, start 10s polling
- [ ] Add error handling for failed fetches (show "Metrics unavailable" banner after N failures)

### 2.3 Styling (Optional)

- [ ] Create `static/css/admin_dashboard.css` if needed
- [ ] Add KPI card styles: `.admin-kpi`, `.admin-kpi--good`, `.admin-kpi--warning`, `.admin-kpi--critical`
- [ ] Add route table row styles: `.route-row--good`, `.route-row--warning`, `.route-row--poor`
- [ ] Add queue table row styles: `.queue-row--healthy`, `.queue-row--slow`, `.queue-row--stuck`
- [ ] Ensure responsive layout (cards stack on narrow screens)
- [ ] Follow design tokens from `docs/UI.md`

### 2.4 Navigation

- [ ] Add link to `/admin/performance` in main navigation or admin menu
- [ ] Ensure link is visible only to authorized users (if auth exists)

---

## Phase 3: Integration & Security

### 3.1 Connect to Live Data

- [ ] Replace any stub metrics in `performance_monitor.py` with real aggregation
- [ ] Remove hard-coded test data from `admin_dashboard.js`
- [ ] Test: interact with app (play videos, rate content) and verify dashboard updates
- [ ] Verify counts, latency values, and error rates reflect real activity

### 3.2 Cache Integration

- [ ] Verify existing `GET /admin/cache/status` endpoint works
- [ ] Verify existing `POST /admin/cache/refresh` endpoint works
- [ ] Wire cache widget in dashboard to call these endpoints
- [ ] Test cache refresh button triggers refresh and updates status

### 3.3 Security & Access Control

- [ ] Configure IP allowlist or reverse proxy auth for `/admin/*` routes
- [ ] Test: verify admin endpoints accessible from trusted LAN clients only
- [ ] Test: verify blocked clients receive 403 or connection refused
- [ ] Document access control setup in deployment notes or `IMPLEMENTATION.md`

### 3.4 Performance Validation

- [ ] Load test `/admin/performance/json` (20 requests, measure p50/p95)
- [ ] Target: p50 < 100ms, p95 < 250ms
- [ ] Monitor user-facing routes with dashboard polling active
- [ ] Confirm no noticeable latency increase on main app routes
- [ ] Add snapshot caching in `performance_monitor.py` if needed (2-5s TTL)
- [ ] Adjust frontend polling interval if backend strain detected

---

## Phase 4: Testing & Quality

### 4.1 Backend Unit Tests

- [ ] Run `pytest tests/test_admin_performance_routes.py`
- [ ] Verify all 9+ backend test cases pass
- [ ] Check coverage report: 90%+ on admin routes and helpers
- [ ] Fix any failing or flaky tests

### 4.2 Integration Tests

- [ ] Manual test: navigate to `/admin/performance`, verify page loads (200 status)
- [ ] Manual test: verify KPI cards show numbers within 5 seconds
- [ ] Manual test: trigger app activity (preview, rating), refresh dashboard, verify metrics update
- [ ] Manual test: queue background job, verify workers panel shows pending/in-progress
- [ ] Manual test: click "Refresh cache", verify success and status update
- [ ] Optional: automate with Playwright/Cypress if available

### 4.3 Accessibility Checks

- [ ] Keyboard navigation: tab through all buttons, links, table headers
- [ ] Verify all buttons have accessible labels
- [ ] Verify tables have `<thead>` with proper column headers
- [ ] Verify charts have text summaries or `aria-label`
- [ ] Verify status colors paired with text (not color-only indicators)
- [ ] Run Lighthouse or browser accessibility audit, fix critical issues

### 4.4 Performance Tests

- [ ] Metrics endpoint latency test (script or tool)
- [ ] Record median and p95 response times
- [ ] Confirm targets met (see 3.4)

---

## Phase 5: Documentation & Deployment

### 5.1 Update Documentation

- [ ] Update `docs/DOCS_INVENTORY.md` with new admin docs (if not already done)
- [ ] Update `docs/API.md` with links to `ADMIN_API_SPEC.md` for admin endpoints
- [ ] Update `docs/TODOS.md` to mark admin dashboard tasks complete
- [ ] Add admin dashboard section to `README.md` features list (if desired)

### 5.2 Deployment Prep

- [ ] Verify all new files committed: `admin/`, `templates/admin/`, `static/js/admin_dashboard.js`, docs
- [ ] Create release notes in `docs/releases/` describing admin dashboard feature
- [ ] Update `CHANGELOG.md` with version bump and admin dashboard addition
- [ ] Test deployment to staging environment
- [ ] Run smoke tests in staging (all Phase 4 manual tests)

### 5.3 Production Release

- [ ] Deploy to production following standard release process
- [ ] Verify `/admin/performance` accessible from admin workstation
- [ ] Monitor logs for errors related to admin endpoints (first 24h)
- [ ] Collect feedback from admin users on usability and performance
- [ ] Document any production-specific config in `IMPLEMENTATION.md`

---

## Phase 6: Future Enhancements (Post-MVP)

### 6.1 Advanced Features

- [ ] Add date range filters for charts (24h/7d/30d)
- [ ] Add route grouping by prefix (`/api/` vs `/admin/`)
- [ ] Add export functionality (CSV/JSON) for metrics snapshots
- [ ] Add action buttons for: reindex library, flush cache, backup database
- [ ] Add real-time updates via WebSockets (replace polling)

### 6.2 Extended Metrics

- [ ] Add storage metrics endpoint (`GET /api/admin/performance/storage`)
- [ ] Add error log endpoint (`GET /api/admin/performance/errors`)
- [ ] Track video-specific analytics (watch completion, seek patterns)
- [ ] Track gallery-specific analytics (most viewed images, group usage)

### 6.3 UI Improvements

- [ ] Add drag-and-drop card rearrangement
- [ ] Add preset layouts (Overview, Video Focus, Gallery Focus)
- [ ] Add user layout preferences (save/load)
- [ ] Add dark/light theme toggle for admin dashboard
- [ ] Add mobile-optimized layout for admin dashboard

---

## Completion Criteria

Admin dashboard is complete when:

- ✅ All Phase 1-4 tasks checked off
- ✅ All backend tests pass (90%+ coverage)
- ✅ Dashboard loads and displays live metrics
- ✅ Cache operations work correctly
- ✅ Security/access control verified
- ✅ Performance targets met
- ✅ Accessibility checklist complete
- ✅ Documentation updated
- ✅ Deployed to production successfully

---

## Quick Reference Commands

```bash
# Run backend tests
pytest tests/test_admin_performance_routes.py -v --cov=admin

# Start dev server
python main.py

# Access dashboard
http://localhost:5000/admin/performance

# Test JSON endpoint
curl http://localhost:5000/admin/performance/json?window_seconds=900&include_routes=true

# Load test (simple)
for i in {1..20}; do curl -w "%{time_total}\n" -o /dev/null -s http://localhost:5000/admin/performance/json; done
```
