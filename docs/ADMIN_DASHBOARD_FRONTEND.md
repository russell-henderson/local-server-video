# Admin Dashboard Frontend Implementation

This document describes how to implement the admin performance dashboard UI on top of the HTML template system used by Local Video Server.

It complements the UI spec in `ADMIN_DASHBOARD.md` and the backend contracts in `ADMIN_API_SPEC.md`.

---

## Tech Stack Decision

**Recommendation**

* Keep using server rendered HTML templates (Jinja) with vanilla JavaScript.
* Use a small client side script to:

  * Fetch JSON metrics from the admin endpoints.
  * Populate KPI cards, tables, and charts.
* Use a lightweight charting library such as Chart.js loaded from a CDN.

**Justification**

* Matches the existing stack described in `UI.md` and `DATA_BACKEND.md`.
* Avoids introducing a separate Node build or framework project for one admin page.
* Keeps deployment simple and consistent with the rest of the app.

**Alternatives Considered**

* React or Vue based single page app mounted on `/admin/performance`:

  * Pros: richer component model, easier future expansion.
  * Cons: additional build pipeline and tooling footprint for a single internal page.

The current approach can be revisited if the admin area grows into a full console later.

---

## Project Structure

Frontend files for the admin dashboard:

* Template:

  * `templates/admin/performance.html`

* Styles:

  * Reuse base layout and CSS defined for the app.
  * Optional extra CSS:

    * `static/css/admin_dashboard.css`

* JavaScript:

  * Entry script:

    * `static/js/admin_dashboard.js`
  * Chart library:

    * Included via `<script>` tag from CDN in `performance.html`.

Folder tree:

```text
templates/
  base.html
  admin/
    performance.html

static/
  css/
    main.css
    admin_dashboard.css     (optional, for dashboard specific tweaks)
  js/
    main.js
    admin_dashboard.js
```

---

## Setup Instructions

1. **Create the template directory**

   * Create `templates/admin/` if it does not already exist.

2. **Create `templates/admin/performance.html`**

   * Extend your existing base layout.
   * Include markup for:

     * Global KPI cards.
     * Route performance table.
     * Worker status panel.
     * Cache status widget.
     * Charts containers.

   Example skeleton:

   ```html
   {% extends "base.html" %}

   {% block title %}Admin Performance Dashboard{% endblock %}

   {% block content %}
   <section class="admin-dashboard">
     <header class="admin-dashboard__header">
       <h1>Admin Performance Dashboard</h1>
       <button id="admin-refresh-button" type="button">Refresh now</button>
     </header>

     <section class="admin-dashboard__kpis" id="admin-kpis">
       <!-- KPI cards will be populated by JS -->
     </section>

     <section class="admin-dashboard__charts">
       <div class="admin-dashboard__chart">
         <h2>Global latency (p50, p95, p99)</h2>
         <canvas id="latency-chart"></canvas>
       </div>
       <div class="admin-dashboard__chart">
         <h2>Requests and error rate</h2>
         <canvas id="traffic-chart"></canvas>
       </div>
     </section>

     <section class="admin-dashboard__routes">
       <h2>Per route performance</h2>
       <table id="routes-table">
         <thead>
           <tr>
             <th>Path</th>
             <th>Method</th>
             <th>P95 (ms)</th>
             <th>Error rate</th>
             <th>Requests</th>
             <th>Status</th>
           </tr>
         </thead>
         <tbody>
           <!-- Rows populated dynamically -->
         </tbody>
       </table>
     </section>

     <section class="admin-dashboard__workers-cache">
       <div id="workers-panel">
         <h2>Workers</h2>
         <div id="workers-summary"></div>
         <table id="queues-table">
           <thead>
             <tr>
               <th>Queue</th>
               <th>Pending</th>
               <th>In progress</th>
               <th>Failed</th>
               <th>Oldest age (s)</th>
               <th>Status</th>
             </tr>
           </thead>
           <tbody></tbody>
         </table>
       </div>

       <div id="cache-panel">
         <h2>Preview cache</h2>
         <p id="cache-usage-text"></p>
         <progress id="cache-usage-bar" max="1" value="0"></progress>
         <button id="cache-refresh-button" type="button">Refresh cache</button>
         <p id="cache-status-text"></p>
       </div>
     </section>
   </section>
   {% endblock %}

   {% block scripts %}
   {{ super() }}
   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   <script src="{{ url_for('static', filename='js/admin_dashboard.js') }}"></script>
   {% endblock %}
   ```

3. **Create `static/js/admin_dashboard.js`**

   * Implement logic described in the next sections.

4. **Optional: create `static/css/admin_dashboard.css`**

   * Add layout and style tweaks as needed, following design tokens in `UI.md`.

