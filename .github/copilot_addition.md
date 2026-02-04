Below is a **revised `copilot-instructions.md`** with the specific changes that should be made to prevent **favorites + rating icons disappearing on Quest 2** (and other “app-like” contexts such as PWA / offline / strict CORS). The core change is: **do not rely on CDN webfont-based icon sets for critical UI**. Use **inline SVG (preferred)** or **Unicode** and make icons a **reusable template partial** used on every screen.

---

# Copilot Instructions — Local Video Server

## Project Overview

**Local Video Server** is a Flask-based application for managing a personal video library and image gallery with responsive themes, cross-platform support (desktop/mobile/VR), performance optimization, and a Next.js admin dashboard for performance monitoring. Source of truth for current work: `docs/TODO.md` (top-to-bottom priority order).

---

## Architecture Essentials

### Core Components

| Module                   | Purpose                                                                          | Key Patterns                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `main.py`                | Flask app, video routes, gallery routes, thumbnail orchestration                 | Route handlers w/ `@performance_monitor` decorator; cache-driven metadata pulls                      |
| `cache_manager.py`       | In-memory + SQLite cache for videos, images, ratings, views, tags, favorites     | Dual-backend (JSON fallback); TTL-based refresh; thread-safe with locks                              |
| `database_migration.py`  | SQLite schema & migrations                                                       | Uses `sqlite3.Row` for dict-like access; foreign keys on `videos.filename`; soft deletes via CASCADE |
| `file_watcher.py`        | Debounced directory monitoring w/ batch processing                               | Watchdog observer; background thread; dedup via checksum                                             |
| `config.py`              | Dataclass-based config w/ cascade (env vars → `.env` → `config.json` → defaults) | `ServerConfig` validation; `ConfigManager` singleton                                                 |
| `performance_monitor.py` | Optional route latency tracking & optional perf reporting                        | Non-fatal import; can disable monitoring if unavailable                                              |
| `admin-dashboard/`       | Next.js app for admin performance dashboard                                      | Separate app; fetches `/admin/performance.json` from Flask backend                                   |

### Data Flow

1. **Video List** (`index`) → `cache.get_all_video_data()` → SQLite/JSON → Frontend (sorted by date/views/rating)
2. **Favorites Page** (`favorites`) → Filter `cache.get_all_video_data()` by `cache.get_favorites()` → Paginated frontend
3. **Popular Page** (`popular`) → `cache.get_all_video_data(sort='views', reverse=True)` → Paginated frontend
4. **Watch Page** → `cache.get_ratings()`, `get_views()`, `get_tags()`, `get_favorites()` (bulk loads) → Single template render
5. **Gallery Page** (`gallery`) → `cache.get_all_image_data()` → SQLite/JSON → Frontend (grouped by virtual groups)
6. **Metadata Write** (ratings, views, tags, favorites) → `POST /api/*` → DB write → Cache invalidate → Re-fetch next read
7. **File Discovery** → `file_watcher` detects changes → calls `generate_thumbnail_async()` → Queueing deduped via `thumbnail_manager`
8. **Admin Dashboard** → Fetches `/admin/performance.json` → Displays metrics with charts

### Key Design Decisions

* **Cache-Driven Architecture**: All routes pull from `cache` object first. DB is single source of truth; cache validates against file existence.
* **Nullable Ratings/Views**: A video with no rating shows `0`; views default to `0` if unset.
* **SQLite + JSON Fallback**: If DB fails, reads JSON files (`ratings.json`, etc.). Writes still go to DB if available.
* **Background Thumbnail Generation**: Non-blocking; new files trigger `generate_thumbnail_async()` queued by filename dedup.
* **Thread Safety**: `cache_manager` and `database_migration` use `threading.RLock()` for concurrent access.
* **Cross-Device Accessibility**: 44px+ touch targets, no hover dependencies, PWA caching for mobile performance.
* **Image Gallery**: Supports loose images and virtual groups; favorites work across both; selection mode for bulk operations.
* **Admin Dashboard**: Separate Next.js app for performance monitoring; uses Recharts for visualizations.

