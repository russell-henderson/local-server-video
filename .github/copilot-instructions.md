# Copilot Instructions — Local Video Server

## Project Overview

**Local Video Server** is a Flask-based streaming application for managing a personal video library with responsive themes, cross-platform support (desktop/mobile/VR), and performance optimization. Source of truth for current work: `TODO.md` (top-to-bottom priority order).

---

## Architecture Essentials

### Core Components

| Module | Purpose | Key Patterns |
|--------|---------|--------------|
| `main.py` | Flask app, video routes, thumbnail orchestration | Route handlers w/ `@performance_monitor` decorator; cache-driven metadata pulls |
| `cache_manager.py` | In-memory + SQLite cache for videos, ratings, views, tags, favorites | Dual-backend (JSON fallback); TTL-based refresh; thread-safe with locks |
| `database_migration.py` | SQLite schema & migrations | Uses `sqlite3.Row` for dict-like access; foreign keys on `videos.filename`; soft deletes via CASCADE |
| `file_watcher.py` | Debounced directory monitoring w/ batch processing | Watchdog observer; background thread; dedup via checksum |
| `config.py` | Dataclass-based config w/ cascade (env vars → `.env` → `config.json` → defaults) | `ServerConfig` validation; `ConfigManager` singleton |
| `performance_monitor.py` | Optional route latency tracking & optional perf reporting | Non-fatal import; can disable monitoring if unavailable |

### Data Flow

1. **Video List** (`index`) → `cache.get_all_video_data()` → SQLite/JSON → Frontend (sorted by date/views/rating)
2. **Favorites Page** (`favorites`) → Filter `cache.get_all_video_data()` by `cache.get_favorites()` → Paginated frontend
3. **Popular Page** (`popular`) → `cache.get_all_video_data(sort='views', reverse=True)` → Paginated frontend
4. **Watch Page** → `cache.get_ratings()`, `get_views()`, `get_tags()`, `get_favorites()` (bulk loads) → Single template render
5. **Metadata Write** (ratings, views, tags) → `POST /api/*` → DB write → Cache invalidate → Re-fetch next read
6. **File Discovery** → `file_watcher` detects changes → calls `generate_thumbnail_async()` → Queueing deduped via `thumbnail_manager`

### Key Design Decisions

- **Cache-Driven Architecture**: All routes pull from `cache` object first. DB is single source of truth; cache validates against file existence.
- **Nullable Ratings/Views**: A video with no rating shows `0`; views default to `0` if unset.
- **SQLite + JSON Fallback**: If DB fails, reads JSON files (`ratings.json`, etc.). Writes still go to DB if available.
- **Background Thumbnail Generation**: Non-blocking; new files trigger `generate_thumbnail_async()` queued by filename dedup.
- **Thread Safety**: `cache_manager` and `database_migration` use `threading.RLock()` for concurrent access.
- **Cross-Device Accessibility**: 44px+ touch targets, no hover dependencies, PWA caching for mobile performance.

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

### Running Quality Checks

