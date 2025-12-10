````markdown
# Admin Dashboard Specification

This document defines the admin performance dashboard for Local Video Server.

It covers:

- Layout and visual structure.
- Component level design.
- Data bindings to backend metrics.
- How the dashboard uses `/admin/performance` and `/admin/performance.json`.
- How it will evolve with the planned `/api/admin/performance/...` endpoints.

This document builds on:

- `docs/ARCHITECTURE.md` for backend structure.
- `docs/API.md` for endpoint contracts.
- `docs/PERFORMANCE.md` for performance targets and thresholds.
- `docs/PERFORMANCE_MONITORING.md` for metric schemas.
- `docs/UI.md` for global UI patterns and themes.

`ADMIN_DASHBOARD.md` is the single source of truth for the admin dashboard UI.

---

## 1. Design goals

The admin dashboard should:

1. Give a fast at a glance view of server health.
2. Highlight cache efficiency, ratings latency, and database load.
3. Make slow or failing routes visible within seconds.
4. Use visual status indicators that match thresholds from `PERFORMANCE.md`.
5. Stay lightweight enough to run on local hardware without heavy overhead.

The visual style should be inspired by the reference image:

- Dark theme with soft gradients.
- Card based layout with rounded corners.
- Clear separation of sections.
- Compact but readable typography.
- Status badges with green, yellow, and red states.

The dashboard must:

- Render all core metrics with server side HTML only.
- Enhance itself with live updates and charts when JavaScript is available.
- Degrade gracefully if `/admin/performance.json` is unavailable.

---

## 2. Layout overview

The dashboard uses a three tier structure.

1. **Navigation shell**

   - Left sidebar with navigation.
   - Top bar with title, search, and user info.

2. **KPI card row**

   - Four primary metric cards:
     - Cache health.
     - Ratings latency.
     - Database load.
     - Uptime and status.

3. **Detail area**

   - Two main zones:
     - Metrics summary panels.
     - Route performance table and efficiency charts.

High level grid:

- Sidebar: fixed width column on the left.
- Main content: single scrollable column on the right.
- Within main content:
  - Row 1: 4 equal width KPI cards on wide screens, wrapping to 2 x 2 cards on medium screens and a single column on small screens.
  - Row 2: 3 summary panels.
  - Row 3: full width route performance table and small charts.

---

## 3. Data sources

### 3.1 Primary endpoints

The dashboard uses these endpoints.

- `GET /admin/performance`  
  Server rendered HTML dashboard. Provides initial values for all metrics through Jinja2 context variables.

- `GET /admin/performance/json`  
  JSON snapshot of metrics, used by JavaScript for live updates and charts.

The JSON schema is defined in `PERFORMANCE_MONITORING.md`. At minimum it provides:

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
````

Server side rendering uses the same underlying `PerformanceMetrics` singleton as the JSON endpoint so that values match.

### 3.2 Future admin APIs

The dashboard is also the main consumer for planned admin APIs such as:

* `GET /api/admin/performance/routes`
  Returns an array of per route metrics, including p50, p95, p99, average, error counts, and request counts.

These endpoints are documented in `docs/API.md` and use schemas from `docs/PERFORMANCE_MONITORING.md`. The dashboard must be written so that the route table can switch from metrics embedded in `/admin/performance.json` to `GET /api/admin/performance/routes` without changing the visual layout.

### 3.3 Client side sampling for charts

For charts that show trends over time, the dashboard should:

* Poll `GET /admin/performance.json` every 5 to 15 seconds.
* Store the latest N samples in memory, for example N = 60.
* Render charts from this client side buffer only.
* Avoid writing time series data back to the server.

This keeps the backend simple but still allows visual trend indicators for cache efficiency and latency.

---

## 4. Component model

The dashboard is described as a set of conceptual components. In code, these map to:

* Jinja2 partials for HTML structure.
* CSS rules in `static/css/admin-dashboard.css` (or similar).
* Small JavaScript modules in `static/js/admin-dashboard.js` for polling and charts.

TypeScript style interfaces below describe the expected data shape for each component. They are documentation only.

---

## 4.1 Shell components

### 4.1.1 `AdminShell`

**Purpose**

Defines the page frame for all admin pages, including the performance dashboard.

**Structure**