---

## VR/Cross-Platform Critical Rule: Icon Reliability

### Why this matters

Quest 2 (Oculus Browser) and PWA-like contexts can fail to render icon fonts (Font Awesome, etc.) when:

* webfont fetches are blocked, slow, or fail due to CORS
* offline or cached state does not include fonts
* CDN delivery is inconsistent

When icon fonts fail, `<i class="fa ...">` renders as blank UI.

### Required Strategy

**Critical UI icons (favorites, ratings, nav icons) must not depend on external webfont icon libraries.**

**Preferred:** Inline SVG icons shipped with the app
**Acceptable fallback:** Unicode glyphs (♥/♡, ★/☆)
**Allowed only if self-hosted:** Font Awesome, but must be fully local and included in `sw.js` caches

### Implementation Pattern

* Create a single icon component layer used everywhere:

  * `templates/partials/icons.html` with macros like:

    * `favorite_icon(is_on: bool)`
    * `star_icon(is_on: bool)`
* All templates render icons through these macros, never directly using `fa-*` classes.
* All JS toggles state via app-owned classes/attributes:

  * Favorites: toggle `.is-on` or `data-favorite="1|0"`
  * Ratings: toggle `.is-active` on stars

**Do not toggle `fas/far` or `fa-solid/fa-regular` classes.**

---

## Development Workflow

### Starting the Server

```powershell
# Development with auto-reload
.\dev.ps1 dev

# Production (no debug, optimizations enabled)
.\dev.ps1 prod

# Install/update dependencies
.\dev.ps1 install
```

### Starting the Admin Dashboard

```bash
cd admin-dashboard
npm install
npm run dev  # Runs on http://localhost:3000
npm run build && npm start  # Production
```

### Running Quality Checks

```powershell
.\dev.ps1 lint          # Python syntax, HTML, JS file checks
.\dev.ps1 test          # Placeholder; extend with real test suite
.\dev.ps1 health        # healthcheck.py + performance_monitor.py --report
.\dev.ps1 clean         # Remove .pyc, __pycache__, large logs

# Admin dashboard linting
cd admin-dashboard && npm run lint
```

### Database & Cache Maintenance

```powershell
.\dev.ps1 reindex       # Force video reindexing
.\dev.ps1 backup        # Timestamped backup of video_metadata.db & video_cache.db
```

---

## Code Patterns & Conventions

### Routes & Performance Monitoring

```python
@app.route("/watch/<path:filename>")
@performance_monitor("route_watch")
def watch_video(filename: str):
    # Always check file existence first
    if not get_video_path(filename).exists():
        abort(404)

    # Bulk load all metadata in one call pattern
    ratings = cache.get_ratings()
    views = cache.get_views()
    all_tags = cache.get_tags()

    # Then extract for current video
    current_tags = all_tags.get(filename, [])
```

**Rules:**

* Decorate with `@performance_monitor("descriptive_name")` for latency tracking (non-fatal if disabled).
* Always pull full metadata once, then filter. Do not call `cache.get_*(filename)`.
* Use `cache.get_all_video_data(sort_param, reverse)` for sorted listings.

### Cache Invalidation

When writing (ratings, tags, views, favorites):

1. Write to DB (or JSON if DB unavailable).
2. Call cache method to invalidate (e.g., `cache.invalidate_ratings()`).
3. Re-fetch fresh data on next read.

### Template Patterns

* **Single Watch Page**: `templates/watch.html` includes `_player.html` (reusable player partial).
* **Gallery Page**: `templates/gallery.html` with selection mode, groups grid, images grid.
* **Icons**:

  * All favorites + rating icons must come from `templates/partials/icons.html`.
  * Rating partial `templates/partials/rating.html` must call icon macros, not Font Awesome.
