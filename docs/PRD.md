# Product Requirements Document (PRD)

**Product:** Local Video Server (LVS)  
**Last updated:** 2026-04-23  
**Audience:** Contributors, operators, and anyone scoping work against the actual codebase.

---

## 1. Vision

Local Video Server is a **local-first** Flask application for browsing, searching, and playing a personal video library from the LAN or same machine. It emphasizes **SQLite-backed metadata** (ratings, favorites, tags, views, gallery grouping), a **simple web UI**, optional **Docker Compose** deployment, and a **small, explicit HTTP surface** for humans and light automation.

---

## 2. Goals

| ID | Goal | Notes |
|----|------|--------|
| G1 | **Browse and play** videos with thumbnails and a watch experience | `/`, `/watch/<filename>`, streaming routes |
| G2 | **Discover** content via tags, popularity, favorites, search, and gallery | DB-backed lists and ranking |
| G3 | **Persist preference state** (ratings, favorites, tags) in **SQLite**, not JSON-at-runtime | See `docs/SOURCE_OF_TRUTH.md` |
| G4 | **Stable compatibility** for bookmarked URLs and integrated clients | Contract routes documented in SOF + `docs/API.md` |
| G5 | **Operable deployment** via `main.py` and Docker with documented data mounts | `docs/DEPLOYMENT.md` |
| G6 | **Regression safety** via two official pytest entry points | `docs/TESTING.md` |

---

## 3. Non-goals (current product)

- Multi-tenant SaaS auth, billing, or public internet hardening as a first-class product.
- Replacing SQLite with another primary store without an explicit migration project.
- Automatic **runtime** reads from JSON backups (JSON is export/backup only).
- Expanding the official automated test surface beyond the two suite files without an explicit decision (see `docs/TESTING.md`).

---

## 4. Primary users

1. **Home operator** — runs the server on a PC or NAS, opens the browser, curates library metadata.
2. **Household viewer** — uses gallery, watch, and search; may rate or favorite if exposed in UI.
3. **Integrator / device** — uses stable JSON routes (e.g. ratings hash API) where documented.

---

## 5. Functional requirements

### 5.1 Library and playback

- **FR-1** Index and list videos from configured storage; show thumbnails where available.
- **FR-2** Stream or serve video for watch pages (`/watch/...`, `/video/...`) without breaking existing filename-in-path URLs.
- **FR-3** Record views where the product defines view tracking (see implementation).

### 5.2 Discovery and organization

- **FR-4** Tag videos; list by tag; expose tag APIs used by the UI.
- **FR-5** Favorites list and toggle behavior backed by DB.
- **FR-6** Popularity / ordering surfaces as implemented (e.g. popular page).
- **FR-7** **Search:** `GET /search` with query parameter `q` (token AND, case-insensitive partial match over filename/title/tags with relevance ordering). Navbar form must remain `GET` with `name="q"`.

### 5.3 Ratings

- **FR-8** Canonical ratings API: `GET|POST /api/ratings/<media_hash>` (JSON).
- **FR-9** Legacy `POST /rate` remains until fully retired; documented in `docs/API.md`.

### 5.4 Gallery (images)

- **FR-10** Gallery pages and image APIs as registered in `backend/app/factory.py` (groups, similar, CRUD-style group APIs).

### 5.5 Admin and maintenance

- **FR-11** Cache status and refresh: `GET /admin/cache/status`, `POST /admin/cache/refresh`.
- **FR-12** Optional admin/metadata prune and analytics routes as implemented (see `docs/API.md`).

### 5.6 Health

- **FR-13** Lightweight health: `GET /ping` returns JSON OK for monitors.

### 5.7 Static / special pages

- **FR-14** Standalone `links` page route as implemented (decorative / utility HTML + CSS, not part of main app shell unless wired).

---

## 6. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF-1 | **Data authority:** runtime reads/writes for metadata go through SQLite paths defined in SOF (`data/video_metadata.db`, `data/video_search.db`). |
| NF-2 | **Config:** respect `config.py` and `LVS_*` env overrides (see `docs/DEPLOYMENT.md`). |
| NF-3 | **Observability:** optional performance hooks from legacy runtime where enabled. |
| NF-4 | **Quality gate:** changes that affect contracts should update `docs/API.md` and/or `docs/SOURCE_OF_TRUTH.md` and pass smoke + regression suites when the local DB is healthy. |

---

## 7. Success metrics (engineering)

- Smoke + regression suites green on CI / healthy dev DB.
- No undocumented changes to **stable route contracts** listed in `docs/SOURCE_OF_TRUTH.md`.
- README “documentation map” stays accurate with this PRD and sibling docs.

---

## 8. Related documents

| Document | Role |
|----------|------|
| `docs/SOURCE_OF_TRUTH.md` | Runtime policy + stable public routes |
| `docs/ARCHITECTURE.md` | Components, blueprints, data layout |
| `docs/API.md` | HTTP route and JSON contract reference |
| `docs/DEPLOYMENT.md` | Run and mount paths |
| `docs/TESTING.md` | Official pytest entry points |
| `docs/DATA_BACKEND.md` | Schema / storage detail |
| `docs/UI.md` | UI conventions |
| `README.md` | Quick start + doc index |

---

## 9. Revision history

| Date | Change |
|------|--------|
| 2026-04-23 | Initial PRD aligned with `factory.py`, SOF, and README doc map. |
