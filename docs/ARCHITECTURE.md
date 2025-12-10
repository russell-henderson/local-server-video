# Local Video Server Architecture

## 1. High level system design

Local Video Server is a single node, local first media server built around:

- A Flask application entrypoint in `main.py`
- A core Python support layer in the repo root (config, cache, database, thumbnails, performance)
- An optional backend package under `backend/` that provides admin and API blueprints
- SQLite databases in the project root for fast metadata access
- JSON backup files for safety and emergency fallback
- A file system based video library and thumbnail cache
- Jinja2 templates and static assets for the gallery and admin dashboard

### 1.1 Component overview

Logical components:

- Web server and routing  
  - `main.py` creates the Flask app and defines the main gallery and watch routes.
  - Registers blueprints from `backend.app.admin` and `backend.app.api` when available.

- Configuration  
  - `config.py` provides `ServerConfig` and `ConfigManager`.
  - Reads environment variables, `.env`, and `config.json`.
  - Controls video paths, cache paths, performance flags, and CORS.

- Data backend  
  - `database_migration.py` defines `VideoDatabase` and manages `video_metadata.db`.
  - `video_metadata.db` stores video metadata, ratings, views, tags, and favorites.
  - JSON files (`ratings.json`, `views.json`, `tags.json`, `favorites.json`) are backups only.

- Cache layer  
  - `cache_manager.py` implements an in memory cache in front of SQLite.
  - Caches ratings, views, tags, favorites, and related video suggestions.
  - Handles read through and write through behavior.

- Thumbnail and metadata pipeline  
  - `thumbnail_manager.py` manages thumbnail generation and video duration extraction using `ffmpeg`.
  - Thumbnails are stored under a configured directory (for example `cache/thumbnails/`).
  - `main.py` uses a thread pool to ensure thumbnails exist without blocking the UI.

- File watcher (optional)  
  - `file_watcher.py` uses `watchdog` when available to monitor the video directory.
  - Applies debouncing and batch processing to update metadata and thumbnails after changes.

- Performance monitoring  
  - `performance_monitor.py` provides decorators and utilities for route level and function level metrics.
  - `backend/app/admin/performance.py` provides a metrics singleton for admin dashboard use.
  - Request timing logs are also emitted from `main.py` based on config flags.

- Admin and API backends  
  - `backend/app/admin/routes.py` exposes `/admin/performance` and `/admin/performance.json`.
  - `backend/app/admin/performance.py` tracks cache and ratings metrics.
  - `backend/app/api/ratings.py` exposes `/api/ratings/<media_hash>` for rating get and set.

- Front end and templates  
  - `templates/` contains Jinja2 templates for gallery, watch page, and admin performance view.
  - `templates/admin/performance.html` is the current admin dashboard page.
  - `static/` contains shared CSS and JS that support the gallery and admin views.

### 1.2 Technology stack

- Python 3.14
- Flask for HTTP routing and template rendering
- SQLite 3 for persistent metadata storage
- JSON files for backup snapshots
- ThreadPoolExecutor for background thumbnail work and file watcher callbacks
- Optional `watchdog` library for file watching
- `psutil` for performance and resource metrics in `performance_monitor.py`
- Standard Jinja2 templates and static assets for UI

---

## 2. Data flow

This section describes how requests and data move through the system.

### 2.1 Typical gallery page request

Path example: `GET /` or another gallery route.

1. **HTTP request enters Flask app**  
   - `main.py` receives the request through the Flask app.

2. **Configuration resolved**  
   - `get_config()` from `config.py` is used to access current `ServerConfig`.
   - Video directory, thumbnail directory, and feature flags are available.

3. **Metadata and file list fetched**  
   - `cache_manager.py` is used to fetch:
     - video list
     - ratings
     - views
     - tags
     - favorites
   - Cache reads from SQLite through `VideoDatabase` if needed.
   - Cache avoids repeated JSON file reads in normal operation.

4. **Thumbnails ensured**  
   - `main.py` calls into `thumbnail_manager` helpers such as `ensure_thumbnails_exist`.
   - A `ThreadPoolExecutor` is used so thumbnail generation does not block normal page rendering.

