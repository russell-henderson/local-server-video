# Documentation Inventory

Purpose: Track every documentation file that affects Local Video Server so we can remove redundancies, keep a small core, and safely archive legacy material.

## Classification

**Type**

- Core   = Canonical doc that should remain in the final set
- Working = Active, might be edited or merged, not yet frozen
- Legacy = Historical or superseded, kept only for reference

**Scope**

- High level = Project wide overview, roadmaps, or phase summaries
- Feature = Specific feature or subsystem
- Design = UI, UX, or visual style
- Ops = Operations, releases, QA, or dev tooling

## Task file canon (Phase 0)

Three different paths have historically carried “task” content. **Do not confuse them:**

| Path | Role |
|------|------|
| **`TODO.md` (repo root)** | **Canonical** for Cursor / Copilot / agents: priority-ordered work and acceptance checks (see `.github/` instructions). |
| **`docs/TODOS.md`** | **Docs-facing** index: engineering lanes, supplemental checklists, and pointers to the root task file. Not a replacement for root `TODO.md`. |
| **`docs/archive/TODO_docs_legacy.md`** | **Legacy** (was `docs/TODO.md`); **do not extend**. Archived Phase 1b; not root `TODO.md`. |

## Current inventory

| ID | Path | File name | Type | Scope | Notes |
|---|---|---|---|---|---|
| 1 | ./ | README.md | Core | High level | Keep - core doc |
| 1b | docs/ | PRD.md | Core | High level | Product requirements; keep in sync with SOF/API |
| 2 | docs/ | ARCHITECTURE.md | Core | High level | Keep - core doc |
| 3 | docs/ | project_structure.txt | Working | Ops | Active working doc |
| 4 | ./ | LATEST.md | Core | Ops | Keep - core doc |
| 4a | ./ | TODO.md | Core | High level | **Agent/Cursor/Copilot canonical task queue** (repo root); single source for priorities per `.github/` |
| 5 | ./ | TODOv4.md | Working | High level | Long form roadmap / strategy; pair with root `TODO.md` + `docs/TODOS.md` (see Task file canon above) |
| 6 | docs/ | DOCS_INVENTORY.md | Core | Ops | Keep - core doc |
| 7 | docs/ | ADAPTIVE_STREAMING_SYSTEM.md | Core | Feature | Keep - core doc |
| 8 | docs/ | ARCHIVE_INDEX.md | Core | Ops | Keep - core doc |
| 9 | docs/ | CHANGELOG.md | Core | Ops | Keep - core doc |
| 10 | docs/ | DATA_BACKEND.md | Core | Feature | Keep - core doc |
| 11 | docs/archive/ | GEMINI.md | Legacy | Feature | Moved Phase 1a from docs/ |
| 12 | docs/ | IMPLEMENTATION.md | Core | High level | Keep - core doc |
| 13 | docs/archive/ | IMPLEMENTATION_COMPLETION_SUMMARY_v1.md | Legacy | Ops | Archived completion notes, replaced by docs/IMPLEMENTATION.md |
| 14 | docs/archive/ | IMPLEMENTATION_GUIDE_v1.md | Legacy | Feature | Archived early implementation guide, replaced by docs/IMPLEMENTATION.md |
| 15 | docs/archive/ | IMPLEMENTATION_SUMMARY_v1.md | Legacy | Feature | Archived implementation summary, replaced by docs/IMPLEMENTATION.md |
| 16 | docs/archive/ | Local_Video_Server_UI_legacy.md | Legacy | Design | Moved Phase 1a from docs/Local Video Server UI.md |
| 17 | docs/archive/ | MIGRATION_SUMMARY_v1.md | Legacy | Feature | Archived migration notes, details now live in docs/IMPLEMENTATION.md |
| 18 | docs/ | OPENAI_COST_ANALYSIS.md | Core | Feature | Keep - core doc |
| 19 | docs/archive/ | OPTIMIZATION_SUMMARY_v1.md | Legacy | Feature | Archived historic optimization summary, replaced by docs/PERFORMANCE.md |
| 20 | docs/ | PERFORMANCE.md | Core | Feature | Keep - core doc |
| 21 | docs/archive/ | PERFORMANCE_ANALYSIS_SUMMARY_v1.md | Legacy | Feature | Archived historic performance analysis, replaced by docs/PERFORMANCE.md |
| 22 | docs/ | PERFORMANCE_MONITORING.md | Core | Feature | Keep - core doc |
| 23 | docs/archive/ | PERFORMANCE_OPTIMIZATION_GUIDE_v1.md | Legacy | Feature | Archived historic optimization guide, replaced by docs/PERFORMANCE.md |
| 24 | docs/ | PROJECT.md | Core | High level | Keep - core doc |
| 25 | docs/archive/ | PR_2_COMPLETION_NOTES.md | Legacy | Ops | Moved Phase 1a from docs/ |
| 26 | docs/archive/ | PR_2_POST_MERGE_SUMMARY.md | Legacy | Ops | Moved Phase 1a from docs/ |
| 27 | docs/archive/ | PYTHON_UPDATE.md | Legacy | Ops | Moved Phase 1a from docs/ |
| 28 | docs/ | QA_TESTING_GUIDE.md | Core | Ops | Keep - core doc |
| 29 | docs/archive/ | SUBTITLE_GENERATION_GUIDE.md | Legacy | Feature | Moved Phase 1a from docs/ |
| 30 | docs/archive/ | TASK_2_COMPLETION.md | Legacy | Ops | Moved Phase 1a from docs/ |
| 31 | docs/archive/ | TODO_docs_legacy.md | Legacy | High level | Moved Phase 1b from `docs/TODO.md` (not root `TODO.md`) |
| 32 | docs/ | TODOS.md | Core | High level | **Docs-facing** task index / supplemental checklists; points to root `TODO.md` for agent priorities |
| 33 | docs/archive/ | TODO_GROUP_DELETE.md | Legacy | Feature | Moved Phase 1a from docs/ |
| 34 | docs/archive/ | TODOv3.md | Legacy | High level | Moved Phase 1a from docs/ |
| 35 | docs/ | UI.md | Core | Design | Keep - core doc |
| 36 | docs/archive/ | UPDATE.md | Legacy | Ops | Moved Phase 1a from docs/ |
| 37 | docs/ | VIDEO_PREVIEW_IMPROVEMENTS.md | Core | Feature | Keep - core doc |
| 38 | docs/ | VR_RATINGS_FAVORITES_FIX.md | Working | Feature | Active working doc |
| 39 | docs/ | copilot_needs_help.md | Working | Ops | Active working doc |
| 40 | docs/archive/ | tasklist.md | Legacy | Feature | Moved Phase 1a from docs/ |
| 41 | docs/deferred/ | IMPLEMENTATION_GUIDE.md | Legacy | Feature | Legacy - archive |
| 42 | docs/deferred/ | IMPLEMENTATION_SUMMARY.md | Legacy | Ops | Legacy - archive |
| 43 | docs/deferred/ | Local Video Server UI.md | Legacy | Design | Legacy - archive |
| 44 | docs/deferred/ | OPTIMIZATION_SUMMARY.md | Legacy | Feature | Legacy - archive |
| 45 | docs/deferred/ | PERFORMANCE_ANALYSIS_SUMMARY.md | Legacy | Feature | Legacy - archive |
| 46 | docs/deferred/ | PERFORMANCE_OPTIMIZATION_GUIDE.md | Legacy | Feature | Legacy - archive |
| 47 | docs/deferred/ | PROJECT.md | Legacy | High level | Legacy - archive |
| 48 | docs/deferred/ | README.md | Legacy | Ops | Legacy - archive |
| 49 | docs/deferred/ | SUBTITLE_GENERATION_COMPLETE.md | Legacy | Feature | Legacy - archive |
| 50 | docs/deferred/ | SUBTITLE_GENERATION_GUIDE.md | Legacy | Feature | Legacy - archive |
| 51 | docs/deferred/ | SUBTITLE_SYSTEM_TROUBLESHOOTING.md | Legacy | Feature | Legacy - archive |
| 52 | docs/deferred/ | TODO.md | Legacy | High level | Legacy - archive |
| 53 | docs/deferred/ | VIDEO_PREVIEW_IMPROVEMENTS.md | Legacy | Feature | Legacy - archive |
| 54 | docs/deferred/ | VR_MIGRATION_NOTE.md | Legacy | Feature | Legacy - archive |
| 55 | docs/deferred/ | legacy/SUBTITLE_GENERATION_COMPLETE.md | Legacy | Feature | Legacy - archive |
| 56 | docs/deferred/ | legacy/SUBTITLE_GENERATION_GUIDE.md | Legacy | Feature | Legacy - archive |
| 57 | docs/deferred/ | legacy/SUBTITLE_SYSTEM_TROUBLESHOOTING.md | Legacy | Feature | Legacy - archive |
| 58 | docs/deferred/ | tasklist.md | Legacy | High level | Legacy - archive |
| 59 | docs/deferred/ | tasklist_backup.md | Legacy | High level | Legacy - archive |
| 60 | docs/releases/ | index.md | Core | Ops | Keep - core doc |
| 61 | docs/releases/ | pr_announcement_v1.02.1.md | Core | Ops | Keep - core doc |
| 62 | docs/releases/ | v1.02.md | Core | Ops | Keep - core doc |
| 63 | docs/releases/ | v1.03.0.md | Core | Ops | Keep - core doc |
| 64 | docs/releases/ | v1.03.0_SUMMARY.md | Core | Ops | Keep - core doc |
| 65 | archive/templates-backup/ | README.md | Legacy | Design | Legacy - archive |
| 66 | static/ | README.md | Core | Feature | Keep - core doc |
| 67 | tools/ | README.md | Core | Ops | Keep - core doc |
| 68 | docs/ | ADMIN_DASHBOARD_IMPL_NOTES.md | Working | Feature | Implementation companion to admin dashboard UI spec |
| 69 | docs/ | ADMIN_API_SPEC.md | Working | Feature | Admin dashboard API contract for JSON endpoints |
| 70 | docs/ | ADMIN_DASHBOARD_BACKEND.md | Working | Feature | Backend implementation guide for admin dashboard endpoints |
| 71 | docs/ | ADMIN_DASHBOARD_FRONTEND.md | Working | Feature | Frontend implementation guide for admin dashboard UI |
| 72 | docs/ | ADMIN_DASHBOARD_MIGRATION.md | Working | Feature | Step by step guide to add the admin dashboard to existing deployments |
| 73 | docs/ | ADMIN_DASHBOARD_TESTING.md | Working | Feature | Testing strategy and checklists for admin dashboard backend and UI |
| 74 | docs/ | ADMIN_DASHBOARD.md | Working | Feature | Single source of truth for admin dashboard UI spec |
| 75 | docs/archive/ | TODO_ADMIN_DASH.md | Legacy | Feature | Admin dashboard implementation checklist (archive reference) |
| 76 | docs/archive/doc_legacy/ | ADMIN_DASH_UPGRADE.md | Legacy | Design | Aspirational Next.js/Tailwind admin concept (not shipped Flask dashboard) |
| 77 | docs/ | API.md | Core | Feature | Keep - HTTP API surface |
| 78 | docs/ | ADMIN_METADATA_PRUNE.md | Working | Feature | POST /admin/metadata/prune contract and response shape |

