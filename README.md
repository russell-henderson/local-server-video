# Local Video Server

Local-first media server for browsing videos, managing a media library, viewing image galleries, and refining recommendations based on view behavior, tags, and ratings.

This project is built around Flask, SQLite-backed metadata, and a lightweight local-first workflow designed for desktops, tablets, and mobile devices.

## Current status

The app is in a release-quality polish pass with the following verified improvements:

- homepage sort states and recommendation summary are explicit and understandable
- gallery filters, selection state, and lightbox context are clearer
- keyboard and focus behavior were tightened for gallery interactions
- recommendation ranking was upgraded to be behavior-aware instead of a basic popularity or recency dump
- gallery page and image-serving routes were verified to load successfully in the live app

## Highlights

- Media library and watch flow for local video playback
- Gallery with filters, grouping, favorites, and lightbox navigation
- Recommendation rail informed by tags, recency, ratings, popularity, and recent viewing patterns
- Responsive and touch-friendly UI with large hit targets and keyboard access
- SQLite-backed metadata storage with cache and JSON export/backup compatibility

## Quick start

### Local development

```powershell
# PowerShell
./dev.ps1 dev
```

### Production run

```powershell
./dev.ps1 prod
```

### Python app launch

```powershell
python main.py
```

### Admin dashboard

```bash
cd admin-dashboard
npm install
npm run dev
```

## Important URLs

- Local app: http://localhost:8000/
- Local app over local network: http://192.168.4.96:8000/
- Admin dashboard: http://localhost:3000/

## Project layout

```text
.
├── main.py
├── cache_manager.py
├── database_migration.py
├── config.py
├── performance_monitor.py
├── thumbnail_manager.py
├── static/
├── templates/
├── backend/
├── admin-dashboard/
├── docs/
├── tests/
├── TODO.md
├── README.md
├── LICENSE
└── dev.ps1
```

## Documentation map

- [TODO.md](TODO.md) — active task list and current implementation queue
- [docs/README.md](docs/README.md) — documentation hub and deeper docs index
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — project changelog and release notes
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design overview
- [docs/API.md](docs/API.md) — API contract and route reference
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — run and deployment notes
- [docs/TESTING.md](docs/TESTING.md) — testing workflow

## Git changelog

### 2026-10-09

#### Release-quality and gallery validation
- verified the gallery page and asset routes return working responses
- stabilized gallery rendering and keyboard-triggered actions
- improved gallery and recommendation clarity across the main library UX
- completed the accessibility and performance polish milestone
- refreshed root documentation and changelog to match the current project state

### 2026-03 to 2026-10

- upgraded recommendation ranking to include tags, recency, subject similarity, ratings, and popularity
- cleaned up gallery filter and selection-state clarity
- improved lightbox context and metadata presentation
- expanded mobile-first touch ergonomics and action-bar behavior
- tightened empty/loading/error states and release documentation

## Validation notes

Recent live verification confirmed:

- `GET /gallery` returned HTTP 200
- `GET /api/gallery?groups=1` returned HTTP 200 and a populated image list
- `GET /gallery/image/<sample>` returned HTTP 200 and served actual image content
- `node --check static/js/gallery.js` completed successfully

## License

MIT — see LICENSE.