5. **Template rendering**  
   - A Jinja2 template in `templates/` is rendered with:
     - video metadata
     - rating and view counts
     - thumbnails
   - Result is returned as HTML to the browser.

6. **Performance logging**  
   - Request timing hooks in `main.py` record duration to logs when enabled.
   - Performance decorators from `performance_monitor.py` may be applied to hot paths for detailed tracking.

### 2.2 Watch page and streaming request

Path example: `GET /watch/<filename>` and related static serving.

1. **Routing**  
   - `main.py` routes the request to a view that loads a specific video.

2. **Metadata lookup**  
   - `cache_manager` looks up the video's metadata and current rating view.
   - Related videos may be computed using cached tags or similarity hints.

3. **Thumbnail and preview assurance**  
   - Thumbnails or preview images for related videos are checked and created as needed using `thumbnail_manager`.

4. **Response**  
   - The watch template is rendered with:
     - the current video
     - its metadata
     - a related videos list
   - The actual video file is streamed via `send_file` or a similar helper from Flask.

5. **Metrics**  
   - View counts are updated through `cache_manager`, which writes through to SQLite.
   - Performance hooks record latency by route and endpoint.

### 2.3 Ratings API request

Path examples:

- `GET /api/ratings/<media_hash>`
- `POST /api/ratings/<media_hash>`

Flow:

1. The request hits the `ratings_bp` blueprint in `backend/app/api/ratings.py`.
2. For `GET`:
   - `RatingsService` from `backend/services/ratings_service.py` uses:
     - `cache_manager` to retrieve data
     - database lookups by media hash and filename
   - A JSON summary is returned with rating statistics.
3. For `POST`:
   - A Pydantic style schema validates the incoming payload.
   - `RatingsService.set_rating` updates the rating in SQLite and cache.
   - A JSON summary of the updated rating is returned.
4. Both endpoints call `add_cors_headers` to support local LAN usage and Quest clients.

Performance metrics for ratings:

- `backend/app/admin/performance.py` tracks `POST /api/ratings` latencies.
- The metrics are exposed to the admin performance JSON endpoint.

---

## 3. Core modules and interactions

### 3.1 main.py

Responsibilities:

- Create and configure the Flask app.
- Load configuration via `ConfigManager` and `ServerConfig`.
- Initialize or connect to `cache_manager` and database.
- Register:
  - main gallery and watch routes
  - optional admin blueprint via `register_admin_routes(app)`
  - optional ratings API blueprint via `register_ratings_api(app)`
- Set up:
  - request timing hooks
  - logging
  - thread pools for thumbnail generation

Dependencies:

- `config.py`
- `cache_manager.py`
- `database_migration.py`
- `thumbnail_manager.py`
- `performance_monitor.py`
- `backend.app.admin.routes` (optional)
- `backend.app.api.ratings` (optional)

### 3.2 config.py

Responsibilities:

- Define `ServerConfig` dataclass with fields for:
  - server port
  - host
  - video directory path
  - thumbnail directory path
  - cache settings
  - database path and behavior
  - performance flags
  - security and CORS configuration
- Define `ConfigManager` that:
  - loads from environment variables
  - reads `.env`
  - reads `config.json`
  - applies defaults
  - validates values in `_validate_config()`

Key behavior:

- Ensures video and thumbnail directories exist.
- Validates port ranges and log level.
- Drives feature flags used in `main.py` and other modules.

### 3.3 cache_manager.py

Responsibilities:

- Provide a process local cache for:
  - ratings
  - views
  - tags
  - favorites
  - related videos
- Coordinate reads and writes between:
  - in memory structures
  - SQLite database through `VideoDatabase`
  - legacy JSON snapshot files in emergency fallback mode

Key behavior:

- Uses `threading.RLock` for thread safety.
- Exposes helper methods such as:
  - `get_ratings()`, `get_views()`, `get_tags()`, `get_favorites()`
  - `update_rating()`, `update_view()`, `update_tags()`, `update_favorite()`
  - `get_related_videos_optimized()`
