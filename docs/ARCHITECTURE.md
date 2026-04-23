# Local Video Server Architecture

**Last updated:** 2026-04-23

This document describes how the running system is assembled: process entry, Flask app factory, route registration, data stores, and front-end assets.

---

## 1. High-level diagram

```text
┌─────────────────────────────────────────────────────────────┐
│  main.py  (thin bootstrap: create_app, run or WSGI export)   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  backend/app/factory.py :: create_app()                      │
│  • Flask(template_folder, static_folder from repo root)     │
│  • Registers blueprints + ratings API + admin routes         │
│  • Registers legacy view functions on concrete URL rules     │
│  • Hooks: before_request / after_request / teardown          │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  Blueprint routers   legacy_runtime.*    static/js, CSS
  (media, tags,       (index, watch,      templates/
   gallery,            search, gallery,   Jinja partials
   metadata)           analytics, …)
```

---

## 2. Runtime stack

| Layer | Technology |
|-------|------------|
| App server | Flask + Jinja2 |
| Optional container | Docker Compose (`docker-compose.yml`) |
| Primary metadata store | SQLite `data/video_metadata.db` |
| Search / cache DB | SQLite `data/video_search.db` |
| Thumbnails / static | `static/` (e.g. `static/thumbnails/`) |
| Video files | Configured directory (commonly `videos/`) |

**Policy:** JSON files in the repo root are **export/backup** artifacts, not a silent runtime fallback. See `docs/SOURCE_OF_TRUTH.md`.

---

## 3. Entry points

| Path | Role |
|------|------|
| `main.py` | Imports `create_app` from `backend.app.factory`, runs the dev server or exposes `app` for WSGI. |
| `backend/app/factory.py` | Single place that constructs the Flask `app` and attaches all routes. |
| `backend/app/legacy_runtime.py` | Large compatibility module: most HTML and JSON handlers, DB/cache interactions, and perf hooks still live here while route families are partially split into blueprints. |

Blueprints registered from `create_app()`:

- `backend/app/media/routes.py` — `media_bp`
- `backend/app/tags/routes.py` — `tags_bp`
- `backend/app/gallery/routes.py` — `gallery_bp`
- `backend/app/metadata/routes.py` — `metadata_bp`
- `backend/app/api/ratings.py` — `register_ratings_api(app)`
- `backend/app/admin/routes.py` — `register_admin_routes(app)`

Additional URL rules are bound **explicitly** in `factory.py` to preserve **endpoint names** used in templates (`url_for(...)`), e.g. `index`, `watch_video`, `search_page`, `random_video`, `gallery_group`, etc.

---

## 4. Request path (simplified)

1. Flask matches URL to a view (blueprint or legacy).
2. Views use `cache_manager` / `database_migration.VideoDatabase` (and related helpers) for DB-backed reads and writes.
3. HTML responses render templates under `templates/`; shared chrome includes `_base.html`, `_navbar.html`.
4. JSON APIs return structured payloads for ratings, tags, gallery, admin cache, analytics as applicable.

---

## 5. Front end

| Area | Location |
|------|----------|
| Global styles | `static/styles.css` (consolidated app chrome, cards, navbar) |
| Links-only page | `templates/links.html` + `static/css/links.css` (standalone layout, no app navbar) |
| Ratings widget | `static/js/ratings.js` + partials under `templates/partials/` |
| Other JS | `static/js/*.js`, `static/favorites.js`, etc. |

**UI documentation:** `docs/UI.md`.

---

## 6. Data layout (runtime)

| Artifact | Purpose |
|----------|---------|
| `data/video_metadata.db` | Ratings, favorites, tags, views, gallery metadata, etc. |
| `data/video_search.db` | Search index / cache backing `/search` |
| `ratings.json`, `tags.json`, … | Backup/export; not automatic runtime authority |

**Deployment mounts:** see `docs/DEPLOYMENT.md` (`./data` → `/app/data`, `LVS_DB_PATH`).

---

## 7. Testing architecture

Official automated suites (see `docs/TESTING.md`):

- `tests/test_smoke_suite.py` — boot, key routes, navbar search form contract.
- `tests/test_regression_suite.py` — deeper behavior (tags, search ranking, cards, etc.).

---

## 8. Related documents

- `docs/PRD.md` — product goals and functional scope  
- `docs/API.md` — route-level reference  
- `docs/SOURCE_OF_TRUTH.md` — non-negotiable runtime policies  
- `docs/DATA_BACKEND.md` — schema and storage details  
- `docs/PERFORMANCE_MONITORING.md` — metrics hooks  