* Left sidebar with:

  * Logo area or app name.
  * Navigation items:

    * Dashboard (active on this page).
    * Library.
    * Performance.
    * Logs and errors.
    * Settings.
  * Optional logout link near the bottom.

* Top bar with:

  * Page title: "Admin Dashboard".
  * Search box (placeholder in v1, can be wired to route search later).
  * User avatar and label such as "Local Admin".

**Data requirements**

The shell uses primarily static values in v1. Optional future dynamic values:

* Logged in user name or email if authentication is added.
* Hostname or server label.

**Accessibility**

* The sidebar should be marked as a `nav` region.
* The main content should use `role="main"` and an `h1` heading.
* Active navigation item should have `aria-current="page"`.

### 4.1.2 `DashboardGrid`

**Purpose**

Provides a consistent card grid inside the shell.

**Structure**

* First row: 4 KPI card slots.
* Second row: 3 summary panel slots.
* Third row:

  * Left: route performance table.
  * Right: vertical stack of efficiency charts.

**Implementation**

* Jinja2 template that loops over card definitions.
* CSS uses CSS Grid or Flexbox with gap spacing.
* On small screens, cards stack vertically.

---

## 4.2 KPI cards

KPI cards show the most important metrics for a quick scan.

Each KPI card includes:

* A title.
* A main numeric value.
* Optional secondary value such as a trend.
* A status indicator using colors and text.

Status levels are defined by thresholds in `PERFORMANCE.md`. The cards should not hard code numeric values; they should call shared helper functions that map metrics to status keywords.

Common interface:

```ts
type StatusLevel = "good" | "warning" | "poor";

interface KpiCardProps {
  title: string;
  primaryLabel: string;
  primaryValue: string;
  secondaryLabel?: string;
  secondaryValue?: string;
  status: StatusLevel;
}
```

The following sections describe card specific bindings.

### 4.2.1 `CacheHealthCard`

**Purpose**

Show overall cache effectiveness.

**Data binding**

From `/admin/performance.json`:

* `cache_hit_rate` (percentage 0 to 100).

**Derived props**

```ts
interface CacheHealthCardProps {
  hitRatePercent: number;  // cache_hit_rate
  status: StatusLevel;     // derived from thresholds
}
```

`status` is computed by applying thresholds from `PERFORMANCE.md`, for example:

* good: hit rate above target.
* warning: hit rate slightly below target.
* poor: hit rate significantly below target.

**Visual design**

* Title: "Cache Health".
* Main value: `hitRatePercent` formatted as `93 %`.
* Subtitle: "Hit rate since start".
* Status pill: "Good", "Warning", or "Poor" with color trim.

### 4.2.2 `RatingsLatencyCard`

**Purpose**

Show latency for `POST /api/ratings/<media_hash>`.

**Data binding**

From `/admin/performance.json`:

* `ratings_post.p95_latency_ms`
* `ratings_post.avg_latency_ms`
* `ratings_post.request_count`

**Derived props**

```ts
interface RatingsLatencyCardProps {
  p95Ms: number;
  avgMs: number;
  requestCount: number;
  status: StatusLevel;
}
```

`status` is derived from p95 thresholds in `PERFORMANCE.md`.

**Visual design**

* Title: "Ratings Latency".
* Primary value: "`p95Ms` ms p95".
* Secondary value: "`avgMs` ms average, `requestCount` requests".
* Status pill or accent border color based on status.

### 4.2.3 `DatabaseLoadCard`

**Purpose**

Show how heavy database usage is.

**Data binding**

From `/admin/performance.json.database`:

* `avg_per_request`
* `max_per_request`
* `count`

**Derived props**

```ts
interface DatabaseLoadCardProps {
  avgQueries: number;
  maxQueries: number;
  sampleCount: number;
  status: StatusLevel;
}
```

`status` is based on average queries per request. Thresholds are defined in `PERFORMANCE.md`.

**Visual design**

* Title: "Database Load".
* Primary value: "`avgQueries` queries per request".
* Secondary line: "Max `maxQueries` in last `sampleCount` requests".
* Status pill such as "Healthy" or "Heavy".

### 4.2.4 `UptimeStatusCard`

**Purpose**

Show uptime and overall system status.

**Data binding**

From `/admin/performance.json`:

* `uptime_seconds`

Optional future fields once resource metrics are added:

* `resources.cpu_percent`
* `resources.memory_percent`

**Derived props**

