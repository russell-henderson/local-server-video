# Local Video Server - Global Documentation

## Project Overview

Local Video Server is a Flask-based application for managing a personal video library and image gallery with responsive themes, cross-platform support (desktop/mobile/VR), performance optimization, and a Next.js admin dashboard for performance monitoring.

**Source of truth for priority-ordered work:** `TODO.md` at the repository root.

## Table of Contents

1. [Architecture Essentials](#architecture-essentials)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Key Design Decisions](#key-design-decisions)
5. [Development Workflow](#development-workflow)
6. [Code Patterns & Conventions](#code-patterns--conventions)
7. [File Organization & Naming](#file-organization--naming)
8. [Task Workflow](#task-workflow)
9. [VR/Cross-Platform Specifics](#vr/cross-platform-specifics)
10. [Configuration & Environment](#configuration--environment)
11. [Testing & Quality](#testing--quality)
12. [Component Reference](#component-reference)

---

## Architecture Essentials

### Core Components

| Module | Purpose | Key Patterns |
| -------- | --------- | -------------- |
| `main.py` | Flask app entry point, video routes, gallery routes, thumbnail orchestration | Route handlers w/ `@performance_monitor` decorator; cache-driven metadata pulls |
| `cache_manager.py` | In-memory + SQLite cache for videos, images, ratings, views, tags, favorites | Dual-backend (JSON fallback); TTL-based refresh; thread-safe with locks |
| `database_migration.py` | SQLite schema & migrations | Uses `sqlite3.Row` for dict-like access; foreign keys on `videos.filename`; soft deletes via CASCADE |
| `file_watcher.py` | Debounced directory monitoring w/ batch processing | Watchdog observer; background thread; dedup via checksum |
| `config.py` | Dataclass-based config w/ cascade (env vars → `.env` → `config.json` → defaults) | `ServerConfig` validation; `ConfigManager` singleton |
| `performance_monitor.py` | Optional route latency tracking & optional perf reporting | Non-fatal import; can disable monitoring if unavailable |
| `admin-dashboard/` | Next.js app for admin performance dashboard | Separate app; fetches `/admin/performance.json` from Flask backend |

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

- **Cache-Driven Architecture**: All routes pull from `cache` object first. DB is single source of truth; cache validates against file existence.
- **Nullable Ratings/Views**: A video with no rating shows `0`; views default to `0` if unset.
- **SQLite + JSON Fallback**: If DB fails, reads JSON files (`ratings.json`, etc.). Writes still go to DB if available.
- **Background Thumbnail Generation**: Non-blocking; new files trigger `generate_thumbnail_async()` queued by filename dedup.
- **Thread Safety**: `cache_manager` and `database_migration` use `threading.RLock()` for concurrent access.
- **Cross-Device Accessibility**: 44px+ touch targets, no hover dependencies, PWA caching for mobile performance.
- **Image Gallery**: Supports loose images and virtual groups; favorites work across both; selection mode for bulk operations.
- **Admin Dashboard**: Separate Next.js app for performance monitoring; uses Recharts for visualizations.

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
- **Gallery Page**: `templates/gallery.html` with selection mode, groups grid, images grid.
- **Rating Interaction**: `<div class="rating" data-filename="...">` → `static/js/ratings.js` (pointer + click + keyboard support; VR-safe).
- **Video Cards**: Responsive grid; thumbnail lazy-load with fallback GIF; `data-role="video-card"` for JS targeting.
- **Gallery Items**: `data-filename` for selection; shift-click for ranges.

### JavaScript Conventions

- **Player**: `static/js/player.js` → `class VideoPlayer { ... }` wraps `<video>` + controls; keyboard shortcuts (k/space=play, j/l=skip±10s, f=fullscreen).
- **Ratings/Tags**: Module functions (not classes); use `data-filename` to find context; emit fetch requests on DOM changes.
- **Gallery Selection**: `static/js/gallery.js` → Handles selection mode, shift-click ranges, bulk actions.
- **Dark Mode**: Enabled by default; toggle adds/removes `dark-mode` class on `document.documentElement` + `body`.

### Admin Dashboard Patterns

- **Data Fetching**: Fetch from `/admin/performance.json`; use React hooks for live updates.
- **Charts**: Use Recharts for metrics visualization.
- **Layout**: Tailwind CSS for responsive design.

---

## File Organization & Naming

```bash
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
│   ├── styles.css               # **Single CSS entry point** (no duplicates)
│   ├── sw.js                    # Service worker for PWA caching
│   ├── js/
│   │   ├── player.js            # Video player class
│   │   ├── ratings.js           # Rating star interactions
│   │   ├── tags.js              # Tag management
│   │   ├── gallery.js           # Gallery selection logic
│   │   ├── ui.js                # Dark mode toggle
│   └── css/
│       └── player-controls.css  # Player-specific styles
├── templates/
│   ├── watch.html               # **Single watch page** (includes _player.html)
│   ├── index.html               # Video list & grid
│   ├── favorites.html           # Favorites page with sorting/pagination
│   ├── popular.html             # Popular videos by view count
│   ├── gallery.html             # Image gallery with groups
│   ├── _base.html               # Base layout
│   ├── _navbar.html             # Navigation
│   ├── _player.html             # Reusable player component
│   └── partials/
│       └── rating.html          # Rating star partial (included in watch.html)
├── TODO.md                      # **Canonical agent task queue** (repo root)
├── docs/                        # Current, active documentation
│   ├── ADMIN_DASHBOARD.md       # Admin dashboard spec
│   ├── IMPLEMENTATION.md        # Architecture + dev workflow
│   ├── PERFORMANCE.md           # Optimization notes
│   ├── UI.md                    # UI patterns & player behavior
│   └── TODOS.md                 # Docs-facing supplemental task index (not a replacement for root TODO.md)
├── archive/                     # Deprecated systems, cost analyses, old designs
├── .github/
│   └── copilot-instructions.md  # This file
└── dev.ps1                      # PowerShell command wrapper
```

**Critical Rules:**

- One `static/styles.css` only—no `app.css`, `theme.css`, etc.
- One `templates/watch.html`—no backup copies (rename old ones to `watch.html.backup`).
- One `templates/partials/rating.html`—reused wherever ratings are shown.
- All design experiments → `archive/` with a README explaining the rationale.

---

## Task Workflow (from root TODO.md)

1. **Read root `TODO.md` top-to-bottom** — tasks are ordered by dependency & priority.
2. **Pick the highest unchecked task** whose dependencies are met.
3. **Implement the smallest correct change set** — avoid scope creep.
4. **Update root `TODO.md`** when done:
   - Change `- [ ]` to `- [x]`
   - Add a note: `Completed in PR_number (commit abc123).`
5. **Optionally** mirror or summarize in **`docs/TODOS.md`** if the doc-side index should stay aligned.
6. **Open a PR** with:
   - Title: `[scope] short summary` (e.g., `ratings: make stars work on Quest`)
   - Body: summary, linked TODO items, acceptance results, test evidence
7. **All tests must pass locally & in CI** before merging.

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
LVS_IMAGE_DIRECTORY=~/my-images
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

## Component Reference

### Backend Components

#### main.py

- Entry point for Flask application
- Creates app using factory pattern from backend.app.factory
- Handles command line arguments for host, port, and debug mode
- Executes startup tasks on application start

#### cache_manager.py

- Manages in-memory and SQLite caching for metadata
- Provides methods for getting/setting video/image data, ratings, views, tags, favorites
- Implements TTL-based cache invalidation
- Thread-safe with RLock for concurrent access
- Falls back to JSON files if database unavailable

#### database_migration.py

- Handles SQLite database schema creation and migrations
- Defines tables for videos, ratings, views, tags, favorites, playlists, gallery groups
- Uses foreign key constraints for data integrity
- Provides methods for querying and updating metadata
- Implements soft deletes via CASCADE

#### config.py

- Dataclass-based configuration system
- Supports cascade: environment variables → .env → config.json → defaults
- Validates configuration values (port ranges, quality settings, etc.)
- Ensures required directories exist
- Provides methods to save and reload configuration

#### performance_monitor.py

- Optional performance monitoring decorator for Flask routes
- Tracks route latency and provides reporting capabilities
- Non-fatal import - application continues if monitoring unavailable
- Can generate performance reports for admin dashboard

#### thumbnail_manager.py

- Handles asynchronous thumbnail generation
- Queues thumbnail generation requests with deduplication
- Uses background threads for non-blocking thumbnail creation
- Supports various image formats and quality settings
- Manages thumbnail storage and cleanup

#### file_watcher.py

- Monitors video and image directories for changes
- Uses watchdog for efficient file system event detection
- Implements debouncing to prevent excessive processing
- Triggers thumbnail generation for new files
- Runs in background thread to avoid blocking main application

### Frontend Components

#### Templates (templates/)

- `index.html` - Home page showing video library
- `watch.html` - Video playback page with metadata
- `gallery.html` - Image gallery with grouping and selection
- `favorites.html` - Page showing favorite videos
- `popular.html` - Page showing most viewed videos
- `_base.html` - Base layout template
- `_navbar.html` - Navigation bar component
- `_player.html` - Reusable video player partial
- `partials/rating.html` - Rating star component partial

#### Static Assets (static/)

- `styles.css` - Main stylesheet for the application
- `sw.js` - Service worker for PWA functionality
- `js/`
  - `player.js` - Video player class with keyboard controls
  - `ratings.js` - Rating star interaction logic
  - `tags.js` - Tag management functionality
  - `gallery.js` - Gallery selection and interaction logic
  - `ui.js` - Dark mode toggle and UI utilities
- `css/`
  - `player-controls.css` - Styles specific to video player controls

### Backend API (backend/)

- `app/` - Main Flask application factory
- `db/` - Database models and connection handling
- `repositories/` - Data access layer for videos, images, metadata
- `services/` - Business logic for recommendations, metadata processing

### Admin Dashboard (admin-dashboard/)

- Next.js application for performance monitoring
- Fetches performance data from Flask backend `/admin/performance.json`
- Uses React hooks for live data updates
- Implements Recharts for data visualization
- Styled with Tailwind CSS for responsive design

### Documentation (docs/)

- `ADMIN_DASHBOARD.md` - Admin dashboard specification
- `ARCHITECTURE.md` - System architecture overview
- `API.md` - API contract and route reference
- `DEPLOYMENT.md` - Deployment and runtime instructions
- `IMPLEMENTATION.md` - Detailed implementation notes
- `PERFORMANCE.md` - Performance optimization guidelines
- `UI.md` - User interface patterns and behavior
- `TESTING.md` - Testing procedures and guidelines

### Data Files

- `videos/` - Directory containing user video files
- `images/gallery/` - Directory containing user image files
- `data/video_metadata.db` - Primary SQLite database for video metadata
- `data/video_search.db` - Secondary database for search indexing
- `data/gallery_index.db` - Database for gallery image indexing
- `static/thumbnails/` - Generated video thumbnails
- `static/gallery-thumbnails/` - Generated image thumbnails
- `logs/` - Application log files
- `ratings.json`, `views.json`, `tags.json`, `favorites.json` - JSON fallback files

---

## Important URLs

- **Local App**: <http://localhost:5000/> (or configured host/port)
- **Local Network**: http://[your-ip]:5000/
- **Admin Dashboard**: <http://localhost:3000/> (when running separately)
- **Health Check**: Accessible via `.\dev.ps1 health`
- **Performance Report**: Available through admin dashboard or `performance_monitor.py --report`

## Key Features

1. **Media Library Management**
   - Video browsing with sorting (date, rating, views, random)
   - Image gallery with grouping and selection capabilities
   - Favorites system for both videos and images
   - Tagging system for content organization

2. **Playback Experience**
   - Responsive video player with keyboard controls
   - Progress tracking and resume playback
   - View count incrementing
   - Rating system (1-5 stars)

3. **Discovery & Recommendations**
   - Personalized recommendation engine
   - Tag-based content discovery
   - Trending/popular content views
   - Recently watched tracking

4. **Organization Tools**
   - Virtual image groups for organization
   - Bulk selection and actions
   - Metadata editing (ratings, tags, favorites)
   - File system monitoring for automatic library updates

5. **Performance & Monitoring**
   - Intelligent caching system
   - Background thumbnail generation
   - Performance monitoring and reporting
   - Admin dashboard for metrics visualization
   - PWA capabilities for offline access

6. **Cross-Platform Support**
   - Responsive design for desktop, tablet, mobile
   - Touch-friendly interfaces (≥44px targets)
   - Keyboard navigation support
   - VR considerations (no hover dependencies)
   - Dark/light theme support

7. **Reliability & Maintenance**
   - SQLite database with JSON fallback
   - Automatic backup capabilities
   - Health check systems
   - Cache management and cleanup tools
   - Database migration and reindexing utilities

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (for admin dashboard)
- FFmpeg (for video processing)
- Adequate storage for media library

### Installation

```powershell
# Install Python dependencies
.\dev.ps1 install

# Install Node.js dependencies for admin dashboard
cd admin-dashboard
npm install
```

### Development

```powershell
# Start development server
.\dev.ps1 dev

# In another terminal, start admin dashboard
cd admin-dashboard
npm run dev
```

### Production

```powershell
# Start production server
.\dev.ps1 prod

# Build and start admin dashboard
cd admin-dashboard
npm run build
npm start
```

## Maintenance Commands

```powershell
# Force reindexing of media library
.\dev.ps1 reindex

# Create timestamped backup
.\dev.ps1 backup

# Run health checks
.\dev.ps1 health

# Clean temporary files
.\dev.ps1 clean

# Run linting
.\dev.ps1 lint
```

## Configuration

Configuration can be set via:

1. Environment variables (prefixed with `LVS_`)
2. `.env` file in project root
3. `config.json` file in project root
4. Built-in defaults

See `config.py` and `env.example` for available options.

## Contributing

See `TODO.md` for current development priorities and workflow.
Follow the component-by-component workflow outlined in the documentation.
Submit pull requests with clear descriptions of changes and related TODO items.

## License

MIT License - see LICENSE file for details.
