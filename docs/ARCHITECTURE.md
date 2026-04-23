# Local Video Server Architecture

## Runtime Stack

- Framework/runtime: Flask + Jinja templates.
- Orchestration: Docker Compose (unchanged).
- Data: SQLite runtime DB files under `data/`.
- Cache layer: `cache_manager.py` with DB-only runtime behavior.

## Route and Module Shape

- Public route compatibility remains stable for:
  - `/watch/<filename>`
  - `/video/<filename>`
  - `/tag/<tag>`
  - `/api/ratings/<media_hash>`
  - `/admin/cache/status`
  - `/admin/cache/refresh`
- Ratings API lives in `backend/app/api/ratings.py`.
- Admin performance APIs live in `backend/app/admin/routes.py`.

## Ratings/Favorites/Tags Lane

- One active ratings controller: `static/js/ratings.js`.
- Shared ratings widget partial: `templates/partials/rating.html`.
- Favorites endpoint wiring in templates uses `favorites_page`.
- Sidecar tags have an explicit import path:
  - `scripts/import_sidecar_tags_to_db.py`
  - `VideoDatabase.import_sidecar_tags(...)`
- Runtime tag reads use DB-backed cache APIs.

## Data Layout

- Runtime DB:
  - `data/video_metadata.db`
  - `data/video_search.db`
- Backup/export artifacts:
  - `ratings.json`
  - `views.json`
  - `tags.json`
  - `favorites.json`
  - `backup_json/`

## Testing Surfaces

- `tests/test_smoke_suite.py` for fast contract and health checks.
- `tests/test_regression_suite.py` for deeper behavior checks.