```ts
type UptimeStatus = "ok" | "degraded" | "restart-recommended";

interface UptimeStatusCardProps {
  uptimeSeconds: number;
  cpuPercent?: number;
  memoryPercent?: number;
  status: UptimeStatus;
}
```

`status` is computed from uptime and any known critical conditions (for example repeated error spikes or very long uptime plus warnings).

**Visual design**

* Title: "Uptime".
* Primary value: human readable uptime, such as `1 h 23 m`.
* Secondary line: `CPU 12 %, RAM 48 %` if available.
* Status pill: "Running", "Degraded", or "Restart recommended".

---

## 4.3 Summary panels

The second row uses wider cards that show related values together.

### 4.3.1 `CacheAndDbSummaryPanel`

**Purpose**

Provide a compact combined view of cache and database behavior.

**Data binding**

From `/admin/performance.json`:

* `cache_hit_rate`
* `database.total_queries`
* `database.avg_per_request`
* `database.max_per_request`
* `database.count`

**Derived props**

```ts
interface CacheAndDbSummaryPanelProps {
  cacheHitRatePercent: number;
  totalQueries: number;
  avgQueries: number;
  maxQueries: number;
  sampleCount: number;
}
```

**Visual design**

* Left side: cache section.

  * "Cache hit rate: 93 %".
  * Short text like "High cache hit rate reduces disk reads."
* Right side: database section.

  * "Total queries: 420".
  * "Average 4.2 per request, max 12 in last 100 requests."

### 4.3.2 `RatingsSummaryPanel`

**Purpose**

Highlight ratings workload and user interaction level.

**Data binding**

From `ratings_post`:

* `p95_latency_ms`
* `avg_latency_ms`
* `request_count`

**Derived props**

```ts
interface RatingsSummaryPanelProps {
  p95Ms: number;
  avgMs: number;
  requestCount: number;
}
```

**Visual design**

* Header: "Ratings workload".
* Body:

  * Big number for requestCount, for example "58 requests in window".
  * Small labels for p95 and average latency.
* Footer: text like "Within target" or "Above target" using thresholds from `PERFORMANCE.md`.

### 4.3.3 `SystemSummaryPanel`

**Purpose**

Summarize core system health beyond uptime, if resource metrics are present.

**Data binding**

Minimum:

* `uptime_seconds`.

Optional future values:

* `resources.cpu_percent`
* `resources.memory_percent`

**Derived props**

```ts
interface SystemSummaryPanelProps {
  uptimeSeconds: number;
  cpuPercent?: number;
  memoryPercent?: number;
}
```

**Visual design**

* Primary line: "Uptime: 1 h 23 m".
* CPU and memory displayed as:

  * Horizontal bars or mini meters.
  * Numeric labels such as "CPU 12 %" and "RAM 48 %".
* Optional text like "Values from last sample".

---

## 4.4 Route performance section

The bottom section shows detailed route metrics.

### 4.4.1 Data source

In the first iteration:

* Use `endpoints` from `/admin/performance.json` once it is populated.

After `GET /api/admin/performance/routes` is implemented:

* The table should query that endpoint directly for richer data and sorting options.

Each route object follows the schema defined in `PERFORMANCE_MONITORING.md`:

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

### 4.4.2 `RoutePerformanceTable`

**Purpose**

List routes in a sortable table so that slow or failing endpoints are easy to spot.

**Props**

```ts
type RouteSortKey = "p95Ms" | "p99Ms" | "avgMs" | "requestCount" | "errorRate";

interface RoutePerformanceRow {
  route: string;
  endpoint: string;
  p50Ms: number;
  p95Ms: number;
  p99Ms: number;
  avgMs: number;
  requestCount: number;
  errorCount: number;
}

interface RoutePerformanceTableProps {
  routes: RoutePerformanceRow[];
  sortBy: RouteSortKey;
  sortOrder: "asc" | "desc";
}
```

**Columns**

* Route (for example `GET /`).
* Endpoint (for example `main.index`).
* p50 (ms).
* p95 (ms).
* p99 (ms).
* Average (ms).
* Requests.
* Error rate (percentage).
* Status badge combining latency and error rate.

**Interactions**

* Clicking a column header toggles the sort key and sorts ascending then descending.
* A text input filters rows by route or endpoint.
* An optional filter dropdown shows only:

  * All routes.
  * Routes with warnings.
  * Routes with errors.

