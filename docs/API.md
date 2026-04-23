## Local Video Server API

## 1. Purpose and scope

This document describes the HTTP API surface of Local Video Server.

It covers:

- Public gallery and watch routes
- JSON APIs used by the UI and external clients
- Admin and metrics endpoints used by the admin dashboard
- Planned admin APIs that will be added in later phases

The goal is to give the admin dashboard and any clients a stable contract to build against.

---

## Stable Public Routes

- `GET /watch/<filename>`
- `GET /video/<filename>`
- `GET /tag/<tag>`
- `GET /admin/cache/status`
- `POST /admin/cache/refresh`
- `GET|POST /api/ratings/<media_hash>`

---

## Ratings API

These endpoints power the rating widget and are used by web browsers, Quest devices, and potentially other clients.

### GET `/api/ratings/<media_hash>`

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
  "average": 4.0,
  "count": 1,
  "user": { "value": 4 }
}
```

- `404` when `media_hash` cannot be resolved.

### POST `/api/ratings/<media_hash>`

- Body:
```json
{ "value": 4 }
```
- `201` on success with the same summary shape as GET.
- `400` for invalid value.
- `404` for unknown hash.
- `429` when write rate limit is exceeded.

## Legacy Compatibility Route

### POST `/rate`

- Kept intentionally as a compatibility wrapper during migration.
- Body:
```json
{ "filename": "example.mp4", "rating": 4 }
```
- Returns:
```json
{ "success": true, "rating": 4 }
```

## Tags/Favorites Runtime Contract

- `POST /tag`
- `POST /delete_tag`
- `GET /api/tags/popular`
- `GET /api/tags/video?filename=<name>`
- `POST /favorite`
- `GET /favorites`

These routes read/write through DB-backed cache services at runtime.

## Admin Cache Contract

- `GET /admin/cache/status` -> metadata status payload with `video_count`.
- `POST /admin/cache/refresh` -> `{ "success": true, "message": "Cache refreshed" }`.
