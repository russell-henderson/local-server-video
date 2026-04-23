# Admin Metadata Prune

Use this endpoint to run a one-shot cleanup of stale metadata for videos that no longer exist on disk.

## Endpoint

- `POST /admin/metadata/prune`

## What It Prunes

- ratings rows for missing filenames
- views rows for missing filenames
- favorites rows for missing filenames
- tag rows (`video_tags`) for missing filenames

## Response Shape

```json
{
  "success": true,
  "videos_on_disk": 765,
  "ratings_removed": 3,
  "views_removed": 4,
  "favorites_removed": 2,
  "tag_entries_removed": 11,
  "tag_values_removed": 5
}
```

## Notes

- Idempotent: running it again after cleanup should report zeros removed.
- Manual/admin-only flow: it does not run automatically on normal page requests.
- Each run is logged in server logs with `[PRUNE] metadata summary=...`.