## Redundancy groups

These groups identify clusters of overlapping docs. Each group has a target Core doc and a set of members that will either be merged into it or archived.

### Group 1: Performance docs

- **Target core doc**: `docs/PERFORMANCE.md`
- **Related core sibling**: `docs/PERFORMANCE_MONITORING.md`
- **Members to consolidate or archive**  
  - `docs/PERFORMANCE_ANALYSIS_SUMMARY.md`  
  - `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md`  
  - `docs/OPTIMIZATION_SUMMARY.md`  
  - `docs/deferred/PERFORMANCE_ANALYSIS_SUMMARY.md`  
  - `docs/deferred/PERFORMANCE_OPTIMIZATION_GUIDE.md`  
  - `docs/deferred/OPTIMIZATION_SUMMARY.md`  

Planned outcome: all narrative and prescription for performance lives in `PERFORMANCE.md` and `PERFORMANCE_MONITORING.md`. All other performance files are archived as history only.

---

### Group 2: Implementation docs

- **Target core doc**: `docs/IMPLEMENTATION.md`
- **Members to consolidate or archive**  
  - `docs/IMPLEMENTATION_GUIDE.md`  
  - `docs/IMPLEMENTATION_SUMMARY.md`  
  - `docs/IMPLEMENTATION_COMPLETION_SUMMARY.md`  
  - `docs/MIGRATION_SUMMARY.md`  
  - `docs/deferred/IMPLEMENTATION_GUIDE.md`  
  - `docs/deferred/IMPLEMENTATION_SUMMARY.md`  

