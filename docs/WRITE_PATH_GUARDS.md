# Write Path Guards

Metadata write endpoints now validate that the target video currently exists on disk before writing.

## Guarded Endpoints

- `POST /rate`
- `POST /view`
- `POST /tag`
- `POST /delete_tag`
- `POST /favorite`
- `GET /api/tags/video`

## Behavior

- Missing/empty `filename` returns `400` (`{"error":"Missing filename"}`).
- Non-existent video filename returns `404` (`{"error":"Video not found"}`).
- Valid existing video continues through normal write/read logic.

## Why

This prevents orphan ratings/views/tags/favorites rows from being created for videos that were removed, and keeps tag/favorites/ratings pages aligned with the real video library.
