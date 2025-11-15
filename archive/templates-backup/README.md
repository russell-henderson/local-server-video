# Archive: Template Backups

**Status**: Archived - Legacy backup files from template consolidation

**Reason**: During Task 1 (Directory and file layout normalization), all template backup files were consolidated and archived. The application now maintains one canonical `watch.html` and one reusable `partials/rating.html`.

**Archived Files**:

- `best_of.html.backup` - Superseded by main `best_of.html`
- `favorites.html.backup` - Superseded by main `favorites.html`
- `index.html.backup` - Superseded by main `index.html`
- `tag_videos.html.backup` - Superseded by main `tag_videos.html`
- `tags.html.backup` - Superseded by main `tags.html`
- `watch.html.backup` - Superseded by consolidated `watch.html` + `partials/rating.html`

These files are no longer needed as the codebase now follows a single-source-of-truth pattern for all templates. Refer to `z:\local-video-server\templates\` for the current, active templates.

**References**:

- Task 1: Directory and file layout normalization (TODO.md)
- Acceptance: `templates/` has a single `watch.html` and a `partials/rating.html`
