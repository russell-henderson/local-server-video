# TODOv3 - Efficiency, Load Time, Analytics

## Critical fixes

- File watcher cache invalidation: replace calls to nonexistent `cache.invalidate_pattern(...)` with explicit invalidations and refresh/reindex hooks; wire watcher start/stop into app startup/shutdown if desired (file_watcher.py, main.py).
- Analytics persistence: JSON writes in `/analytics/*` are unguarded and on the request thread; move to a SQLite table with batching/locking and background flush; add schema versioning and FS-backed backup (main.py or new analytics module).

## Load time & efficiency

- Index/watch pagination: `index()` and favorites/best-of pages render the full dataset; add server-side pagination/infinite scroll and lightweight list endpoints (main.py/templates/static JS).
- Thumbnail pipeline: throttle `ensure_thumbnails_exist` calls per request, add a dedup queue and per-run limiter; surface ffmpeg failures and pre-warm during startup (main.py, thumbnail_manager.py).
- Static asset delivery: serve JS/CSS with cache headers + etags, compress (gzip/brotli) and consider bundling/treeshaking key frontend scripts (`video-analytics.js`, etc.); avoid blocking inline scripts (static assets).
- Streaming endpoint: add conditional/etag responses and HEAD support; optionally enable chunked async file reads for large files; tune `send_file`/Response headers for caching (main.py).
- Database performance: add WAL+PRAGMA tuning and indexes for hot queries (views/rating/tag lookups, search), and expose DB stats in `/admin/performance/json` (database_migration.py, backend/app/admin).

## Analytics & observability

- Align client/server analytics: frontend posts to `/analytics/event` while the backend only exposes `/analytics/save`; unify endpoint and payload schema (sessionId, progressPct, heartbeats) and validate input (static/video-analytics.js, main.py).
- Analytics warehouse: store events in SQLite with rollups (watch time, completion, seeks), nightly aggregation job, and export to CSV/Parquet; add retention/cleanup policy.
- Dashboards: extend `/admin/performance` to show cache hit rate, search latency, top searches, drop/timeout counts; add watch-time leaderboard and completion histogram.
- Metrics pipeline: wrap DB/cache/search calls with `performance_monitor` timers and publish to structured logs; integrate request/worker health (ffmpeg, watchdog, search index) into `/ping`/health endpoints.
- Search analytics: capture query success/zero-result counts from `AdvancedSearchEngine`, expose reindex duration and FTS size; add background job to prune stale `search_history`.

## Testing/ops

- Add load-test script using `performance_monitor.load_test_simulation` with fixtures and capture perf baselines; wire into CI as an optional step.
- Add migrations/tests for analytics + search schema changes and for cache fallback paths (database_migration.py, tests/).
- Document tuning knobs in `docs/PERFORMANCE.md` and add a runbook for cache/search/analytics rebuild/recovery.
