# Backend Detailed Documentation

Last updated: April 14, 2026
Repository root: `Z:\local-video-server`

Canonical source-of-truth: `docs/SOURCE_OF_TRUTH.md`

## 1. Backend Overview
Implemented backend behavior today:
- Flask runtime in `main.py`
- SQLite-first metadata persistence and query path
- Ratings API based on `media_hash`
- Optional admin/performance telemetry surfaces
- Image gallery and grouping support

## 2. Runtime Composition

### Core modules
- `main.py`
  - App bootstrap and route registration
  - Health endpoints (`/ping`, `/favicon.ico`)
  - Media, gallery, analytics, and admin/cache routes
- `cache_manager.py`
  - `VideoCache` with TTL caches
  - DB-first reads/writes with JSON fallback when DB unavailable
- `database_migration.py`
  - `VideoDatabase` schema initialization and helpers
  - JSON migration helper and gallery/pHash helpers

### Ratings/API modules
- `backend/services/ratings_service.py`
  - media hash generation and resolution
  - rating summary and rating set flow
- `backend/app/api/ratings.py`
  - `/api/ratings/<path:media_hash>` GET/POST/OPTIONS
  - LAN-scoped CORS behavior
  - IP rate limit on POST
- `backend/app/api/schemas.py`
  - Pydantic v2-style `ConfigDict` schema metadata

### Admin/performance modules
- `backend/app/admin/routes.py`
  - `/admin/performance`
  - `/admin/performance/json`
  - `/api/admin/performance/routes`
  - `/api/admin/performance/workers`
  - `/api/admin/performance/active`
- `performance_monitor.py`
  - request/route metric capture helpers
  - optional `psutil` usage with graceful fallback when unavailable

## 3. Metadata Authority
- Canonical metadata backend: SQLite (`video_metadata.db`)
- JSON files are fallback/backup path only when DB cannot initialize
- Persistence semantics remain DB-first in normal runtime

## 4. Ratings Contract (Current)
Route: `/api/ratings/<path:media_hash>`

### GET
- Unknown/unresolved hash: `404`
- Known hash: `200` summary payload

### POST
- Unknown/unresolved hash: `404`
- Invalid payload/type/range: `400`
- Rate-limited requests: `429`
- Valid known hash + valid payload: `201`

## 5. Data Model (SQLite)
Active tables include:
- `videos`
- `ratings`
- `views`
- `video_tags`
- `favorites`
- `media_hash_map`
- `gallery_groups`
- `gallery_group_items`
- `phash_cache`

Indexes and update triggers are defined in `database_migration.py`.

## 6. Validation Baseline
Current safe regression baseline:

```powershell
python -m compileall -q main.py cache_manager.py config.py database_migration.py file_watcher.py thumbnail_manager.py backend tests
python -m pytest -q tests/test_ratings_api_contract_phase2.py tests/test_admin_performance_routes.py tests/test_basic.py tests/test_routes.py tests/test_rate_limiting.py tests/test_cors_support.py
```

Observed state after Phases 0-3: targeted baseline passes.
