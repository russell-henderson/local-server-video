Nice. With `ARCHITECTURE.md` in place, the next clean step is to give the admin dashboard (and everything else) a precise API surface to rely on.

Below is a complete `docs/API.md` you can add as a new file at:

`local-video-server/docs/API.md`

---

````markdown
# Local Video Server API

## 1. Purpose and scope

This document describes the HTTP API surface of Local Video Server.

It covers:

- Public gallery and watch routes
- JSON APIs used by the UI and external clients
- Admin and metrics endpoints used by the admin dashboard
- Planned admin APIs that will be added in later phases

The goal is to give the admin dashboard and any clients a stable contract to build against.

---

## 2. Conventions

### 2.1 Base URL and environment

Local deployment defaults:

- Protocol: `http`
- Host: configured via `ServerConfig.host` (often `0.0.0.0` for LAN)
- Port: configured via `ServerConfig.port` (for example `8080`)

Example base URL for docs:

- `http://localhost:8080`

### 2.2 URL structure

- Public pages:
  - `/`
  - `/watch/<filename>`
  - `/tags`
  - `/tags/<tag>`
  - `/favorites`
- JSON APIs:
  - `/api/...`
- Admin HTML:
  - `/admin/...`
- Admin JSON:
  - `/admin/...` or `/api/admin/...` (future expansion)

### 2.3 CORS

- CORS is controlled by `ServerConfig.enable_cors` and `ServerConfig.allowed_origins`.
- Ratings API explicitly adds CORS headers to support:
  - localhost
  - LAN IPs
  - optionally `.local` hostnames and Quest browser origins
- Admin APIs are intended for local network use only and should remain restricted to trusted origins.

### 2.4 Authentication

Current assumption:

- Local trusted deployment.
- No user authentication layer yet.
- Future authentication can be layered on top of these routes with minimal API shape changes.

---

## 3. Public gallery endpoints

These are HTML endpoints intended for browsers.

### 3.1 GET `/`

**Purpose**

Render the main gallery view.

**Behavior**

- Loads video list from cache and database.
- Injects:
  - thumbnails
  - ratings
  - views
  - basic metadata
- Renders `templates/index.html`.

**Query parameters** (optional)

- `page`: integer, page number for pagination.
- `sort`: string, for example `recent`, `views`, `rating`.
- `tag`: string, filter by tag if supplied.

**Response**

- `200 OK` with HTML page.

---

### 3.2 GET `/watch/<filename>`

**Purpose**

Render the watch page for a specific video.

**Path parameters**

- `filename`: URL encoded filename of the video file.

**Behavior**

- Looks up metadata, rating, and view count based on filename.
- Increments view count.
- Ensures thumbnail and preview assets exist.
- Computes related videos list using tags and metadata.
- Renders `templates/watch.html`.

**Response**

- `200 OK` with HTML on success.
- `404 Not Found` if the video does not exist or is not indexed.

---

### 3.3 GET `/tags`

**Purpose**

Show all tags and tag usage.

**Behavior**

- Aggregates tag list from database or cache.
- Renders `templates/tags.html` with:
  - tag name
  - usage count
  - optional sample thumbnails.

**Response**

- `200 OK` with HTML.

---

### 3.4 GET `/tags/<tag>`

**Purpose**

Show videos that share a specific tag.

**Path parameters**

- `tag`: tag string, usually slugified.

**Behavior**

- Looks up all videos associated with this tag.
- Renders `templates/tag_videos.html` with thumbnails and metadata.

**Response**

- `200 OK` with HTML list of tagged videos.
- `404 Not Found` if tag does not exist.

---

### 3.5 GET `/favorites`

**Purpose**

Show all videos marked as favorites.

**Behavior**

- Reads favorite status from cache and database.
- Renders an HTML gallery of favorite videos.

**Response**

- `200 OK` with HTML.

---

## 4. Ratings API

These endpoints power the rating widget and are used by web browsers, Quest devices, and potentially other clients.

### 4.1 GET `/api/ratings/<media_hash>`

#### Purpose

Fetch rating information for a specific video.

#### Path parameters

- `media_hash`: opaque stable identifier derived from filename or file hash.

#### Request

- Method: `GET`
- Headers:
  - `Accept: application/json`

#### Response

- `200 OK` with JSON body:

