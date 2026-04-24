# Local Video Server TODOs

## Task file canon (read first)

- **Agent / Cursor / Copilot canonical queue:** [`TODO.md`](../TODO.md) at the **repository root**. That file is the single place to read priority-ordered work and to check off acceptance criteria for automation and humans using agent instructions.
- **This file (`docs/TODOS.md`):** a **docs-facing** engineering task index and supplemental checklist map (historical completions, stability lanes, and hygiene items). It does **not** replace the root task file; keep it aligned with or summarized from `../TODO.md` where useful.
- **Do not extend** `docs/archive/TODO_docs_legacy.md` (archived from `docs/TODO.md`, Phase 1b) — **legacy** duplicate of the task-file name; use root `TODO.md` instead (see `docs/DOCS_INVENTORY.md`).

## Active

- [x] Complete app-factory + full route-family blueprint extraction.
- [x] Remove or archive stale `doc/` materials after final content merge into `docs/`.
- [x] Finish retirement of legacy fragmented tests after two-suite parity is proven in CI.

## Stability Lane (ratings/favorites/tags)

- [x] Keep one active ratings controller (`static/js/ratings.js`).
- [x] Reuse shared rating partial on key card/watch surfaces.
- [x] Fix favorites route endpoint mismatch in templates.
- [x] Add explicit sidecar tag import command (`scripts/import_sidecar_tags_to_db.py`).
- [x] Switch runtime tag APIs to DB-backed reads.

## Data/Runtime

- [x] Standardize runtime DB defaults to `data/video_metadata.db`.
- [x] Standardize compose DB mount path to `/app/data/...`.
- [x] Remove automatic JSON runtime fallback paths in cache/services.

## Tests

- [x] Create `tests/test_smoke_suite.py`.
- [x] Create `tests/test_regression_suite.py`.
- [x] Fold remaining legacy tests into the two suite files and archive leftovers.

## Optional Hygiene

- [x] Move root legacy DB/JSON artifacts into `backups/` (non-destructive, no deletes).
- [x] Resolve non-functional template lint warnings where behavior remains unchanged.

## Documentation cleanup

- [x] Phase 2 (admin docs): consolidated read map in `docs/PROJECT.md` (**Admin dashboard documentation cluster**); `docs/DOCS_INVENTORY.md` Group 8 points to it; removed erroneous opening markdown fence from `docs/ADMIN_DASHBOARD.md`.
