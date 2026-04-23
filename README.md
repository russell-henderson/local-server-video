# Local Video Server

Last updated: April 23, 2026

Local-first media server with Flask + Docker Compose, DB-authoritative metadata, and a hash-based ratings API.

## Documentation Map

Authoritative implementation reference:

- `docs/SOURCE_OF_TRUTH.md`

Supporting docs:

- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/DEPLOYMENT.md`
- `docs/TESTING.md`

## Current Architecture

- `main.py` is a thin bootstrap entrypoint.
- `backend/app/factory.py` is the app construction path.
- Route families are registered via blueprints under `backend/app/`.
- Runtime metadata authority is SQLite in `data/video_metadata.db`.
- Runtime search/cache DB is `data/video_search.db`.
- JSON files are export/backup artifacts only (not runtime fallback).

## Runtime Commands

Local Flask run:

```powershell
python main.py
```

Docker Compose run:

```powershell
docker compose up -d --build
docker compose ps
```

## Ratings and Compatibility Contracts

- Canonical ratings API: `/api/ratings/<path:media_hash>`.
- Legacy ratings route `/rate` remains available as compatibility bridge.
- Required compatibility routes remain stable:
  - `/watch/<filename>`
  - `/video/<filename>`
  - `/tag/<tag>`
  - `/admin/cache/status`
  - `/admin/cache/refresh`

## Testing

Official reporting surface:

```powershell
python -m pytest -q tests/test_smoke_suite.py tests/test_regression_suite.py
```

The fragmented legacy suite surface is retired from release validation.

## License

MIT - see `LICENSE`.
