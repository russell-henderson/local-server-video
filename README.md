# Local Video Server

Last updated: April 23, 2026

Local-first media server with Flask + Docker Compose, DB-authoritative metadata, and a hash-based ratings API.

## Comprehensive documentation guide

Read these in order when onboarding or scoping work:

| Document | What it is |
|----------|------------|
| [**docs/PRD.md**](docs/PRD.md) | Product vision, goals, functional / non-functional requirements, and scope boundaries. |
| [**docs/SOURCE_OF_TRUTH.md**](docs/SOURCE_OF_TRUTH.md) | **Authoritative** runtime rules: SQLite paths, no JSON runtime fallback, **stable URL contracts**, ratings/tags/favorites guardrails. |
| [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md) | `main.py` → `factory.py` → blueprints + `legacy_runtime`, data flow, static/templates layout. |
| [**docs/API.md**](docs/API.md) | Full HTTP route table (HTML + JSON), ratings contract, search `GET /search`, admin cache, gallery APIs. |
| [**docs/DEPLOYMENT.md**](docs/DEPLOYMENT.md) | Local run, Docker Compose, `data/` mounts, `LVS_DB_PATH`. |
| [**docs/TESTING.md**](docs/TESTING.md) | Official pytest entry points (`smoke` + `regression` suites). |
| [**docs/DATA_BACKEND.md**](docs/DATA_BACKEND.md) | SQLite schema / storage detail. |
| [**docs/UI.md**](docs/UI.md) | UI patterns and design notes for the main app. |
| [**docs/PROJECT.md**](docs/PROJECT.md) | Broader project overview and extended doc map. |
| [**docs/TODOS.md**](docs/TODOS.md) | Docs-facing task index and supplemental checklists; **active agent/operator priorities** live in **[`TODO.md`](TODO.md)** (repo root). |

Supporting / deep-dive docs (performance, admin dashboard, QA, archives) are indexed from **PROJECT.md** and **docs/DOCS_INVENTORY.md**.

## Documentation Map (short)

Authoritative implementation reference:

- `docs/SOURCE_OF_TRUTH.md`

Core companions:

- `docs/PRD.md` — *what we build*
- `docs/ARCHITECTURE.md` — *how it is assembled*
- `docs/API.md` — *what each endpoint is*

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
  - `GET /search` (query `q`)
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