```powershell
.\dev.ps1 lint          # Python syntax, HTML, JS file checks
.\dev.ps1 test          # Placeholder; extend with real test suite
.\dev.ps1 health        # healthcheck.py + performance_monitor.py --report
.\dev.ps1 clean         # Remove .pyc, __pycache__, large logs
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
- Decorate with `@performance_monitor("descriptive_name")` for latency tracking (non-fatal if disabled).
- Always pull full metadata once, then filter—don't call `cache.get_*(filename)`.
- Use `cache.get_all_video_data(sort_param, reverse)` for sorted listings.

### Cache Invalidation

When writing (ratings, tags, views, favorites):
1. Write to DB (or JSON if DB unavailable).
2. Call cache method to invalidate (e.g., `cache.invalidate_ratings()`).
3. Re-fetch fresh data on next read.

### Template Patterns

- **Single Watch Page**: `templates/watch.html` includes `_player.html` (reusable player partial).
- **Rating Interaction**: `<div class="rating" data-filename="...">` → `static/js/ratings.js` (pointer + click + keyboard support; VR-safe).
- **Video Cards**: Responsive grid; thumbnail lazy-load with fallback GIF; `data-role="video-card"` for JS targeting.

### JavaScript Conventions

- **Player**: `static/js/player.js` → `class VideoPlayer { ... }` wraps `<video>` + controls; keyboard shortcuts (k/space=play, j/l=skip±10s, f=fullscreen).
- **Ratings/Tags**: Module functions (not classes); use `data-filename` to find context; emit fetch requests on DOM changes.
- **Dark Mode**: Enabled by default; toggle adds/removes `dark-mode` class on `document.documentElement` + `body`.

---

## File Organization & Naming

```
repo/
├── main.py                      # Flask app
├── cache_manager.py             # Metadata cache (DB + JSON)
├── database_migration.py        # SQLite schema & queries
├── file_watcher.py              # Directory monitoring
├── config.py                    # Configuration (env → .env → config.json → defaults)
├── performance_monitor.py       # Optional route profiling
├── thumbnail_manager.py         # Async thumbnail generation
├── static/
│   ├── styles.css               # **Single CSS entry point** (no duplicates)
│   ├── sw.js                    # Service worker for PWA caching
│   ├── js/
│   │   ├── player.js            # Video player class
│   │   ├── ratings.js           # Rating star interactions
│   │   ├── tags.js              # Tag management
│   │   ├── ui.js                # Dark mode toggle
│   └── css/
│       └── player-controls.css  # Player-specific styles
├── templates/
│   ├── watch.html               # **Single watch page** (includes _player.html)
│   ├── index.html               # Video list & grid
│   ├── favorites.html           # Favorites page with sorting/pagination
│   ├── popular.html             # Popular videos by view count
│   ├── _base.html               # Base layout
│   ├── _navbar.html             # Navigation
│   ├── _player.html             # Reusable player component
│   └── partials/
│       └── rating.html          # Rating star partial (included in watch.html)
├── docs/                        # Current, active documentation
│   ├── IMPLEMENTATION.md        # Architecture + dev workflow
│   ├── PERFORMANCE.md           # Optimization notes
│   ├── UI.md                    # UI patterns & player behavior
│   └── TODOS.md                 # High-level roadmap
├── archive/                     # Deprecated systems, cost analyses, old designs
├── .github/
│   └── copilot-instructions.md  # This file
├── TODO.md                      # **Single source of truth for current work**
└── dev.ps1                      # PowerShell command wrapper
```

**Critical Rules:**
- One `static/styles.css` only—no `app.css`, `theme.css`, etc.
- One `templates/watch.html`—no backup copies (rename old ones to `watch.html.backup`).
- One `templates/partials/rating.html`—reused wherever ratings are shown.
- All design experiments → `archive/` with a README explaining the rationale.

---

## Task Workflow (from TODO.md)

1. **Read `TODO.md` top-to-bottom** — tasks are ordered by dependency & priority.
2. **Pick the highest unchecked task** whose dependencies are met.
3. **Implement the smallest correct change set** — avoid scope creep.
4. **Update TODO.md** when done:
   - Change `- [ ]` to `- [x]`
   - Add a note: `Completed in PR_number (commit abc123).`
5. **Open a PR** with:
   - Title: `[scope] short summary` (e.g., `ratings: make stars work on Quest`)
   - Body: summary, linked TODO items, acceptance results, test evidence
6. **All tests must pass locally & in CI** before merging.

---

## VR/Cross-Platform Specifics

- **No Hover Interactions**: All controls must work with pointer events, click, and keyboard.
- **Touch Targets ≥ 44px**: Rating stars, buttons, links with padding and min-size.
- **Rating Visibility**: Always render the rating partial on `watch.html`; do not hide in VR-only containers.
- **User Agent Testing**: Add Playwright tests with Quest 2 user agent (e.g., `Mozilla/5.0 ... OculusBrowser`).
- **Theme Support**: App supports Dark/Light, Glassmorphic/Neomorphic/Hybrid themes; all must work on VR.
- **PWA Features**: Service worker caches static assets for offline access on mobile devices.

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
```

Config is loaded once at startup via `config_manager.load_config()`. To reload: `config_manager.reload_config()`.

---

## Testing & Quality

- **Unit Tests**: Test `cache_manager`, `database_migration`, `config` in isolation (mock filesystem/DB if needed).
- **Integration Tests**: Spin up Flask app, test routes, verify cache → DB → HTTP flows.
- **E2E Tests**: Use Playwright for cross-platform (desktop, mobile, VR user agents) interaction flows.
- **Performance Tests**: Measure route latency via `@performance_monitor`; compare before/after optimizations.

Run with:
```powershell
.\dev.ps1 test
```

---

## When Uncertain

1. **Propose the smallest, reversible change** — don't refactor unrelated code.
2. **Check `TODO.md` Acceptance criteria** — implement *exactly* as specified.
3. **Prefer existing patterns** — if the codebase uses a style, follow it (e.g., `data-*` attributes for targeting, `@performance_monitor` for routes).
4. **Document edge cases** — add a comment explaining *why* a workaround is needed (e.g., "SQLite UNIQUE constraint prevents duplicate ratings").
5. **Test on multiple platforms** — desktop, mobile, VR if the change affects UI.

---

## Safety Rails

- **Do not remove files** unless the task explicitly instructs it OR a replacement exists.
- **Do not change API contracts** without updating tests & docs.
- **Preserve `.github/copilot-instructions.md`** — update it when architectural patterns change.
- **Always check `TODO.md` first** — it is the single source of truth for priorities.

---

## First Actions for New Issues

1. Read `TODO.md` from the top.
2. Check acceptance criteria for the relevant task.
3. Review the files in "Architecture Essentials" to understand the current implementation.
4. Run `.\dev.ps1 dev` to start the server locally; test your changes in real-time.
5. Use `.\dev.ps1 lint` and `.\dev.ps1 test` before committing.
