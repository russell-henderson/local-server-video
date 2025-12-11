# Archive Index

Purpose: Track historical and superseded documentation so it remains discoverable without competing with the current core docs.

Each section lists archived or legacy docs, what replaced them, and whether you should ever update them again.

Defaults:

- Archived docs are never edited.
- New work goes into the core docs that replaced them.

---

## 1. Performance docs

These files captured the original performance analysis and early optimization plan. Their content has been merged into `docs/PERFORMANCE.md` and `docs/PERFORMANCE_MONITORING.md`.

### 1.1 Files

- `docs/archive/PERFORMANCE_ANALYSIS_SUMMARY_v1.md`  
  - Status: archived  
  - Replaced by: `docs/PERFORMANCE.md`  
  - Notes: original narrative of bottlenecks and estimates

- `docs/archive/PERFORMANCE_OPTIMIZATION_GUIDE_v1.md`  
  - Status: archived  
  - Replaced by: `docs/PERFORMANCE.md`  
  - Notes: original step by step optimization playbook

- `docs/archive/OPTIMIZATION_SUMMARY_v1.md`  
  - Status: archived  
  - Replaced by: `docs/PERFORMANCE.md`  
  - Notes: short summary of optimization goals and progress

### 1.2 How to use

- Read these only if you need historical context.
- Do not copy text back out into new docs.
- If you change performance strategy, update:
  - `docs/PERFORMANCE.md`
  - `docs/PERFORMANCE_MONITORING.md`
  - `docs/LATEST.md` (with a short note)

---

## 2. Implementation docs

These files contain older implementation and migration notes. Their content has been merged into the current implementation guide.

### 2.1 Files

- `docs/archive/IMPLEMENTATION_GUIDE_v1.md`  
- `docs/archive/IMPLEMENTATION_SUMMARY_v1.md`  
- `docs/archive/IMPLEMENTATION_COMPLETION_SUMMARY_v1.md`  
- `docs/archive/MIGRATION_SUMMARY_v1.md`  

### 2.2 How to use

- Read these only if you need historical implementation context.
- Do not update them.
- All new implementation details belong in `docs/IMPLEMENTATION.md` and, when relevant, in:
  - `ARCHITECTURE.md`
  - `API.md`
  - `PERFORMANCE.md`

---

## 3. Subtitle system docs

Subtitle generation and troubleshooting have been removed as an active feature. All related docs are preserved only for history.

### 3.1 Files

- `docs/deferred/SUBTITLE_GENERATION_GUIDE.md`
- `docs/deferred/SUBTITLE_GENERATION_COMPLETE.md`
- `docs/deferred/SUBTITLE_SYSTEM_TROUBLESHOOTING.md`
- `docs/deferred/legacy/SUBTITLE_GENERATION_GUIDE.md`
- `docs/deferred/legacy/SUBTITLE_GENERATION_COMPLETE.md`
- `docs/deferred/legacy/SUBTITLE_SYSTEM_TROUBLESHOOTING.md`

### 3.2 How to use

- Do not treat these as live specs.
- If subtitles ever return as a feature, create a new `docs/SUBTITLES.md` fresh and link back here for history.

---

## 4. Planning and TODO history

These are older planning docs that have been superseded by `TODOv4.md` and `docs/TODOS.md`.

### 4.1 Files

- `docs/TODO.md`
- `docs/TODOv3.md`
- `docs/tasklist.md`
- `docs/tasklist_backup.md`
- `docs/TODO_GROUP_DELETE.md`
- `docs/deferred/PROJECT.md`
- `docs/deferred/TODO.md`
- `docs/deferred/tasklist.md`
- `docs/deferred/tasklist_backup.md`

### 4.2 How to use

- Only read if you need to see how the project evolved.
- Do not add new tasks here.
- All new planning work goes into:
  - `TODOv4.md` for long form
  - `docs/TODOS.md` for current actionable items

---

## 5. UI and legacy template docs

Older UI descriptions and template backups, replaced by `docs/UI.md` and `static/README.md`.

### 5.1 Files

- `docs/Local Video Server UI.md`
- `docs/deferred/Local Video Server UI.md`
- `archive/templates-backup/README.md`

### 5.2 How to use

- For historical screenshots or layout ideas only.
- New UI work should update:
  - `docs/UI.md`
  - component level notes in the codebase

---

## 6. Release and PR notes

Release documents remain part of the core history but are listed here for convenience.

### 6.1 Files

- `docs/releases/v1.02.md`
- `docs/releases/pr_announcement_v1.02.1.md`
- `docs/releases/v1.03.0.md`
- `docs/releases/v1.03.0_SUMMARY.md`
- `docs/PR_2_COMPLETION_NOTES.md`
- `docs/PR_2_POST_MERGE_SUMMARY.md`

### 6.2 How to use

- Do not modify past release notes.
- New releases should:
  - add a new file under `docs/releases/`
  - update `docs/releases/index.md`
  - mention any major documentation changes that affect core docs

---

## 7. Other legacy feature and meta docs

These are one off legacy feature docs or meta docs that are kept for context but are not part of the live spec set.

### 7.1 Files

- `docs/GEMINI.md`  
  - Status: legacy  
  - Scope: earlier AI integration notes that are not part of the current plan

- `docs/deferred/VR_MIGRATION_NOTE.md`  
  - Status: legacy  
  - Scope: early VR migration notes, superseded by newer VR and ratings work

### 7.2 How to use

- Read only when you need deep historical background.
- Do not extend these docs.
- Any new AI integration or VR work should be documented in the current core docs:
  - `ARCHITECTURE.md`
  - `IMPLEMENTATION.md`
  - `UI.md`
  - `API.md`

---

## 8. Admin dashboard working checklist (future archive)

This is a live checklist during development and should be archived once the dashboard ships.

### 8.1 File

- `TODO_ADMIN_DASH.md`  
  - Status: working until dashboard release  
  - Archive path: move to `docs/archive/TODO_ADMIN_DASH.md` after launch (placeholder file already exists)  
  - Notes: stop updating once archived; keep `docs/ADMIN_DASHBOARD.md` and `docs/API.md` as the enduring specs

### 8.2 How to use

- Keep it updated only while the dashboard is in development.
- After release, move it to the archive path above and remove it from active task tracking.
