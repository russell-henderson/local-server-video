## Tag Sync Notes

This change hardens watch-page tag accuracy by using a merged read path for each video:

- `watch` now merges DB/cache tags with sidecar tags from `videos/<filename>.json`.
- New endpoint: `GET /api/tags/video?filename=<video>` returns current merged tags for one video.
- `static/js/tags.js` now refreshes `#existing-tags` from that endpoint on page load.

Why this matters:

- Prevents stale or incomplete tags on active watch pages when sidecar files were updated outside the app.
- Keeps `/watch/<filename>` consistent with merged-tag behavior already used by `/tags` and `/tag/<tag>`.
