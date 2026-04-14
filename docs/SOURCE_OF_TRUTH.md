# Source Of Truth

Last updated: April 14, 2026
Repository: `local-video-server`

This file is the canonical implementation reference.  
If another doc conflicts with this file, treat this file and code as authoritative.

## 1. Canonical Runtime Entrypoints
- Local runtime: `python main.py`
- Docker runtime: `Dockerfile` `CMD ["python", "main.py"]`
- Flask app bootstrap: `main.py`

## 2. Actual Docker Topology
Defined in `docker-compose.yml`:
- `video-server`
  - builds from repo root Dockerfile
  - exposes `5000:5000`
- `nginx-proxy`
  - image `nginx:alpine`
  - exposes `8080:80`
  - proxies/serves static assets
- `admin-dashboard`
  - builds from `admin-dashboard/Dockerfile`
  - exposes `3000:3000`
  - reads app metadata/video/image volumes as read-only

No additional production services are currently defined.

## 3. Metadata Authority And Fallback
- Primary metadata authority: SQLite (`video_metadata.db`) via:
  - `database_migration.py` (`VideoDatabase`)
  - `cache_manager.py` (`VideoCache`)
- JSON files are fallback/backups only:
  - `ratings.json`, `views.json`, `tags.json`, `favorites.json`
- Runtime intent:
  - DB-first for reads/writes
  - JSON path used only when DB is unavailable

## 4. Admin/Performance Surfaces
Current endpoints include:
- `/admin/performance`
- `/admin/performance/json`
- `/api/admin/performance/routes`
- `/api/admin/performance/workers`
- `/api/admin/performance/active`
- `/admin/cache/status`
- `/admin/cache/refresh`

`psutil` behavior:
- installed: full system metric collection
- missing: graceful fallback (same output keys with numeric defaults), no import-time failure

## 5. Ratings API Contract (Current)
Route prefix: `/api/ratings/<path:media_hash>`

### GET
- Unknown/unresolved `media_hash`: `404`
- Known hash: `200` with rating summary payload

### POST
- Unknown/unresolved `media_hash`: `404`
- Invalid payload (`value` missing/type/range invalid): `400`
- Rate limit exceeded: `429` (unchanged behavior)
- Known hash + valid payload: `201` with unchanged summary shape

## 6. Current Status Labels

### Implemented now
- Flask media server routes and watch/listing flows
- SQLite-first metadata cache and persistence
- Ratings API hash contract above
- Admin performance surfaces and caching
- Optional `psutil` fallback mode

### Optional / partially implemented
- System metrics detail quality depends on `psutil` availability
- Some large or legacy test modules remain noisy/legacy and are not baseline-gated

### Planned / not yet canonicalized
- Broader full-suite test harmonization beyond current safe baseline
- Additional doc consolidation of older historical files in `docs/`

## 7. Safe Regression Baseline
Use these commands as current validation baseline:

```powershell
python -m compileall -q main.py cache_manager.py config.py database_migration.py file_watcher.py thumbnail_manager.py backend tests
python -m pytest -q tests/test_ratings_api_contract_phase2.py tests/test_admin_performance_routes.py tests/test_basic.py tests/test_routes.py tests/test_rate_limiting.py tests/test_cors_support.py
```

## 8. Documentation Hierarchy
1. `docs/SOURCE_OF_TRUTH.md` (this file)
2. `README.md` (operator/developer quickstart)
3. `BACKEND_DETAILED.md` (backend detail snapshot)
4. Historical/planning docs (`PROJECT_ANALYSIS_REPORT.md`, `SUGGESTED_CHANGES.md`, phase notes)