```json
{
  "media_hash": "abc123...",
  "filename": "example.mp4",
  "rating": 4.5,
  "rating_count": 12,
  "last_rated_at": "2025-11-15T03:21:00Z"
}
````

* `404 Not Found` if media hash is unknown.

### Notes

* Adds CORS headers based on `allowed_origins`.
* Safe to call from gallery UI or Quest browser.

---

### 4.2 POST `/api/ratings/<media_hash>`

#### Purpose

Set or update a rating for a specific video.

#### Path parameters

* `media_hash`: opaque ID as above.

#### Request

* Method: `POST`
* Headers:

  * `Content-Type: application/json`
  * `Accept: application/json`
* JSON body (schema):

```json
{
  "rating": 4,
  "source": "web" 
}
```

* `rating`: required integer or float in the accepted rating scale (for example 1 to 5).
* `source`: optional string for analytics source, such as `"web"`, `"quest"`, `"mobile"`.

**Response**

* `200 OK` with JSON body:

```json
{
  "media_hash": "abc123...",
  "filename": "example.mp4",
  "rating": 4.0,
  "rating_count": 13,
  "updated_at": "2025-11-15T03:22:10Z"
}
```

* `400 Bad Request` if payload does not validate.
* `404 Not Found` if media hash is unknown.

### Notes

* Implemented by `RatingsService` which:

  * looks up filename from hash
  * updates SQLite and cache
* `PerformanceMetrics` tracks:

  * count
  * p95 latency
  * average latency
    for this endpoint to feed the admin performance dashboard.

---

## 5. Admin HTML endpoints

These endpoints return HTML pages for admin use.

### 5.1 GET `/admin/performance`

#### Purpose

Render the admin performance dashboard.

#### Behavior

* Uses metrics from `PerformanceMetrics` (singleton).
* Renders `templates/admin/performance.html` with cards for:

  * ratings POST p95 latency
  * ratings POST average latency
  * cache hit rate
  * basic uptime and resource stats
* May embed JavaScript that fetches `/admin/performance.json` for live updates.

#### Response

* `200 OK` with HTML.
* `403 Forbidden` in future if auth is added and user is unauthorized.

---

## 6. Admin JSON endpoints

These endpoints are intended for the admin dashboard front end and other monitoring tools.

### 6.1 GET `/admin/performance.json`

#### Purpose

Provide a JSON snapshot of performance metrics for the admin dashboard.

#### Request

* Method: `GET`
* Headers:

  * `Accept: application/json`

#### Response

* `200 OK` with JSON body similar to:

```json
{
  "uptime_seconds": 12345,
  "cache": {
    "hit_rate": 0.94,
    "hits": 1234,
    "misses": 78
  },
  "ratings_post": {
    "count": 56,
    "p95_ms": 42.3,
    "avg_ms": 20.1
  },
  "routes": {
    "/": { "p95_ms": 30.0, "avg_ms": 12.5, "count": 230 },
    "/watch": { "p95_ms": 35.0, "avg_ms": 14.2, "count": 180 }
  }
}
```

* `500 Internal Server Error` if metrics cannot be produced.

#### Notes

* Backed by `PerformanceMetrics` defined in `backend/app/admin/performance.py`.
* The shape above should be kept stable for the dashboard.

---

### 6.2 Planned admin JSON endpoints

The following endpoints are part of the admin dashboard specification and may not all exist yet. They should be implemented in future phases, using the patterns already in place.

#### 6.2.1 GET `/api/admin/overview`

**Purpose: Overview Summary**

Provide a high level system summary for the admin dashboard Overview section.

**Planned response shape**

```json
{
  "server": {
    "version": "1.03.0",
    "uptime_seconds": 12345,
    "video_count": 333,
    "thumbnail_count": 333,
    "library_size_bytes": 1234567890
  },
  "recent_activity": {
    "new_videos_24h": 3,
    "ratings_24h": 12,
    "views_24h": 150
  }
}
```

---

#### 6.2.2 GET `/api/admin/videos/summary`

##### Purpose: Video Analytics Summary

Support dashboard cards for video and engagement analytics.

##### Response shape for video analytics

```json
{
  "totals": {
    "videos": 333,
    "favorites": 45,
    "ratings": 210,
    "views": 12345
  },
  "top_rated": [
    { "media_hash": "abc123", "filename": "a.mp4", "rating": 5.0, "rating_count": 20 },
    { "media_hash": "def456", "filename": "b.mp4", "rating": 4.9, "rating_count": 10 }
  ],
  "most_viewed": [
    { "media_hash": "ghi789", "filename": "c.mp4", "views": 900 },
    { "media_hash": "jkl012", "filename": "d.mp4", "views": 850 }
  ]
}
```

---

#### 6.2.3 GET `/api/admin/search/analytics`

##### Purpose: Search Analytics

Provide search analytics for the Search and Discovery section.

##### Response shape for search analytics

```json
{
  "top_queries": [
    { "query": "cats", "count": 40 },
    { "query": "travel", "count": 25 }
  ],
  "zero_result_queries": [
    { "query": "snowboarding", "count": 5 }
  ],
  "volume_over_time": [
    { "date": "2025-11-01", "count": 30 },
    { "date": "2025-11-02", "count": 45 }
  ]
}
```

---

#### 6.2.4 GET `/api/admin/performance/routes`

##### Purpose: Route Performance Metrics

Expose per route performance metrics for charts.

##### Response shape for route performance metrics

```json
{
  "routes": [
    {
      "path": "/",
      "p50_ms": 10.5,
      "p95_ms": 30.2,
      "p99_ms": 50.1,
      "count": 230
    },
    {
      "path": "/watch",
      "p50_ms": 12.0,
      "p95_ms": 35.0,
      "p99_ms": 60.3,
      "count": 180
    }
  ],
  "updated_at": "2025-11-15T03:45:00Z"
}
```

---

#### 6.2.5 GET `/api/admin/errors/recent`

##### Purpose: Recent Errors and Warnings

Display recent errors and warnings in the Errors and Maintenance section.

##### Response shape for recent errors

```json
{
  "items": [
    {
      "timestamp": "2025-11-15T03:21:00Z",
      "level": "ERROR",
      "source": "thumbnail_worker",
      "message": "ffmpeg failed for file example.mp4",
      "context": {
        "filename": "example.mp4"
      }
    },
    {
      "timestamp": "2025-11-15T03:22:10Z",
      "level": "WARNING",
      "source": "ratings_api",
      "message": "Validation error",
      "context": {
        "media_hash": "abc123"
      }
    }
  ]
}
```

---

#### 6.2.6 GET `/api/admin/storage/summary`

##### Purpose: Storage Usage and Cache Health

Provide storage usage and cache health data.

##### Response shape for storage usage

```json
{
  "library": {
    "video_count": 333,
    "size_bytes": 1234567890
  },
  "thumbnails": {
    "count": 333,
    "size_bytes": 234567890
  },
  "database": {
    "path": "video_metadata.db",
    "size_bytes": 567890
  },
  "backup": {
    "json_backup_exists": true,
    "last_backup_at": "2025-11-10T04:00:00Z"
  }
}
```

---

#### 6.2.7 POST `/api/admin/maintenance/action`

#### Purpose: Maintenance Actions

Trigger maintenance jobs from the dashboard.

##### Planned actions

* `rebuild_thumbnails`
* `reindex_library`
* `compact_database`
* `clear_cache`

**Request**

```json
{
  "action": "rebuild_thumbnails"
}
```

**Response**

* `202 Accepted` with JSON:

```json
{
  "action": "rebuild_thumbnails",
  "status": "queued",
  "job_id": "job_12345"
}
```

---

## 7. Error handling and status codes

General conventions:

* `200 OK` for successful GET and POST that return data or confirmation.
* `202 Accepted` for long running maintenance actions that are queued.
* `400 Bad Request` when input validation fails.
* `404 Not Found` when a resource cannot be found.
* `429 Too Many Requests` when rate limits are exceeded (applies to ratings POST and future APIs).
* `500 Internal Server Error` for unexpected failures.

JSON error format (for JSON endpoints):

```json
{
  "error": "Bad Request",
  "message": "Rating must be between 1 and 5",
  "code": 400
}
```

---

## 8. Versioning

Current server version is tracked in release docs under `docs/releases/`.

API versioning approach:

* The initial set of APIs are treated as version 1.
* If breaking changes are needed later:

  * Add a versioned prefix such as `/api/v2/...` for new endpoints.
  * Keep `/api/...` for backwards compatible or deprecated v1 endpoints.
  * Document changes in:

    * `docs/API.md`
    * relevant release notes in `docs/releases/`

---

## 9. How this connects to other docs

* `ARCHITECTURE.md`
  Describes how these endpoints are implemented, including modules and data flow.

* `IMPLEMENTATION.md`
  Explains how to work on these routes in the codebase, including patterns and tests.

* `PERFORMANCE.md` and `PERFORMANCE_MONITORING.md`
  Describe how performance is measured for these endpoints and how metrics feed the admin dashboard.

* `UI.md`
  Maps admin dashboard cards and views to these endpoints.

* `PROJECT.md`
  Gives the big picture and how the admin dashboard fits into the system.

Keep this file updated whenever you add, remove, or materially change an endpoint so the admin dashboard and any clients always have an accurate contract.