### 4.4.3 `RouteTrendSparkline`

**Purpose**

Show a quick trend for each route as a small inline chart.

**Data**

The dashboard collects time series samples in memory as it polls `/admin/performance.json` or `/api/admin/performance/routes`.

**Props**

```ts
interface RouteTrendPoint {
  timestamp: number;   // unix ms
  p95Ms: number;
}

interface RouteTrendSparklineProps {
  routeKey: string;            // unique key, for example "GET /watch/<filename>"
  points: RouteTrendPoint[];   // last N samples
}
```

**Visual design**

* Small line or area chart using canvas or SVG.
* The line color can change based on thresholds:

  * Mostly green if p95 stays under target.
  * Transition toward yellow or red if p95 crosses warning or error thresholds.

The sparkline is optional. The table must remain readable without it.

---

## 4.5 Efficiency charts

Efficiency charts show trends over time for cache hit rate and ratings latency. They live beside or below the route table.

### 4.5.1 `CacheEfficiencyChart`

**Purpose**

Plot cache hit rate over time.

**Data**

From client side sampling of `cache_hit_rate`.

**Props**

```ts
interface CacheEfficiencyPoint {
  timestamp: number;
  hitRatePercent: number;
}

interface CacheEfficiencyChartProps {
  samples: CacheEfficiencyPoint[];  // last N points
}
```

**Visual design**

* X axis: time.
* Y axis: cache hit rate in percent.
* Background bands that mark thresholds:

  * Green band where hit rate meets or exceeds target.
  * Yellow band near the boundary.
  * Red band where hit rate is poor.

The chart does not need axis labels in v1, as long as hover tooltips show numeric values.

### 4.5.2 `RatingsLatencyChart`

**Purpose**

Plot ratings p95 latency over time to reveal spikes or regressions.

**Data**

From client side sampling of `ratings_post.p95_latency_ms`.

**Props**

```ts
interface RatingsLatencyPoint {
  timestamp: number;
  p95Ms: number;
}

interface RatingsLatencyChartProps {
  samples: RatingsLatencyPoint[];
}
```

**Visual design**

* X axis: time.
* Y axis: p95 latency in ms.
* A reference line for the target p95 threshold from `PERFORMANCE.md`.
* Color coding:

  * Line is green while under target.
  * Line turns yellow or red where it crosses warning or error thresholds.

### 4.5.3 `UptimeAndLoadChart` (optional)

**Purpose**

Provide a small combined view of uptime and resource load once resource metrics are available.

**Data**

From `/admin/performance.json` plus any future `resources` block.

**Props**

```ts
interface UptimeAndLoadPoint {
  timestamp: number;
  cpuPercent?: number;
  memoryPercent?: number;
}

interface UptimeAndLoadChartProps {
  samples: UptimeAndLoadPoint[];
}
```

**Visual design**

* One or two stacked line plots for CPU and memory.
* Simple legend to distinguish lines.

This chart is optional and should only be enabled when CPU and memory metrics are wired into the admin layer.

---

## 5. Data flow and JavaScript integration

### 5.1 Initial render

1. `GET /admin/performance` is requested.
2. The view function in `backend/app/admin/routes.py`:

   * Reads values from `PerformanceMetrics`.
   * Renders `admin/performance.html` with:

     * Cache hit rate.
     * Ratings metrics.
     * Database summary.
     * Uptime.
3. The template uses Jinja2 to render:

   * KPI cards with server side numbers.
   * Summary panels.
   * Route table (empty or static explanatory text until `endpoints` data is available).

This means the dashboard is useful even with JavaScript disabled.

### 5.2 Live updates

`static/js/admin-dashboard.js` implements the client side behavior.

Responsibilities:

1. On page load:

   * Read initial values from `data-*` attributes on KPI cards and panels.
   * Start a poller that calls `/admin/performance.json` at a fixed interval.

2. On each poll:

   * Parse the JSON response.
   * Update:

     * KPI card text and status classes.
     * Summary panel values.
     * Route table rows.
     * Time series buffers for efficiency charts.

3. Re render charts and sparklines using a lightweight drawing library or simple canvas code.

Pseudocode outline:

```js
async function fetchMetrics() {
  const response = await fetch("/admin/performance/json", { cache: "no-store" });
  if (!response.ok) return null;
  return response.json();
}

function schedulePolling() {
  const intervalMs = 10000; // 10 seconds
  setInterval(async () => {
    const metrics = await fetchMetrics();
    if (!metrics) return;

    updateKpiCards(metrics);
    updateSummaryPanels(metrics);
    updateRouteTable(metrics);
    pushSamples(metrics);
    redrawCharts();
  }, intervalMs);
}

document.addEventListener("DOMContentLoaded", () => {
  schedulePolling();
});
```

The polling interval must be configurable in JS so it can be tuned without backend changes.

### 5.3 Error handling

If a JSON request fails:

* Keep the last known values on screen.
* Show a small banner or badge such as "Live metrics unavailable" after several consecutive failures.
* Do not log errors to the console on every failure; apply a cooldown to avoid noise.

---

## 6. Accessibility and responsiveness

### 6.1 Accessibility

* Use semantic HTML:

  * `nav` for the sidebar.
  * `main` for the content area.
  * `table` with `thead`, `tbody`, `th`, and `td` for route metrics.
* All status colors must be paired with text labels so that color blind users can read state.
* Charts should include:

  * Short text summaries near them, for example "Cache hit rate steady at 90 to 95 percent over last ten minutes."
  * `aria-label` attributes to describe their purpose.

Keyboard navigation:

* The sidebar must be reachable by tabbing.
* Table headers must be clickable with keyboard (use `button` inside `th` for sorting).

### 6.2 Responsive behavior

* On narrow screens:

  * Sidebar can collapse into a top menu or icon row.
  * KPI cards stack vertically.
  * Route table can allow horizontal scrolling.
  * Charts become full width stacked under the table.

* Layout must remain usable at common widths:

  * 1280 px and above: full layout as designed.
  * 1024 px: cards wrap, table shrinks but stays readable.
  * 768 px and below: single column layout with scroll.

---

## 7. Fail states and empty states

The dashboard should handle:

1. **No metrics yet**

   * When the server has just started and no requests have been made:

     * Cache hit rate may be zero.
     * Database counts will be zero.
     * Ratings request count may be zero.
   * Show meaningful empty states:

     * "No ratings requests yet."
     * "No database samples yet."

2. **Partial data**

   * If some blocks of the JSON payload are missing:

     * Treat missing blocks as unavailable rather than error.
     * Hide charts that depend on missing data and display a message like "Route metrics not yet available."

3. **High error conditions**

   * If a route has a high error rate:

     * Route table status cell should show "Errors" with a red pill.
     * Optionally link to logs or error pages in a later version.

---

## 8. Roadmap and extension points

Future enhancements that this spec anticipates:

1. **Richer admin APIs**

   * Full adoption of `GET /api/admin/performance/routes` for route table data.
   * Additional APIs such as:

     * `GET /api/admin/performance/storage`
     * `GET /api/admin/performance/errors`

2. **Interactive filters**

   * Date range filters that change which samples the charts use.
   * Toggles for grouping routes by prefix, such as `/api/` vs `/admin/`.

3. **Action links**

   * Buttons in summary panels that take the admin to:

     * Library reindex tools.
     * Cache flush and warm actions.
     * Backup or restore operations.

4. **Export**

   * Simple export of current metrics snapshot as JSON or CSV from the dashboard.

Any future changes should:

* Keep `ADMIN_DASHBOARD.md` and `PERFORMANCE_MONITORING.md` in sync.
* Update `docs/API.md` when new admin endpoints are added.
* Avoid breaking the existing HTML structure unless the change is reflected here.

---

## 9. Implementation checklist

When implementing or modifying the admin dashboard, ensure:

1. `/admin/performance` renders:

   * All four KPI cards with server side values.
   * Summary panels with server side values.
   * Route table container and any explanatory text.

2. `/admin/performance.json` matches the schema in `PERFORMANCE_MONITORING.md`.

3. `static/js/admin-dashboard.js`:

   * Polls JSON at a safe interval.
   * Updates KPI cards, summary panels, and table rows.
   * Maintains lightweight in memory buffers for charts.

4. `static/css/admin-dashboard.css`:

   * Implements the dark theme and card layout.
   * Respects responsive rules outlined above.
   * Uses shared tokens from `docs/UI.md` where possible.

5. Accessibility checks confirm:

   * Keyboard navigation works across the dashboard.
   * Status states are readable without relying solely on color.
   * Core content is still usable with JavaScript disabled.