5. **Add navigation link**

   * Update the admin navigation section in `base.html` or an appropriate layout file to include a link to `/admin/performance`.

---

## Component Implementation

The dashboard UI has several logical components. Each component is implemented as a JavaScript function that reads from the JSON payloads defined in `ADMIN_API_SPEC.md`.

### 1. Data fetch layer

Implement a small fetch client in `admin_dashboard.js`:

```js
const ADMIN_API = {
  performanceJsonUrl: "/admin/performance/json",
  routesUrl: "/api/admin/performance/routes",
  workersUrl: "/api/admin/performance/workers",
  cacheStatusUrl: "/admin/cache/status",
  cacheRefreshUrl: "/admin/cache/refresh",
};

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: {
      "Accept": "application/json",
    },
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Request failed with ${response.status}: ${text}`);
  }

  return response.json();
}
```

### 2. KPI cards

Generate KPI cards for:

* Global p95 latency.
* Global error rate.
* Ratings p95 latency.
* Preview cache usage.

Example JS:

```js
function renderKpis(perfSnapshot) {
  const container = document.getElementById("admin-kpis");
  if (!container) return;

  const cards = [];

  cards.push({
    id: "kpi-global-p95",
    label: "Global p95 latency",
    value: `${perfSnapshot.global.p95_latency_ms.toFixed(1)} ms`,
    status: perfSnapshot.status.overall,
  });

  if (perfSnapshot.ratings) {
    cards.push({
      id: "kpi-ratings-p95",
      label: "Ratings p95 latency",
      value: `${perfSnapshot.ratings.p95_latency_ms.toFixed(1)} ms`,
      status: perfSnapshot.ratings.status,
    });
  }

  cards.push({
    id: "kpi-error-rate",
    label: "Global error rate",
    value: `${(perfSnapshot.global.error_rate * 100).toFixed(2)} %`,
    status: perfSnapshot.status.overall,
  });

  const usagePct = perfSnapshot.cache.preview_cache_usage_ratio * 100;
  cards.push({
    id: "kpi-cache-usage",
    label: "Preview cache usage",
    value: `${usagePct.toFixed(1)} %`,
    status: perfSnapshot.cache.status,
  });

  container.innerHTML = cards
    .map((card) => {
      return `
        <article class="admin-kpi admin-kpi--${card.status}">
          <h3>${card.label}</h3>
          <p class="admin-kpi__value">${card.value}</p>
          <p class="admin-kpi__status">${card.status}</p>
        </article>
      `;
    })
    .join("");
}
```

Use CSS classes such as `admin-kpi--good`, `admin-kpi--warning`, and `admin-kpi--critical` to color code cards as described in `ADMIN_DASHBOARD.md`.

### 3. Route performance table

Implementation pattern:

```js
function renderRoutesTable(routesPayload) {
  const tbody = document.querySelector("#routes-table tbody");
  if (!tbody) return;

  const rows = routesPayload.routes.map((route) => {
    return `
      <tr class="route-row route-row--${route.status}">
        <td>${route.path}</td>
        <td>${route.method}</td>
        <td>${route.p95_latency_ms.toFixed(1)}</td>
        <td>${(route.error_rate * 100).toFixed(2)} %</td>
        <td>${route.request_count}</td>
        <td>${route.status}</td>
      </tr>
    `;
  });

  tbody.innerHTML = rows.join("");
}
```

Add click handlers on table headers if you want client side sorting. The backend already supports sorted responses via query parameters.

### 4. Worker and queue panels

Use the payload from `/api/admin/performance/workers`:

```js
function renderWorkers(workersPayload) {
  const summaryEl = document.getElementById("workers-summary");
  const queuesTbody = document.querySelector("#queues-table tbody");
  if (!summaryEl || !queuesTbody) return;

  summaryEl.textContent = `Workers: ${workersPayload.worker_count} (status: ${workersPayload.status})`;

  const rows = workersPayload.queues.map((queue) => {
    return `
      <tr class="queue-row queue-row--${queue.status}">
        <td>${queue.name}</td>
        <td>${queue.pending_jobs}</td>
        <td>${queue.in_progress_jobs}</td>
        <td>${queue.failed_jobs}</td>
        <td>${queue.oldest_pending_age_seconds}</td>
        <td>${queue.status}</td>
      </tr>
    `;
  });

  queuesTbody.innerHTML = rows.join("");
}
```

### 5. Cache status widget

Use the existing cache endpoints:

```js
async function refreshCacheStatus() {
  const status = await fetchJson(ADMIN_API.cacheStatusUrl);

  const usageText = document.getElementById("cache-usage-text");
  const usageBar = document.getElementById("cache-usage-bar");
  const statusText = document.getElementById("cache-status-text");

  if (!usageText || !usageBar || !statusText) return;

  const ratio = status.preview_cache_usage_ratio ?? (
    status.preview_cache_bytes / status.preview_cache_limit_bytes
  );

  usageText.textContent = `Using ${(ratio * 100).toFixed(1)} % of cache capacity (${status.preview_cache_items} items)`;
  usageBar.value = ratio;
  statusText.textContent = `Status: ${status.status}`;
}

