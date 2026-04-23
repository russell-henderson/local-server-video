# Source Of Truth

Last updated: 2026-04-23

## Runtime Policy

- Runtime metadata authority is SQLite only.
- Runtime DB paths:
  - `data/video_metadata.db`
  - `data/video_search.db`
- Automatic JSON fallback is not allowed in runtime code.
- JSON files are explicit export/backup artifacts only.

## Public Route Contract (Stable)

- `/watch/<filename>`
- `/video/<filename>`
- `/tag/<tag>`
- `/api/ratings/<media_hash>`
- `/admin/cache/status`
- `/admin/cache/refresh`

## Ratings/Favorites/Tags Guardrails

- Canonical ratings controller is `static/js/ratings.js`.
- Keep legacy `/rate` compatibility path until every ratings surface is validated against the canonical flow.
- Favorites endpoint is `favorites_page` for template `url_for(...)` wiring.
- Runtime tags reads/writes are DB-backed (with explicit sidecar import path).
- Metadata controls contract is hard-required on every video surface:
  - favorite icon + rating stars
  - DB-backed current visual state
  - interactive updates via shared controller path
- Rendering contract is shared and centralized:
  - `templates/partials/video_metadata_controls.html` for favorite+rating controls
  - `templates/partials/rating.html` for star rendering internals
  - no page-specific duplicate or static-only metadata control markup

## Deployment Topology

- Flask + Docker Compose remain the runtime architecture.
- `docker-compose.yml` mounts DB files from `./data` into `/app/data`.
- `LVS_DB_PATH` points to `data/video_metadata.db`.

## Test Reporting Surfaces

- `tests/test_smoke_suite.py`
- `tests/test_regression_suite.py`

Legacy fragmented suite reporting is retired; release validation reports through the two suites above.