- Implements TTL based cache refresh and write through semantics.
- Treats JSON files as backup only, as documented in `docs/DATA_BACKEND.md`.

### 3.4 database_migration.py

Responsibilities:

- Provide `VideoDatabase` as the main interface to `video_metadata.db`.
- Handle schema creation and migration from JSON to SQLite.

Schema:

- `videos`  
  - filename  
  - added_date  
  - file_size  
  - duration  
- `ratings`  
  - filename  
  - rating value  
  - created and updated timestamps  
- `views`  
  - filename  
  - view count  
  - last viewed timestamp  
- `video_tags`  
  - many to many between filenames and tags  
- `favorites`  
  - list of favorite videos

Key behavior:

- Uses context managers for safe connection handling.
- Exposes query and update helpers used by `cache_manager` and services.

### 3.5 thumbnail_manager.py

Responsibilities:

- Generate and maintain thumbnails and basic metadata for videos.
- Use `ffmpeg` to:
  - extract frame captures
  - measure video duration

Key behavior:

- Uses `ThreadPoolExecutor` for parallel thumbnail generation in scripts or utilities.
- Uses a fixed thumbnail directory under the cache root.
- Integrates with `main.py` to ensure required thumbnails exist before rendering pages.

### 3.6 file_watcher.py

Responsibilities:

- Monitor the video directory tree and detect:
  - added files
  - removed files
  - modified files
- Apply debouncing and batch processing so bursts of file changes do not cause repeated work.
- Optionally detect duplicates using checksums.

Key behavior:

- Uses `watchdog` where available.
- Runs an internal `ThreadPoolExecutor` for batch processing.
- Invokes callbacks such as:
  - `on_video_added`
  - `on_video_removed`
  - `on_video_modified`
  - `on_batch_processed`

Integration plan:

- Designed to be wired into startup or maintenance workflows.
- When active, can call into `thumbnail_manager` and `cache_manager` to keep metadata and thumbnails in sync with disk.

### 3.7 performance_monitor.py

Responsibilities:

- Provide decorators and utilities to collect:
  - function level latency
  - memory usage snapshots
  - per name statistics

Key behavior:

- `PerformanceTracker` manages a registry of metrics.
- Decorator wrapper measures:
  - execution time
  - memory before and after
- Can be applied to key routes or background jobs to feed admin dashboard metrics.

Relationship to admin metrics:

- `performance_monitor.py` is a general tool.
- `backend/app/admin/performance.py` wraps admin specific counters and p95 statistics that the dashboard uses.

---

## 4. Admin dashboard backend

The admin dashboard is served from the main Flask app but has its own blueprints and metrics.

### 4.1 Admin blueprint (`backend/app/admin/routes.py`)

- Blueprint: `admin_bp`
- URL prefix: `/admin`

Endpoints:

- `GET /admin/performance`  
  - Renders `templates/admin/performance.html`.
  - Injects values for cards such as cache hit rate and ratings POST p95.

- `GET /admin/performance.json`  
  - Returns a JSON structure with:
    - `cache_hit_rate`
    - `uptime_seconds`
    - `db_queries` summary
    - `ratings_post` p95 and average latency
    - additional endpoint metrics

Registration:

- `register_admin_routes(app)` is imported and called from `main.py` when the backend package is available.

### 4.2 Metrics layer (`backend/app/admin/performance.py`)

`PerformanceMetrics` tracks:

- Cache hits and misses  
- Endpoint latency lists  
- Database queries per request  
- Ratings POST latencies with convenience methods for:
  - p95 latency
  - average latency
  - request counts

The `get_metrics()` function returns a process wide singleton used by:

- the admin HTML view
- the admin JSON API

This layer is separate from `performance_monitor.py` but can be combined with it if needed.

### 4.3 Ratings API (`backend/app/api/ratings.py`)

Blueprint:

- `ratings_bp`, typically registered under `/api/ratings`.

Responsibilities:

- `GET /api/ratings/<media_hash>`  
  - Return rating summary for a video.

