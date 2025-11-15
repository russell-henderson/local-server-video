# Implementation — Local Video Server

This consolidated implementation document combines the project-level summary, development workflow, and UI implementation guidance into a single reference. The original documents have been archived to docs/deferred/ for traceability.

## Project & Development Summary

See the archived originals for full historical context. Key points:

- Development workflow exposed via dev.ps1 with commands for dev/prod/install/lint/test/reindex/backup/health/clean.
- Configuration is dataclass-based (config.py) with cascade: env vars → .env → config.json → defaults.
- ile_watcher.py provides efficient, debounced monitoring with background thumbnail generation and duplicate detection.

### Architecture Highlights

- Modular Python scripts: main.py, cache_manager.py, database_migration.py, performance_monitor.py.
- Data files: ideo_metadata.db (SQLite), avorites.json, atings.json, 	ags.json, iews.json.
- Templates & static assets under 	emplates/ and static/.

## UI Implementation Summary

This project follows a unified UI approach with a single shared player, responsive video cards, and accessible controls.

- Theme & UX: theme manager supports Dark/Light, keyboard shortcuts, and persisted user preferences.
- Video cards: hover/tap preview system with adaptive behavior for mobile/VR; touch-friendly hit targets and accessibility considerations.
- Player controls: consistent, accessible controls (play/pause, volume, scrub, fullscreen, ±10s skip, keyboard bindings).

Key implementation artifacts live in static/ (e.g., optimized-utils.js, ideo-preview-enhanced.js, avorites.js) and 	emplates/_player.html.

## Developer Commands & Notes

- Use .\dev.ps1 dev to start development server with live reload.
- Use .\dev.ps1 lint and .\dev.ps1 test to run checks.
- Backup configuration and data before performing migrations.

---

For the full original contents of the archived files, see docs/deferred/IMPLEMENTATION_GUIDE.md, docs/deferred/IMPLEMENTATION_SUMMARY.md, and docs/deferred/PROJECT.md.