* **Rating Interaction**: `<div class="rating" data-filename="...">` → `static/js/ratings.js` (pointer + click + keyboard support; VR-safe).
* **Video Cards**: Responsive grid; thumbnail lazy-load with fallback GIF; `data-role="video-card"` for JS targeting.
* **Gallery Items**: `data-filename` for selection; shift-click for ranges.

### JavaScript Conventions

* **Player**: `static/js/player.js` → `class VideoPlayer { ... }` wraps `<video>` + controls; keyboard shortcuts (k/space=play, j/l=skip±10s, f=fullscreen).
* **Favorites**:

  * Must toggle `.is-on` or a `data-state` attribute on the button/container.
  * Must not toggle Font Awesome classes.
* **Ratings**:

  * Stars use app-owned DOM structure with `data-rating-value`.
  * Toggle `.is-active` for star visual state.
  * Must not toggle Font Awesome classes.
* **Gallery Selection**: `static/js/gallery.js` → Handles selection mode, shift-click ranges, bulk actions.
* **Dark Mode**: Enabled by default; toggle adds/removes `dark-mode` class on `document.documentElement` + `body`.

### Admin Dashboard Patterns

* **Data Fetching**: Fetch from `/admin/performance.json`; use React hooks for live updates.
* **Charts**: Use Recharts for metrics visualization.
* **Layout**: Tailwind CSS for responsive design.

---

## File Organization & Naming

```
repo/
├── main.py                      # Flask app (videos + gallery)
├── cache_manager.py             # Metadata cache (DB + JSON)
├── database_migration.py        # SQLite schema & queries
├── file_watcher.py              # Directory monitoring
├── config.py                    # Configuration (env → .env → config.json → defaults)
├── performance_monitor.py       # Optional route profiling
├── thumbnail_manager.py         # Async thumbnail generation
├── admin-dashboard/             # Next.js admin performance dashboard
│   ├── src/                     # React components
│   ├── package.json             # Node dependencies
│   └── ...
├── images/                      # User image files for gallery
├── videos/                      # User video files
├── static/
│   ├── styles.css               # Single CSS entry point (no duplicates)
│   ├── sw.js                    # Service worker for PWA caching
│   ├── js/
│   │   ├── player.js            # Video player class
│   │   ├── ratings.js           # Rating star interactions
│   │   ├── tags.js              # Tag management
│   │   ├── gallery.js           # Gallery selection logic
│   │   ├── ui.js                # Dark mode toggle
│   │   └── favorites.js         # Favorites interactions (if not already present)
│   └── css/
│       └── player-controls.css  # Player-specific styles
├── templates/
│   ├── watch.html               # Single watch page (includes _player.html)
│   ├── index.html               # Video list & grid
│   ├── favorites.html           # Favorites page with sorting/pagination
│   ├── popular.html             # Popular videos by view count
│   ├── gallery.html             # Image gallery with groups
│   ├── _base.html               # Base layout
│   ├── _navbar.html             # Navigation
│   ├── _player.html             # Reusable player component
│   └── partials/
│       ├── rating.html          # Rating star partial (uses icons macro)
│       └── icons.html           # Icon macros for favorite + rating stars
├── docs/                        # Current, active documentation
│   ├── ADMIN_DASHBOARD.md       # Admin dashboard spec
│   ├── IMPLEMENTATION.md        # Architecture + dev workflow
│   ├── PERFORMANCE.md           # Optimization notes
│   ├── UI.md                    # UI patterns & player behavior
│   └── TODO.md                  # Single source of truth for current work
├── archive/                     # Deprecated systems, cost analyses, old designs
├── .github/
│   └── copilot-instructions.md  # This file
└── dev.ps1                      # PowerShell command wrapper
```

**Critical Rules:**

* One `static/styles.css` only. No `app.css`, `theme.css`, etc.
* One `templates/watch.html` only. No backup copies (rename old ones to `watch.html.backup`).
* One `templates/partials/rating.html`. Reused wherever ratings are shown.
* Critical icons must be inline SVG or Unicode, not CDN icon fonts.
* All design experiments → `archive/` with a README explaining the rationale.