Planned outcome: all implementation guidance and completion notes are merged into `IMPLEMENTATION.md`. Remaining files are archived.

---

### Group 3: TODO and planning docs

- **Target core docs**:  
  - **Agent task queue (canonical):** `TODO.md` at repo root  
  - **Docs-facing index:** `docs/TODOS.md` (supplemental lanes; points to root `TODO.md`)  
  - **Long form plan:** `TODOv4.md`  

- **Members to consolidate or archive**  
  - `docs/archive/TODO_docs_legacy.md` (was `docs/TODO.md`; Phase 1b — not root `TODO.md`)  
  - `docs/archive/TODOv3.md` (was `docs/TODOv3.md`; Phase 1a)  
  - `docs/todos.md` or variants if present  
  - `docs/archive/tasklist.md` (was `docs/tasklist.md`; Phase 1a)  
  - `docs/deferred/tasklist_backup.md`  
  - `docs/archive/TODO_GROUP_DELETE.md` (was `docs/TODO_GROUP_DELETE.md`; Phase 1a)  
  - `docs/deferred/PROJECT.md`  
  - `docs/deferred/TODO.md`  
  - `docs/deferred/tasklist.md`  
  - `docs/deferred/tasklist_backup.md`  

Planned outcome: active agent work is tracked in **root `TODO.md`**; narrative roadmap in **`TODOv4.md`**; **`docs/TODOS.md`** remains the docs-side index. **Do not** list `docs/PROJECT.md` as an archive member — it is core. Legacy duplicate task file **`docs/archive/TODO_docs_legacy.md`** (formerly `docs/TODO.md`) is archive-only history.

