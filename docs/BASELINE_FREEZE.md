# Phase 0 Baseline Freeze

This file captures the pre-refactor baseline required by the structural cleanup plan.

## Snapshot Inventory

- Timestamped snapshot directory: `backups/phase0_baseline_20260423_114555`
- Captured runtime DB artifacts (when present):
  - `data/video_metadata.db`
  - `data/video_search.db`
  - `video_metadata.db`
  - `video_search.db`
- Captured legacy JSON artifacts (when present):
  - `ratings.json`
  - `views.json`
  - `tags.json`
  - `favorites.json`
- Captured backup folder snapshot (when present):
  - `backup_json/` -> `backups/phase0_baseline_20260423_114555/backup_json_snapshot`

## Protected Public Route Contract (Must Not Break)

- `GET /watch/<filename>`
- `GET /video/<filename>`
- `GET /tag/<tag>`
- `GET|POST /api/ratings/<media_hash>`
- `GET /admin/cache/status`
- `POST /admin/cache/refresh`

## Current Page/Behavior Contract Baseline

- Ratings write endpoint currently used by frontend widgets: `POST /rate` with `{ filename, rating }`.
- New ratings API exists: `/api/ratings/<media_hash>` with `{ value }` write payload and summary response.
- Favorites page endpoint function is `favorites_page`, but template links currently call `url_for('favorites')` in places.
- Tags runtime path currently merges DB/cache tags with sidecar tags for several read endpoints.

## Ratings/Favorites/Tags Script and Callsite Inventory

### Script loads

- Global base load:
  - `templates/_base.html` -> `static/js/ratings.js`
- Additional page loads:
  - `templates/index.html` -> `static/js/rating.js` (module)
  - `templates/watch.html` -> `static/js/rating.js` (module)
  - `templates/favorites.html` -> `static/js/rating.js` (module)

### Ratings callsites

- Legacy write path:
  - `static/js/rating.js` -> `POST /rate`
  - `static/js/ratings.js` -> `POST /rate`
  - `static/optimized-utils.js` -> delegated rating handler -> `POST /rate`
- API contract path:
  - `backend/app/api/ratings.py` -> `GET|POST /api/ratings/<media_hash>`

### Favorites callsites

- Backend:
  - `POST /favorite`
  - `GET /favorites` (endpoint name `favorites_page`)
- Frontend:
  - `static/favorites.js`
  - `static/optimized-utils.js`

### Tags callsites

- Backend writes:
  - `POST /tag`
  - `POST /delete_tag`
- Backend reads:
  - `GET /tags`
  - `GET /tag/<tag>`
  - `GET /api/tags/popular`
  - `GET /api/tags/video`

## Known Drift / Known Failures to Correct

- Duplicate ratings controllers (`rating.js` and `ratings.js`) are both active.
- Favorites template route wiring mismatch (`url_for('favorites')` vs endpoint `favorites_page`).
- Runtime tag truth is mixed due to sidecar merge in read paths.
- Runtime data behavior remains mixed between DB-first and JSON fallback in cache/runtime services.
