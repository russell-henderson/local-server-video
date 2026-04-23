# Tag Cleanup Notes

Automatic cleanup now runs from the tag pages to prevent stale tag data:

- `/tags` and `/tag/<tag>` run a prune pass that clears tag mappings for videos no longer present on disk.
- Sidecar tag aggregation now ignores orphan sidecars where `<video>.<ext>.json` exists but `<video>.<ext>` does not.
- `/tag/<tag>` no longer renders synthetic fallback cards for missing videos.

Outcome:

- Tag lists only include tags that still exist on at least one current video.
- Tag result pages stop showing removed videos.