async function handleCacheRefreshClick() {
  const button = document.getElementById("cache-refresh-button");
  if (!button) return;

  button.disabled = true;
  try {
    const result = await fetch(ADMIN_API.cacheRefreshUrl, {
      method: "POST",
      headers: {
        "Accept": "application/json",
      },
    }).then((res) => res.json());

    if (!result.success) {
      alert(`Cache refresh failed: ${result.error?.message ?? "Unknown error"}`);
    } else {
      await refreshCacheStatus();
    }
  } finally {
    button.disabled = false;
  }
}
```

Wire this in `initDashboard`:

```js
function initDashboard() {
  const refreshButton = document.getElementById("admin-refresh-button");
  const cacheRefreshButton = document.getElementById("cache-refresh-button");

  if (refreshButton) {
    refreshButton.addEventListener("click", () => {
      loadDashboardData(true);
    });
  }

  if (cacheRefreshButton) {
    cacheRefreshButton.addEventListener("click", handleCacheRefreshClick);
  }

  // Initial load
  loadDashboardData(false);

  // Poll every 10 seconds
  setInterval(() => loadDashboardData(false), 10000);
}
```

### 6. Charts and visualization

Use Chart.js for simple line or bar charts.

Example creating a latency chart:

```js
let latencyChartInstance = null;

function renderLatencyChart(ctx, perfSnapshot) {
  const labels = ["p50", "p95", "p99"];
  const globalValues = [
    perfSnapshot.global.p50_latency_ms,
    perfSnapshot.global.p95_latency_ms,
    perfSnapshot.global.p99_latency_ms,
  ];
  const ratingsValues = perfSnapshot.ratings
    ? [
        perfSnapshot.ratings.p50_latency_ms,
        perfSnapshot.ratings.p95_latency_ms,
        perfSnapshot.ratings.p99_latency_ms,
      ]
    : [0, 0, 0];

  const data = {
    labels,
    datasets: [
      {
        label: "Global",
        data: globalValues,
      },
      {
        label: "Ratings",
        data: ratingsValues,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { display: true },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  if (latencyChartInstance) {
    latencyChartInstance.data = data;
    latencyChartInstance.options = options;
    latencyChartInstance.update();
  } else {
    latencyChartInstance = new Chart(ctx, {
      type: "bar",
      data,
      options,
    });
  }
}
```

In `loadDashboardData`, after fetching the snapshot:

```js
async function loadDashboardData(forceRoutes) {
  try {
    const perfSnapshot = await fetchJson(
      `${ADMIN_API.performanceJsonUrl}?include_routes=${forceRoutes ? "true" : "false"}&include_workers=true`
    );

    renderKpis(perfSnapshot);

    const latencyCanvas = document.getElementById("latency-chart");
    if (latencyCanvas) {
      renderLatencyChart(latencyCanvas.getContext("2d"), perfSnapshot);
    }

    // Optionally load routes table when forced
    if (forceRoutes) {
      const routesPayload = await fetchJson(ADMIN_API.routesUrl);
      renderRoutesTable(routesPayload);
    }

    const workersPayload = await fetchJson(ADMIN_API.workersUrl);
    renderWorkers(workersPayload);

    await refreshCacheStatus();
  } catch (error) {
    console.error("Failed to load dashboard data", error);
  }
}
```

---

## API Integration Summary

* `GET /admin/performance/json`

  * Primary source for KPI cards and charts.
* `GET /api/admin/performance/routes`

  * Used when user explicitly requests full route table refresh.
* `GET /api/admin/performance/workers`

  * Used on every refresh to keep worker and queue panels accurate.
* `GET /admin/cache/status` and `POST /admin/cache/refresh`

  * Used for cache widget interactions.

All network calls must handle errors gracefully. The UI should show a simple message such as "Metrics unavailable" rather than breaking the page.

---

## Build and Deploy

Because this is a template driven page with plain JavaScript:

* There is no separate build step.
* To deploy:

  * Ensure `templates/admin/performance.html` and `static/js/admin_dashboard.js` are part of the repository.
  * Restart the application process.
  * Verify access to `/admin/performance` from a trusted browser on the LAN.

If you later move to a compiled frontend stack, update this document to describe the build process and static asset pipeline.