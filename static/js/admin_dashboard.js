/* Admin Performance Dashboard client-side script */
(() => {
  const ADMIN_API = {
    performanceJsonUrl: "/admin/performance/json",
    routesUrl: "/api/admin/performance/routes",
    workersUrl: "/api/admin/performance/workers",
    cacheStatusUrl: "/admin/cache/status",
    cacheRefreshUrl: "/admin/cache/refresh",
  };

  const state = {
    latencyChart: null,
    trafficChart: null,
    failureCount: 0,
    windowSeconds: 900,
    pollingMs: 10000,
  };

  function getBootstrapSnapshot() {
    const el = document.getElementById("admin-bootstrap");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || "{}");
    } catch (err) {
      console.warn("Failed to parse bootstrap snapshot", err);
      return null;
    }
  }

  const bootstrapSnapshot = getBootstrapSnapshot();
  if (bootstrapSnapshot && bootstrapSnapshot.window_seconds) {
    state.windowSeconds = bootstrapSnapshot.window_seconds;
  }

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      cache: "no-store",
      ...options,
    });
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(`Request failed (${response.status}): ${text}`);
    }
    return response.json();
  }

  function setBannerVisible(isVisible) {
    const banner = document.getElementById("metrics-banner");
    if (!banner) return;
    banner.style.display = isVisible ? "block" : "none";
  }

  function renderKpis(snapshot) {
    const container = document.getElementById("admin-kpis");
    if (!container || !snapshot) return;
    const cacheUsage = (snapshot.cache?.preview_cache_usage_ratio || 0) * 100;
    const ratingsStatus = snapshot.ratings?.status || "warning";
    const cards = [
      {
        id: "kpi-global-p95",
        label: "Global p95 latency",
        value: `${(snapshot.global?.p95_latency_ms || 0).toFixed(1)} ms`,
        status: snapshot.status?.overall || "unknown",
      },
      {
        id: "kpi-ratings-p95",
        label: "Ratings p95 latency",
        value: snapshot.ratings
          ? `${(snapshot.ratings.p95_latency_ms || 0).toFixed(1)} ms`
          : "--",
        status: ratingsStatus,
      },
      {
        id: "kpi-error-rate",
        label: "Global error rate",
        value: `${((snapshot.global?.error_rate || 0) * 100).toFixed(2)} %`,
        status: snapshot.status?.overall || "unknown",
      },
      {
        id: "kpi-cache-usage",
        label: "Cache usage",
        value: `${cacheUsage.toFixed(1)} %`,
        status: snapshot.cache?.status || "unknown",
      },
    ];

    container.innerHTML = cards
      .map(
        (card) => `
      <article class="admin-kpi admin-kpi--${card.status}">
        <div class="text-muted text-uppercase small">${card.label}</div>
        <p class="admin-kpi__value">${card.value}</p>
        <p class="admin-kpi__status">${card.status}</p>
      </article>
    `
      )
      .join("");
  }

  function renderRoutesTable(routesPayload) {
    const tbody = document.querySelector("#routes-table tbody");
    if (!tbody || !routesPayload) return;
    const routes = routesPayload.routes || [];
    if (!routes.length) {
      tbody.innerHTML =
        '<tr><td colspan="8" class="text-muted">No route metrics yet.</td></tr>';
      return;
    }
    const rows = routes
      .map((route) => {
        const statusClass = `status-${route.status || "unknown"}`;
        return `
        <tr>
          <td>${route.path}</td>
          <td>${route.method}</td>
          <td>${route.p50_latency_ms.toFixed(1)}</td>
          <td>${route.p95_latency_ms.toFixed(1)}</td>
          <td>${route.p99_latency_ms.toFixed(1)}</td>
          <td>${route.request_count}</td>
          <td>${(route.error_rate * 100).toFixed(2)} %</td>
          <td><span class="status-pill ${statusClass}">${route.status}</span></td>
        </tr>
      `;
      })
      .join("");
    tbody.innerHTML = rows;
  }

  function renderWorkers(workersPayload) {
    const summaryEl = document.getElementById("workers-summary");
    const statusEl = document.getElementById("workers-status");
    const tbody = document.getElementById("queues-table");
    if (!summaryEl || !statusEl || !tbody) return;

    summaryEl.textContent = `Workers: ${workersPayload.worker_count} | Status: ${workersPayload.status}`;
    statusEl.textContent = workersPayload.status;
    statusEl.className = `badge bg-${
      workersPayload.status === "good"
        ? "success"
        : workersPayload.status === "disabled"
        ? "secondary"
        : "warning"
    }`;

    const queues = workersPayload.queues || [];
    if (!queues.length) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="text-muted">No queues</td></tr>';
      return;
    }

    tbody.innerHTML = queues
      .map(
        (queue) => `
      <tr>
        <td>${queue.name}</td>
        <td>${queue.pending_jobs}</td>
        <td>${queue.in_progress_jobs}</td>
        <td>${queue.failed_jobs}</td>
        <td>${queue.oldest_pending_age_seconds}</td>
        <td><span class="status-pill status-${queue.status}">${queue.status}</span></td>
      </tr>
    `
      )
      .join("");
  }

  async function refreshCacheStatus() {
    const usageText = document.getElementById("cache-usage-text");
    const usageBar = document.getElementById("cache-usage-bar");
    const statusText = document.getElementById("cache-status-text");
    if (!usageText || !usageBar || !statusText) return;

    try {
      const status = await fetchJson(ADMIN_API.cacheStatusUrl);
      const ratio =
        status.preview_cache_usage_ratio ??
        (status.preview_cache_bytes && status.preview_cache_limit_bytes
          ? status.preview_cache_bytes / status.preview_cache_limit_bytes
          : 0);
      const pct = Math.min(Math.max(ratio || 0, 0), 1) * 100;
      const items =
        status.preview_cache_items ??
        status.cache_items ??
        status.recent_videos?.length ??
        0;
      usageText.textContent = `Using ${pct.toFixed(1)} % of cache capacity (${items} items)`;
      usageBar.style.width = `${pct}%`;
      usageBar.setAttribute("aria-valuenow", pct.toFixed(1));
      statusText.textContent = `Status: ${status.status || "unknown"}`;
    } catch (err) {
      usageText.textContent = "Cache status unavailable";
      statusText.textContent = String(err);
    }
  }

  async function handleCacheRefreshClick() {
    const button = document.getElementById("cache-refresh-button");
    if (!button) return;
    button.disabled = true;
    try {
      const result = await fetchJson(ADMIN_API.cacheRefreshUrl, { method: "POST" });
      if (!result.success && result.error) {
        alert(`Cache refresh failed: ${result.error.message || "Unknown error"}`);
      }
      await refreshCacheStatus();
    } catch (err) {
      alert(`Cache refresh failed: ${err.message}`);
    } finally {
      button.disabled = false;
    }
  }

  function renderLatencyChart(snapshot) {
    const canvas = document.getElementById("latency-chart");
    if (!canvas || typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    const globalValues = [
      snapshot.global?.p50_latency_ms || 0,
      snapshot.global?.p95_latency_ms || 0,
      snapshot.global?.p99_latency_ms || 0,
    ];
    const ratingsValues = snapshot.ratings
      ? [
          snapshot.ratings.p50_latency_ms || 0,
          snapshot.ratings.p95_latency_ms || 0,
          snapshot.ratings.p99_latency_ms || 0,
        ]
      : [0, 0, 0];
    const data = {
      labels: ["p50", "p95", "p99"],
      datasets: [
        { label: "Global", data: globalValues, backgroundColor: "rgba(79, 70, 229, 0.6)" },
        { label: "Ratings", data: ratingsValues, backgroundColor: "rgba(16, 185, 129, 0.6)" },
      ],
    };
    const options = {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: { y: { beginAtZero: true } },
    };
    if (state.latencyChart) {
      state.latencyChart.data = data;
      state.latencyChart.options = options;
      state.latencyChart.update();
    } else {
      state.latencyChart = new Chart(ctx, { type: "bar", data, options });
    }
  }

  function renderTrafficChart(snapshot) {
    const canvas = document.getElementById("traffic-chart");
    if (!canvas || typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    const requestCount = snapshot.global?.request_count || 0;
    const errorRate = (snapshot.global?.error_rate || 0) * 100;

    const data = {
      labels: ["Current window"],
      datasets: [
        {
          type: "bar",
          label: "Requests",
          data: [requestCount],
          backgroundColor: "rgba(59,130,246,0.6)",
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Error rate (%)",
          data: [errorRate],
          borderColor: "rgba(248,113,113,0.9)",
          backgroundColor: "rgba(248,113,113,0.2)",
          yAxisID: "y1",
        },
      ],
    };
    const options = {
      responsive: true,
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "Requests" } },
        y1: {
          beginAtZero: true,
          position: "right",
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Error rate (%)" },
        },
      },
    };
    if (state.trafficChart) {
      state.trafficChart.data = data;
      state.trafficChart.options = options;
      state.trafficChart.update();
    } else {
      state.trafficChart = new Chart(ctx, { data, options });
    }
  }

  async function loadRoutes() {
    try {
      const payload = await fetchJson(
        `${ADMIN_API.routesUrl}?window_seconds=${state.windowSeconds}&sort_by=p95_latency_ms&order=desc`
      );
      renderRoutesTable(payload);
    } catch (err) {
      console.error("Failed to load routes", err);
    }
  }

  async function loadDashboardData(forceRoutes = false) {
    try {
      const perfSnapshot = await fetchJson(
        `${ADMIN_API.performanceJsonUrl}?window_seconds=${state.windowSeconds}&include_routes=${forceRoutes}`
      );
      state.failureCount = 0;
      setBannerVisible(false);
      renderKpis(perfSnapshot);
      renderLatencyChart(perfSnapshot);
      renderTrafficChart(perfSnapshot);
      if (forceRoutes || perfSnapshot.routes) {
        renderRoutesTable({ routes: perfSnapshot.routes || [] });
      }
    } catch (err) {
      state.failureCount += 1;
      if (state.failureCount >= 2) {
        setBannerVisible(true);
      }
      console.error("Failed to load performance snapshot", err);
    }

    try {
      const workersPayload = await fetchJson(ADMIN_API.workersUrl);
      renderWorkers(workersPayload);
    } catch (err) {
      console.error("Failed to load workers", err);
    }

    if (forceRoutes) {
      await loadRoutes();
    }

    await refreshCacheStatus();
  }

  function initDashboard() {
    const refreshButton = document.getElementById("admin-refresh-button");
    const routesRefreshButton = document.getElementById("routes-refresh-button");
    const cacheRefreshButton = document.getElementById("cache-refresh-button");

    if (refreshButton) {
      refreshButton.addEventListener("click", () => loadDashboardData(true));
    }
    if (routesRefreshButton) {
      routesRefreshButton.addEventListener("click", () => loadRoutes());
    }
    if (cacheRefreshButton) {
      cacheRefreshButton.addEventListener("click", handleCacheRefreshClick);
    }

    if (bootstrapSnapshot) {
      renderKpis(bootstrapSnapshot);
      renderLatencyChart(bootstrapSnapshot);
      renderTrafficChart(bootstrapSnapshot);
      if (bootstrapSnapshot.routes) {
        renderRoutesTable({ routes: bootstrapSnapshot.routes });
      }
    }

    loadDashboardData(false);
    setInterval(() => loadDashboardData(false), state.pollingMs);
  }

  document.addEventListener("DOMContentLoaded", initDashboard);
})();