---

## VR/Cross-Platform Specifics

* **No Hover Interactions**: All controls must work with pointer events, click, and keyboard.
* **Touch Targets ≥ 44px**: Rating stars, buttons, links with padding and min-size.
* **Rating Visibility**: Always render the rating partial on `watch.html`. Do not hide in VR-only containers.
* **Icon Visibility**: Favorites and rating icons must render without external icon fonts.
* **User Agent Testing**: Add Playwright tests with Quest 2 user agent (e.g., `Mozilla/5.0 ... OculusBrowser`).
* **Theme Support**: App supports Dark/Light, Glassmorphic/Neomorphic/Hybrid themes. All must work on VR.
* **PWA Features**:

  * Service worker must cache all critical static UI assets that affect interaction UI (including any icons if stored as separate assets).

---

## Configuration & Environment

**Config Cascade** (lowest → highest priority):

1. Hardcoded defaults in `ServerConfig`
2. `config.json` (if exists)
3. `.env` file (if exists)
4. Environment variables with `LVS_` prefix

**Example:**

```bash
# .env or ENV
LVS_PORT=5001
LVS_DEBUG=true
LVS_VIDEO_DIRECTORY=~/my-videos
LVS_IMAGE_DIRECTORY=~/my-images
```

Config is loaded once at startup via `config_manager.load_config()`. To reload: `config_manager.reload_config()`.

---

## Testing & Quality

* **Unit Tests**: Test `cache_manager`, `database_migration`, `config` in isolation (mock filesystem/DB if needed).
* **Integration Tests**: Spin up Flask app, test routes, verify cache → DB → HTTP flows.
* **E2E Tests**: Use Playwright for cross-platform (desktop, mobile, VR user agents) interaction flows.
* **Performance Tests**: Measure route latency via `@performance_monitor`; compare before/after optimizations.
* **VR UI Regression**:

  * Add an E2E assertion that favorites and rating icons are visible (not blank) on key routes.

Run with:

```powershell
.\dev.ps1 test
```

---

## When Uncertain

1. Propose the smallest, reversible change. Do not refactor unrelated code.
2. Check `docs/TODO.md` acceptance criteria. Implement exactly as specified.
3. Prefer existing patterns. If the codebase uses a style, follow it.
4. Document edge cases. Add a comment explaining why a workaround is needed.
5. Test on multiple platforms. Desktop, mobile, VR if the change affects UI.

---

## Safety Rails

* Do not remove files unless the task explicitly instructs it OR a replacement exists.
* Do not change API contracts without updating tests & docs.
* Preserve `.github/copilot-instructions.md`. Update it when architectural patterns change.
* Always check `docs/TODO.md` first. It is the single source of truth for priorities.

---

## First Actions for New Issues

1. Read `docs/TODO.md` from the top.
2. Check acceptance criteria for the relevant task.
3. Review the files in "Architecture Essentials" to understand the current implementation.
4. Run `.\dev.ps1 dev` to start the server locally; test your changes in real-time.
5. Use `.\dev.ps1 lint` and `.\dev.ps1 test` before committing.

---

Updated “Copilot instruction” addendum (Docker)

Add this section under VR/Cross-Platform or Workflow:

Docker Runtime Notes

Always test from a non-localhost origin (Quest must access the container via LAN IP/hostname).

Keep port mappings stable (compose ports: pinned).

Avoid external icon font CDNs; inline SVG or Unicode prevents CORS/font issues across containerized deployments.

If service worker is enabled, ensure sw.js caches only assets present inside the container and bump cache version per deploy.

If behind a reverse proxy or subpath, validate static URLs + SW scope on Quest.

Bottom line

If you implement inline SVG/Unicode icons, Docker doesn’t introduce any extra risk for the icons themselves.

Docker only matters if you keep external webfonts, rely on service worker caching, or have reverse proxy pathing.