- `POST /api/ratings/<media_hash>`  
  - Validate payload using a schema model.
  - Set rating through `RatingsService`.
  - Return updated rating summary.

CORS behavior:

- Adds CORS headers based on allowed origins so Quest and other LAN devices can call the API.

Service:

- `backend/services/ratings_service.py`  
  - Maps between media hashes and filenames.
  - Uses `cache_manager` and the database to fetch or update data.

---

## 5. Security model

The current security model is oriented around a trusted local network.

Key points:

- Server binding and port are controlled by `ServerConfig` from `config.py`.  
  Typical bind: `0.0.0.0` on a configured port for LAN access.

- CORS  
  - `ServerConfig` includes `enable_cors` and `allowed_origins`.
  - Ratings API uses CORS helpers to support:
    - localhost
    - LAN IPs
    - specified origins

- Authentication  
  - There is no full user authentication layer yet.
  - The server is intended for local deployments on trusted networks.
  - Future work can add auth on top of the existing blueprints without changing the core data model.

- Data integrity  
  - SQLite enforces constraints on core tables.
  - JSON backups in `backup_json/` are read only from the application point of view.
  - `database_migration.py` and `DATA_BACKEND.md` describe migration and recovery options.

---

## 6. Scalability and performance considerations

The architecture choices are driven by running on a single machine with potentially thousands of videos.

Main ideas:

- SQLite plus in memory cache  
  - Gives a good balance of performance, simplicity, and durability.
  - Cache avoids repeated disk I O for hot data.
  - JSON backups provide a safety net without adding runtime cost.

- Thread pools for I O bound work  
  - Thumbnail generation uses thread pools to keep latency reasonable.
  - File watcher callbacks also use a thread pool for batch handling.
  - Avoids blocking the main Flask worker threads on slow ffmpeg calls.

- Metrics and monitoring  
  - Route timing logs in `main.py` combined with:
    - `performance_monitor.py`
    - `backend/app/admin/performance.py`
  - Provide enough data for the admin dashboard to show:
    - cache behavior
    - ratings endpoint health
    - general latency ranges

- Future scaling paths  
  - Split admin dashboard API into dedicated blueprints under `/api/admin`.
  - Add more metrics to the `PerformanceMetrics` object for:
    - thumbnail worker queue depth
    - cache size and eviction counts
    - database query counts by route
  - If necessary, move SQLite to a dedicated process or host while keeping the same schema.

---

## 7. How this supports the admin dashboard spec

The admin dashboard spec that lives in `chatgpt_prompt.md` and future `API.md` assumes:

- A clear way to surface metrics and health data through HTTP.
- Stable data models for ratings, views, tags, and favorites.
- Ability to add new admin endpoints for:
  - usage analytics
  - error logs
  - storage and cache health
  - export tools

This architecture supports that by:

- Providing `PerformanceMetrics` and `performance_monitor.py` as reusable metrics backends.
- Exposing admin data through blueprints that are already isolated from public gallery routes.
- Centralizing data access in `cache_manager.py` and `VideoDatabase`, so:
  - new admin APIs can reuse the same abstractions
  - write paths remain consistent and safe.

When you add new dashboard tiles or sections:

1. Add any needed metrics to `PerformanceMetrics` or `performance_monitor.py`.
2. Expose them through a new admin JSON endpoint under `/admin` or `/api/admin`.
3. Update `docs/API.md` to match the new endpoint.
4. Render the data from the admin front end using the existing pattern in `templates/admin/performance.html`.

---

## 8. Summary

- `main.py` is the HTTP and orchestration center.
- `config.py`, `cache_manager.py`, `database_migration.py`, `thumbnail_manager.py`, `file_watcher.py`, and `performance_monitor.py` form the core backend subsystem.
- `backend/app` hosts admin and API blueprints that use this subsystem.
- SQLite plus in memory caching gives a simple and fast data backbone.
- Admin dashboard endpoints already exist for performance and can be extended for the full spec described in the other docs.

Keep this file updated whenever the structure of the backend changes or whenever you add major new admin features so that the dashboard spec always rests on an accurate picture of the running system.