---

### Group 4: Subtitle system docs

- **Target core doc**: none, feature has been removed from the product
- **Members to archive and stop referencing**  
  - `docs/archive/SUBTITLE_GENERATION_GUIDE.md` (was `docs/SUBTITLE_GENERATION_GUIDE.md`; Phase 1a)  
  - `docs/SUBTITLE_GENERATION_COMPLETE.md`  
  - `docs/SUBTITLE_SYSTEM_TROUBLESHOOTING.md`  
  - `docs/deferred/SUBTITLE_GENERATION_GUIDE.md`  
  - `docs/deferred/SUBTITLE_GENERATION_COMPLETE.md`  
  - `docs/deferred/SUBTITLE_SYSTEM_TROUBLESHOOTING.md`  
  - `docs/deferred/legacy/SUBTITLE_GENERATION_GUIDE.md`  
  - `docs/deferred/legacy/SUBTITLE_GENERATION_COMPLETE.md`  
  - `docs/deferred/legacy/SUBTITLE_SYSTEM_TROUBLESHOOTING.md`  

Planned outcome: subtitle system remains fully documented only in archive for historical context. No core docs should mention it as an active feature.

---

### Group 5: UI and visual design docs

- **Target core docs**:  
  - Design system: `docs/UI.md`  
  - Static assets notes: `static/README.md`  

