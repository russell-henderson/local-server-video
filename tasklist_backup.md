You are Cursor working on Local Video Server. Implement the following improvements without adding frameworks.

1) Dev workflow and code quality:

- Add pre-commit with black, ruff, isort, prettier, stylelint. Configure minimal rules. Fail on format errors.
- Add a Makefile with: dev, prod, lint, test, reindex, backup.
- Add a config layer: config.py with dataclass, reads .env then config.json, with sensible defaults.

2) Automation:

- Add a watchdog-based indexer script that listens to the videos/ folder and calls existing index functions on create, move, delete. Run as a background thread when app starts and provide a CLI entry to run standalone.
- Add Windows Task Scheduler docs and sample .bat files for nightly reindex, cache prune, and backup tasks.

3) Search and discovery:

- Add SQLite FTS5-based search as a first step (table for files with title, tags, people, ai_labels). Simple search endpoint and navbar search field with instant results.

4) UX:

- Add “Continue Watching” row using stored resume times. Fallback to server if localStorage empty.
- Add Playlists/Queue: ephemeral queue persisted in localStorage. Use the same player.js.

5) Admin:

- Add /admin/logs route to view last N lines of JSON logs, filter by level.
- Add /admin/actions with buttons: Reindex, Clean Cache, Export Metadata. Each posts to existing endpoints and shows a progress bar.

Keep the unified player and dark mode. Do not reintroduce glass/neomorphic or VR. Keep hover preview behind a feature flag. Write small commits with clear messages.
