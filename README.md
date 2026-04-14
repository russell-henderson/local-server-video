# Local Video Server

Last updated: April 14, 2026

Local-first media server with SQLite-backed metadata, hash-based ratings API, merged tag reads (DB + sidecar), and an optional admin dashboard.

## What This Project Does
- Serves local video files with byte-range streaming
- Tracks ratings, views, tags, and favorites
- Uses SQLite as metadata authority with JSON fallback paths
- Exposes admin/performance surfaces for diagnostics
- Includes an optional Next.js admin dashboard

## Documentation Map
Authoritative implementation reference:
- `docs/SOURCE_OF_TRUTH.md`

High-value docs:
- `doc/BACKEND_DETAILED.md`
- `doc/PROJECT_ANALYSIS_REPORT.md`
- `doc/SUGGESTED_CHANGES.md`
- `doc/LATEST.md`

Legacy and deep-dive documentation remains under `docs/`.

## Repository Layout
- `main.py`: Flask app entrypoint and web routes
- `backend/`: API blueprints, schemas, service-layer logic, admin telemetry helpers
- `cache_manager.py`: metadata cache orchestration and fallback behavior
- `database_migration.py`: SQLite schema, helpers, and migration utilities
- `templates/`: server-rendered HTML pages
- `static/`: frontend JS/CSS assets and generated thumbnails
- `admin-dashboard/`: Next.js dashboard app
- `tests/`: pytest suite
- `doc/`: project status/phase artifacts moved from root
- `docs/`: canonical + historical technical docs

## Runtime Topology
### Local runtime
- Start app: `python main.py`
- Default bind: `127.0.0.1:5000` (configurable)

### Docker Compose runtime
Defined in `docker-compose.yml`:
- `video-server`: Flask service (`5000:5000`)
- `nginx-proxy`: reverse/static proxy (`8080:80`)
- `admin-dashboard`: Next.js dashboard (`3000:3000`)

## Metadata and Data Authority
### Primary authority
- SQLite (`video_metadata.db`) via:
  - `database_migration.py` (`VideoDatabase`)
  - `cache_manager.py` (`VideoCache`)

### Fallback behavior
- JSON files (`ratings.json`, `views.json`, `tags.json`, `favorites.json`) are fallback/backup paths when DB is unavailable
- Runtime intent is DB-first for normal operations

## Ratings API Contract (Current)
Base route: `/api/ratings/<path:media_hash>`

### GET
- Known hash: `200`
- Unknown/unresolved hash: `404`

### POST
- Valid known hash and valid payload: `201`
- Invalid payload (`value` missing/type/range): `400`
- Unknown/unresolved hash: `404`
- Rate limit exceeded: `429`

### Payload shape
Request:
```json
{ "value": 4 }
```

Response summary:
```json
{
  "average": 4.0,
  "count": 1,
  "user": { "value": 4 }
}
```

## Tags Behavior (Current)
- Read paths are merged from sidecar + DB (additive, deduped): `/tags`, `/tag/<tag>`, `/api/tags/popular`
- Tag writes remain DB-path behavior

## Admin and Performance Surfaces
- `/admin/performance`
- `/admin/performance/json`
- `/api/admin/performance/routes`
- `/api/admin/performance/workers`
- `/api/admin/performance/active`
- `/admin/cache/status`
- `/admin/cache/refresh`

## Optional Dependencies
`psutil` is optional:
- Installed: richer system metrics
- Missing: graceful fallback with stable output keys and numeric defaults

## Configuration
Use `env.example` as the reference and copy to `.env` if needed.

Key variables include:
- `LVS_HOST`, `LVS_PORT`, `LVS_DEBUG`
- `LVS_VIDEO_DIRECTORY`, `LVS_THUMBNAIL_DIRECTORY`
- `LVS_CACHE_TIMEOUT`, `LVS_MAX_CACHE_SIZE`
- `LVS_ENABLE_ANALYTICS`, `LVS_ENABLE_PERF_LOG`

## Local Development Commands
### PowerShell helper
- `./dev.ps1 help`
- `./dev.ps1 dev`
- `./dev.ps1 test`

### Makefile helper
- `make help`
- `make dev`
- `make test`

## Testing
### Current verified baseline
Targeted regression slice:
```powershell
python -m pytest -q --color=no tests/test_ratings_api_contract_phase2.py tests/test_admin_performance_routes.py tests/test_basic.py tests/test_routes.py tests/test_rate_limiting.py tests/test_cors_support.py tests/test_tag_merge_phase5.py
```

Legacy ratings alignment suite:
```powershell
python -m pytest -q --color=no tests/test_rating_write_and_read.py tests/test_api_hash_invariants.py tests/test_rating_mapping.py
```

Full suite:
```powershell
python -m pytest -q --color=no
```

Current full-suite status after stabilization:
- Passes, with Playwright/browser tests skipped when browser dependencies are not installed.

## Optional Playwright Lane
`tests/test_watch_page_smoke.py` is treated as optional unless Playwright dependencies are installed.

To enable locally, install:
- `pytest-playwright`
- browser binaries for Playwright

Then run the file directly:
```powershell
python -m pytest -q --color=no tests/test_watch_page_smoke.py
```

## Troubleshooting
### Ratings POST returns 404
- Cause: unknown or unresolved `media_hash`
- Fix: ensure filename has been mapped to hash through the normal app flow/service registration

### Unexpected 429 on ratings POST
- Cause: request rate limit exceeded
- Fix: wait for limiter window reset or reduce burst traffic

### Missing system metrics detail
- Cause: `psutil` not installed
- Behavior is expected; app falls back gracefully

### No videos detected
- Verify video files exist in configured `videos/` path
- Verify volume mounts when using Docker

## Stability Notes
- Runtime/API/schema/Docker/proxy behavior was preserved during stabilization phases
- Legacy test drift was corrected in test files only
- Root markdown phase/status docs were relocated to `doc/` (except `README.md`)

## License
MIT - see `LICENSE`.
