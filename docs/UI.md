# UI - Local Video Server

Consolidated UI documentation (design, player, and preview system). Original files archived to docs/deferred/.

## Design & Patterns

- Hybrid approach: glassmorphism for panels, neumorphism for controls where appropriate.
- Accessibility: WCAG AA contrast, keyboard navigation, clear focus states, reduced motion respect.

## Player & Controls

- Single shared player across pages (templates/_player.html).
- Controls: play/pause, volume, scrub, fullscreen, skip ±10s, keyboard bindings.
- Favorites and rating UI updated via centralized optimized-utils.js to sync controls across DOM.

## Preview System

- Adaptive preview strategies: hover based on desktop, tap or long press for touch and VR, disabled for low memory or slow connections.
- Key files: static/video-preview-enhanced.js, static/video-preview-debug.js, static/device-detection.js (stubbed compatibility file exists).

---

See docs/deferred/Local Video Server UI.md and docs/deferred/VIDEO_PREVIEW_IMPROVEMENTS.md for the full original text.

## Tag Autocomplete

- The watch page tag input now uses a datalist that surfaces the most frequently used tags.
- Suggestions are powered by SQLite data via the `/api/tags/popular` endpoint and cached in `cache_manager`.
- Typing filters the list; focusing on the field shows the top tags, which is helpful for videos that currently lack tags.
- Each suggestion displays the tag and usage count, preserving the existing `#tag` convention.

## Admin Dashboard overview

The admin dashboard provides a single place to review overall server health, cache efficiency, request latency, database load, and route performance. It is available at `/admin/performance` and is intended for local and LAN monitoring rather than public users.

At a high level, the dashboard:

- Confirms that gallery and watch pages remain responsive.
- Highlights overloaded or failing routes.
- Shows whether caching and indexing are behaving as expected.
- Acts as the starting point when you investigate performance regressions.

### Main visual building blocks

- **KPI card row**  
  A top row of compact cards that surfaces high level status such as overall health, p95 latency band, cache hit rate, error rate, and recent worker or background job issues.

- **Summary panels**  
  Panels that group related metrics, for example:
  - Cache and index health, including hit ratio and index coverage.
  - Database load, including active connections and query rates.
  - Background worker status, including queued and running jobs.

- **Route performance table**  
  A sortable table that lists key routes such as `/`, `/watch/<id>`, and core API endpoints. Each row shows per route latency statistics (p50, p95), request counts, and error counts so you can quickly find hot spots. Filters allow you to focus on slow or error prone routes.

- **Efficiency charts**  
  Compact charts and sparklines that show recent trends in latency, cache hit rate, database query volume, and error rate across the selected time window. These charts emphasize direction and stability rather than exact values.

### Relationship to other docs

This UI document stays at the design guideline level. Detailed component and layout behavior for the dashboard lives in `docs/ADMIN_DASHBOARD.md`. The metric shapes and field names consumed by the dashboard are defined in `docs/PERFORMANCE_MONITORING.md`. Backend wiring and endpoint contracts, including `/admin/performance` and `/admin/performance.json`, are described in `docs/ARCHITECTURE.md` and `docs/API.md`.