- **Members to consolidate or archive**  
  - `docs/archive/Local_Video_Server_UI_legacy.md` (was `docs/Local Video Server UI.md`; Phase 1a)  
  - `docs/deferred/Local Video Server UI.md`  
  - `archive/templates-backup/README.md`  

- **Related implementation companion**  
  - `docs/ADMIN_DASHBOARD_IMPL_NOTES.md` is a working implementation notes file that ties the admin dashboard UI spec and metrics schema to real endpoints and templates. Keep it in sync with `docs/ADMIN_DASHBOARD.md` and `docs/PERFORMANCE_MONITORING.md`, but do not treat it as a consolidation target.

Planned outcome: all current UI guidance and visual rules live in `UI.md`. Old UI descriptions and template backups are archive only. Implementation details that affect UI are tracked in `ADMIN_DASHBOARD_IMPL_NOTES.md` and reflected into `IMPLEMENTATION.md` as needed.

---

### Group 6: Release and PR notes

- **Target core docs**:  
  - Release index: `docs/releases/index.md`  

- **Members that remain as historical records**  
  - `docs/releases/v1.02.md`  
  - `docs/releases/pr_announcement_v1.02.1.md`  
  - `docs/releases/v1.03.0.md`  
  - `docs/releases/v1.03.0_SUMMARY.md`  
  - `docs/archive/PR_2_COMPLETION_NOTES.md` (was `docs/PR_2_COMPLETION_NOTES.md`; Phase 1a)  
  - `docs/archive/PR_2_POST_MERGE_SUMMARY.md` (was `docs/PR_2_POST_MERGE_SUMMARY.md`; Phase 1a)  

Planned outcome: releases stay as a family of core historical documents. PR completion notes are treated as legacy but kept for forensic reference.

---

### Group 7: One off legacy and working docs

These do not have strong redundancy but should be handled consistently.

- `docs/archive/GEMINI.md` (was `docs/GEMINI.md`; Phase 1a)  
  - Status: legacy feature doc  
  - Plan: keep in archive, do not treat as core  

- `docs/VR_RATINGS_FAVORITES_FIX.md`  
  - Status: working  
  - Plan: once fully merged into implementation and performance docs, move to archive  

- `docs/copilot_needs_help.md`  
  - Status: working meta doc  
  - Plan: keep as is for now, archive when no longer useful  

Planned outcome: these files are either archived or mapped into core docs as part of specific features, with no redundant new copies created.

---

### Group 8: Admin dashboard docs

- **Read map (Phase 2):** canonical table of every admin doc and its role — [`docs/PROJECT.md`](PROJECT.md) → section **Admin dashboard documentation cluster** (after the core documentation spine list).
- **Target working spec**: `docs/ADMIN_DASHBOARD.md` is the UI source of truth; `docs/API.md` defines the HTTP contracts it relies on.
- **Companion working guides**: keep `docs/ADMIN_DASHBOARD_IMPL_NOTES.md`, `docs/ADMIN_DASHBOARD_BACKEND.md`, `docs/ADMIN_DASHBOARD_FRONTEND.md`, `docs/ADMIN_DASHBOARD_MIGRATION.md`, `docs/ADMIN_DASHBOARD_TESTING.md`, `docs/ADMIN_API_SPEC.md`, and `docs/ADMIN_METADATA_PRUNE.md` in sync with the spec and with `IMPLEMENTATION.md` as features ship.
- **Implementation tracker**: `docs/archive/TODO_ADMIN_DASH.md` is a frozen checklist reference (not maintained as live status).
- **Concept-only doc**: `docs/archive/doc_legacy/ADMIN_DASH_UPGRADE.md` is an aspirational Next.js/Tailwind redesign; keep it separate from the Flask dashboard spec and treat as reference only.

Planned outcome: admin dashboard work stays consolidated in the spec and its companions; checklists and concept docs remain reference material without spawning new redundant specs.
