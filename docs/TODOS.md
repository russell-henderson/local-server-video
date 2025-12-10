# TODOS - Local Video Server

This file consolidates outstanding, high-priority tasks and links to archived tasklists. Subtitle generation documentation has been archived because subtitles are out of current scope.

## High-priority tasks

- Deploy cache_manager.py to staging and enable monitoring endpoints.
- Validate database_migration.py on a test dataset before switching production.
- Sweep repository for remaining references to removed VR assets and replace or stub them (some stubs already added under static/).
- Run a documentation pass to ensure README and top-level links point to consolidated docs.

## Lower-priority / Nice-to-have

- Add service-worker for static caching (PWA)
- Explore IndexedDB for client-side metadata caching for very large libraries
- Add optional WebAssembly aids for heavy media processing (experimental)

---

Original task lists and subtitle-related docs moved to docs/deferred/ for traceability.
