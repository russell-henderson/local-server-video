Here is the fully updated `docs/IMPLEMENTATION.md` with admin dashboard references wired in and no changes to the existing structure other than the requested cross references.

````markdown
# Implementation - Local Video Server

This document explains how the Local Video Server is implemented in code.

It describes:

- How the main Flask app is wired.
- How configuration, data storage, and caching work.
- How thumbnails and metadata are generated.
- How the ratings API and backend services are structured.
- How admin metrics and the performance monitor are implemented.
- How the front end uses templates and static assets.
- How to work with the developer tooling in this repo.

For a higher level view of the system, see:

- `docs/PROJECT.md` for phases and doc map.
- `docs/ARCHITECTURE.md` for component and data flow.
- `docs/API.md` for the endpoint surface.
- `docs/ADMIN_DASHBOARD.md` for the admin dashboard UI specification.
- `docs/PERFORMANCE.md` and `docs/PERFORMANCE_MONITORING.md` for performance goals and metrics.

Historical implementation documents have been archived to `docs/deferred/` and should be treated as reference only.

---

## 1. Application entry point

### 1.1 `main.py`

`main.py` is the main entry point of the application and is responsible for:

- Creating and configuring the Flask app.
- Wiring configuration, database, cache, and thumbnail manager.
- Registering blueprints for the main views and APIs.
- Registering admin and performance monitoring views.
- Optionally enabling file watching and performance diagnostics.

High level flow inside `create_app()`:

1. Load configuration via `ConfigManager` and `ServerConfig`.
2. Initialize logging.
3. Initialize `VideoDatabase` and migrate schema if needed.
4. Initialize cache and thumbnail manager.
5. Register blueprints for:
   - Gallery, watch, favorites, and popular views.
   - Ratings API.
   - Admin and performance views.
6. Optionally start background tasks like file watching.
7. Optionally enable the diagnostic performance monitor.

Key patterns:

- Dependency injection is done manually by passing shared components (database, cache, thumbnail manager) into blueprints or helper functions.
- Configuration is centralized through `ServerConfig`, which is resolved once during app creation.

Typical usage:

```bash
export FLASK_APP=main.py
flask run
````

or directly:

```bash
python main.py
```

The application is intended for local and LAN use. It is not hardened for untrusted public internet exposure.

---

## 2. Configuration and settings

### 2.1 `config.py`

`config.py` contains:

* `ServerConfig`
  A dataclass that holds all runtime settings, including:

  * video directory
  * cache directory
  * database path
  * JSON backup directory
  * thumbnail sizes
  * feature flags (file watcher, diagnostics, etc.)

* `ConfigManager`
  A helper that resolves `ServerConfig` from:

  * environment variables
  * `.env` file
  * optional `config.json`
  * compiled defaults

Resolution rules:

1. Environment variables override everything else.
2. `.env` file is used as a convenient local override.
3. `config.json` can define a persistent configuration for a machine.
4. Defaults baked into `ServerConfig` cover reasonable local use cases.

`ConfigManager` also:

* Validates that directories exist or can be created.
* Normalizes paths.
* Ensures that the video directory and cache directory are not identical.

The resulting `ServerConfig` is treated as immutable during runtime.

---

## 3. Data storage and caching

### 3.1 SQLite database

The primary data store is a SQLite database, accessed through `VideoDatabase` in `database_migration.py`.

The database stores:

* Video records

  * id
  * path
  * title
  * duration
  * resolution
  * size
  * created_at
  * updated_at

* Ratings and views

  * per video rating aggregate
  * rating count
  * favorites flag
  * view count

* Tags

  * video to tag relationships
  * tag usage counts

Schema evolution is handled via migration helpers inside `database_migration.py`.

### 3.2 JSON backups

JSON backups act as a secondary and portable data format.

* Each video can have a sidecar JSON file with metadata.
* Periodic exports write a snapshot of the database to JSON files in the data directory. They are used for backup and emergency restore, not as the primary source of truth.

### 3.3 Cache and metadata

`cache_manager.py` provides an in memory cache that sits in front of the database and JSON sidecars.

Responsibilities:

* Cache frequently accessed video metadata: title, thumbnail path, ratings, tags.
* Cache computed aggregates such as favorite counts or tag popularity.
* Provide basic eviction logic when the cache grows too large.

Typical flow:

1. Gallery or watch page requests data for a video.
2. Cache manager checks for an existing cached entry.
3. On a miss, it fetches data from the database, enriches it, and stores it in cache.
4. When ratings or tags change, cache entries are updated or invalidated.

The cache is designed for read heavy workloads on local or LAN access patterns.

---

## 4. Thumbnails and file system operations

### 4.1 `thumbnail_manager.py`

`thumbnail_manager.py` is responsible for:

* Probing video files with `ffmpeg` to extract metadata such as:

  * duration
  * frame size
  * codec information
* Generating thumbnail and poster images at configured sizes.
* Writing thumbnails into the cache directory.

Behavior:

* On first request for a thumbnail, the manager checks if a cached image exists.
* If not, it invokes `ffmpeg` with appropriate arguments to extract a frame at a representative time (often mid duration).
* It writes out JPEG or WEBP files into the cache directory.
* It returns the path for templating.

The manager respects configuration:

* Thumbnail sizes.
* Maximum cache size or directory layout.
* Whether to generate multiple sizes for responsive layouts.

### 4.2 File scanning

Initial library scanning is performed by a separate helper that walks the video directory:

* Discovers video files based on extension.
* Adds new video records to the database if they do not exist.
* Updates existing records if metadata has changed.
* Marks records as missing if files have been removed.

This scan can be:

* Run at startup.
* Run on demand through a management command.
* Augmented by the file watcher.

### 4.3 `file_watcher.py`

`file_watcher.py` integrates `watchdog` to monitor the video directory for changes:

* File created.
* File modified.
* File deleted or moved.

On each event, the watcher:

* Triggers incremental metadata updates in the database.
* Requests thumbnail generation or cache invalidation if needed.

The watcher is optional and is controlled by a configuration flag. It is useful on machines where video files are frequently added or updated while the server is running.

---

## 5. Web layer and routing

### 5.1 Blueprints and overall structure

The web layer is built with Flask blueprints:

* Main views:

  * Gallery view.
  * Watch view.
* API:

  * Ratings and favorites.
  * Tags and autocomplete.
* Admin:

  * Performance and metrics dashboard.

Each blueprint receives shared dependencies such as the database and cache, usually through a factory pattern.

### 5.2 Main views

The main views provide:

* Gallery:

  * Paginated list of videos.
  * Filters by tags and favorites.
  * Sorting by date, rating, or views.
  * Thumbnail grid with hover or tap preview.
* Watch page:

  * Single video player.
  * Ratings and favorites controls.
  * Tags input and display.
  * Related videos.

These views are implemented with Jinja2 templates and use JS helpers for interactive parts such as rating updates.

### 5.3 API endpoints

The ratings and tags APIs are implemented under `/api`:

* `POST /api/ratings`
  Accepts rating submissions or updates for a video.
* `POST /api/favorites`
  Toggles the favorite status of a video.
* `GET /api/tags/popular`
  Returns popular tags for autocomplete and discovery.
* `POST /api/tags/set`
  Sets or updates tags for a video.

Implementation details for these endpoints are in `backend/app/api/ratings.py` and `backend/services/ratings_service.py`, which coordinate:

* Input validation.
* Database updates.
* Cache invalidation.
* Metrics updates for performance monitoring.

---

## 6. Templates and static assets

Template and asset structure:

* Gallery and watch templates:

  * `templates/gallery.html`
  * `templates/watch.html`
* Partials:

  * Shared header and footer.
  * Video card partial.
* Admin:

  * `templates/admin/performance.html`

Important directories:

* JSON backups

  * Stored under a configured data directory. They are used for backup and emergency restore, not as the primary source of truth.

* Thumbnails and cache

  * Thumbnail images live under the configured cache directory (often `static/thumbnails/` or `cache/thumbnails/` depending on configuration).
  * The cache directory root and limits are controlled by `ServerConfig`.

* Templates and static files

  * `templates/` contains Jinja2 templates for the gallery, watch page, and admin performance view.
  * `templates/admin/performance.html` is the current admin dashboard page and follows the layout defined in `docs/ADMIN_DASHBOARD.md`.
  * The dashboard consumes metrics that follow the schemas in `docs/PERFORMANCE_MONITORING.md`.
  * `static/` contains shared JS and CSS, for example:

    * `static/styles.css`
    * `static/video-player-controls.js`
    * `static/favorites.js`
    * `static/metrics.js`
    * `static/js/ratings.js`
    * `static/js/tags.js`

The front end is intentionally simple and is focused on fast local use. It uses minimal JavaScript and leans on server rendered HTML.

---

## 7. Admin metrics and performance monitoring

### 7.1 Admin metrics singleton

`backend/app/admin/performance.py` defines `PerformanceMetrics`, which stores:

* Cache counters:

  * `cache_hits`
  * `cache_misses`
* Endpoint latency samples in `endpoint_latencies`.
* Database query counts in `db_queries_per_request` and `total_db_queries`.
* Ratings specific latency samples in `ratings_post_latencies`.
* `start_time` for uptime.

The primary public methods used by routes are:

* `record_cache_hit()` and `record_cache_miss()`
  Update cache hit and miss counters.

* `record_endpoint_latency(endpoint, latency_ms)`
  Records a latency sample for a named endpoint.

* `record_db_queries(count)`
  Tracks the number of database queries performed during a request.

* `get_cache_hit_rate()`
  Returns the current cache hit rate as a float between 0 and 1.

* `get_uptime_seconds()`
  Returns seconds since `start_time`.

* `get_ratings_post_p95_latency()`
  Returns p95 latency for `POST /api/ratings` in milliseconds.

* `get_ratings_post_avg_latency()`
  Returns average latency for `POST /api/ratings` in milliseconds.

* `get_ratings_post_count()`
  Returns the number of `POST /api/ratings` calls in the current window.

Future work will extend usage of `endpoint_latencies` to drive per route metrics in the admin dashboard and the planned `/api/admin/performance/routes` endpoint.

### 7.2 Admin routes and JSON snapshot

`backend/app/admin/routes.py` exposes:

* `GET /admin/performance`
  Renders `templates/admin/performance.html`. The template receives:

  * `cache_hit_rate`
  * `uptime_seconds`
  * `ratings_post_p95`
  * `ratings_post_avg`
  * `ratings_post_count`
    and displays status badges based on thresholds documented in `docs/PERFORMANCE.md`.

* `GET /admin/performance/json`
  Returns a JSON snapshot suitable for the dashboard and for external tools. It includes:

  * `cache_hit_rate`
  * `uptime_seconds`
  * `database` aggregate metrics
  * `ratings_post` metrics
  * A placeholder `endpoints` object reserved for future route metrics

The HTML view at `/admin/performance` implements the admin dashboard specified in `docs/ADMIN_DASHBOARD.md`.
The JSON snapshot uses the metric schemas from `docs/PERFORMANCE_MONITORING.md` so that the dashboard and any external tooling share a consistent structure.

The detailed schema is defined in `docs/PERFORMANCE_MONITORING.md`.

### 7.3 Diagnostic performance monitor

`performance_monitor.py` provides a second layer of monitoring:

* `PerformanceMonitor` maintains:

  * recent function metrics
  * per route timing in `route_stats`
  * cache statistics in `cache_stats`
* Decorators:

  * `@performance_monitor` for generic functions
  * `flask_route_monitor(app)` to hook Flask request timing

In `main.py`, the app uses `flask_route_monitor(app)` when the diagnostic layer is enabled. This layer is used for:

* Detailed performance reports during development.
* Load testing via `load_test_simulation()`.

Over time, more of these diagnostics can be bridged into `PerformanceMetrics` so that the admin dashboard reflects the same data.

---

## 8. Background tasks and workers

The project can run background tasks for:

* Library scanning.
* Thumbnail generation.
* Periodic backups.

While the core implementation runs these in process and on demand, the code is structured so that they can be moved into a dedicated worker process or external job runner in the future.

Typical patterns:

* Use a simple queue or list of tasks.
* Run workers in a loop that:

  * pops tasks
  * performs work
  * logs results and errors

For now, the background task implementation is conservative and targeted at single machine use.

---

## 9. Developer tooling

This repository includes several helpers for development and testing.

### 9.1 Scripts and utilities

* `scripts/load_test.py`
  Simulates load against the ratings API and main views. Useful for exercising the performance monitor and admin dashboard.

* `scripts/backup_database.py`
  Writes a JSON backup of the SQLite database to the configured data directory.

* `scripts/restore_from_backup.py`
  Restores from a JSON backup into a new SQLite database.

These scripts are designed to be safe for local experimentation.

### 9.2 Testing

Tests focus on:

* Ratings API behavior.
* Tagging and autocomplete.
* Performance metrics collection.
* Basic view rendering.

They are run with:

```bash
pytest
```

The coverage is targeted at critical paths rather than full line coverage.

---

## 10. Adding new features

When adding new features:

1. Add or update API contracts in `docs/API.md`.
2. Update `docs/ARCHITECTURE.md` for new components or data flows.
3. Extend `docs/PERFORMANCE_MONITORING.md` if new metrics are required.
4. Implement the feature in a new or existing module.
5. Update templates and static assets if the UI changes.
6. Add tests for new behavior.
7. Update `docs/IMPLEMENTATION.md` where necessary.

For admin dashboard changes:

* Update `docs/ADMIN_DASHBOARD.md` first so that it remains the source of truth for layout and visual behavior.
* Ensure metric changes are reflected in `docs/PERFORMANCE_MONITORING.md`.
* Then update `templates/admin/performance.html` and any related JS in `static/`.

---

## 11. Legacy and removed features

Certain features no longer ship as part of the active runtime but remain in the repository for reference.

* Subtitle system
  The previous subtitle generation and management pipeline has been removed from the active runtime. Any remaining subtitle helper scripts in `static/` are considered inactive.

Any new implementation work should refer to:

* `docs/ARCHITECTURE.md` for current system structure.
* `docs/API.md` for endpoint contracts.
* `docs/PERFORMANCE_MONITORING.md` for metrics schemas.

This `IMPLEMENTATION.md` is the canonical guide for how the code in this repository fits together today.
