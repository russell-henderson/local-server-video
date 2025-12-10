# Local Video Server Project Overview

## 1. Purpose

Local Video Server is a local first media server for personal video libraries.  
It scans a folder of videos, builds thumbnails and metadata, and presents a modern gallery with previews, ratings, favorites, tags, and analytics.

This file is the high level project overview and the map for all other documentation.

---

## 2. Core documentation set

These are the canonical docs that describe the system.  
If you update the system in a significant way, you should usually update at least one of these files.

- `README.md`  
  Short public facing introduction plus quick start instructions.

- `docs/PROJECT.md`  
  This file. High level overview, phases, and doc map.

- `docs/ARCHITECTURE.md`  
  System architecture, core components, and data flow between backend, storage, and front end.

- `docs/IMPLEMENTATION.md`  
  How to work on the codebase day to day. Development workflow, modules, patterns, and testing.

- `docs/API.md`  
  REST API layout for gallery, metadata, and admin dashboard endpoints.

- `docs/UI.md`  
  Design system for gallery and dashboard. Layout patterns, components, and interaction rules.

- `docs/PERFORMANCE.md`  
  Performance goals, bottlenecks, and optimization strategy.

- `docs/PERFORMANCE_MONITORING.md`  
  How metrics are collected, stored, and exposed to the admin dashboard.

- `docs/DATA_BACKEND.md`  
  Details of SQLite databases, JSON stores, indexes, and any future storage changes.

- `docs/QA_TESTING_GUIDE.md`  
  Manual and automated test strategy, including smoke tests for gallery and admin dashboard.

- `docs/TODOS.md`  
  Live actionable task list. Short form what to do next.

- `TODOv4.md`  
  Long form roadmap and strategy. Background and future plan.

- `docs/DOCS_INVENTORY.md`  
  Inventory of all docs with Type and Scope classifications.

- `docs/ARCHIVE_INDEX.md`  
  Index of historical docs that are kept only for reference.

- `docs/releases/index.md`  
  Release catalogue with links to individual release docs.

You can treat this list as the spine of the documentation set.

---

## 3. Project phases

The project is organized into four broad phases that can repeat as needed.

### Phase 1: Documentation consolidation

Goal: make the documentation trustworthy and compact.

Key outcomes:

- `DOCS_INVENTORY.md` lists all doc like files with Type and Scope.
- Redundant performance, implementation, and planning docs are archived and merged into:
  - `PERFORMANCE.md`
  - `IMPLEMENTATION.md`
  - `TODOS.md` and `TODOv4.md`
- `ARCHIVE_INDEX.md` explains what is historical and what replaced it.

Status:

- Inventory created.
- Performance cluster consolidated.
- Implementation cluster consolidated.
- Planning cluster normalized.

### Phase 2: Core system spec

Goal: have a clean, current description of the system that matches the running code.

Key outcomes:

- `ARCHITECTURE.md` describes the real architecture and data flow.
- `IMPLEMENTATION.md` matches the current module layout and developer workflow.
- `DATA_BACKEND.md` describes the current state of SQLite and JSON usage.
- `UI.md` documents active gallery and base dashboard design.

Status:

- In progress. Some files may already exist, but each should be checked and updated against the real code.

### Phase 3: Admin dashboard specification and API

Goal: fully specify what the admin dashboard does and how it talks to the backend.

Key outcomes:

- `API.md` lists all endpoints used by the dashboard, including:
  - video analytics
  - engagement metrics
  - search analytics
  - performance and health
  - error monitoring
  - maintenance and export
- Admin dashboard sections are described in enough detail to implement:
  - Overview
  - Videos and engagement
  - Gallery and search
  - Performance and health
  - Errors and maintenance
- Any stack choice for the dashboard front end is recorded here or in `IMPLEMENTATION.md`.

Status:

- High level structure defined in earlier planning docs.
- Needs validation against the current code and any new metrics schema.

### Phase 4: Implementation, monitoring, and polish

Goal: ship and maintain a production ready Local Video Server with a usable admin dashboard.

Key outcomes:

- Admin dashboard front end runs and uses real data.
- Metrics recorded in the backend match `PERFORMANCE_MONITORING.md`.
- QA checks in `QA_TESTING_GUIDE.md` are run and kept up to date.
- New feature work and refactors always update:
  - `ARCHITECTURE.md`
  - `IMPLEMENTATION.md`
  - `API.md`
  - `PERFORMANCE.md`
  - `UI.md` when visuals change

Status:

- To be driven by `docs/TODOS.md` and `TODOv4.md`.

---

## 4. How to work with the docs

Use this section as a personal rule set for future you and for any AI agent.

1. When you add or change a major feature  
   - Update `ARCHITECTURE.md` and `IMPLEMENTATION.md`  
   - If there is a new route or API, update `API.md`  
   - If there is a visible UI change, update `UI.md`  
   - If performance is affected, update `PERFORMANCE.md`

2. When you plan work  
   - Put narrative and strategy into `TODOv4.md`  
   - Put concrete tasks and checklists into `docs/TODOS.md`

3. When you retire or replace a doc  
   - Move the old file into `docs/archive/` or `docs/deferred/`  
   - Add or update an entry in `ARCHIVE_INDEX.md`  
   - Update `DOCS_INVENTORY.md` so the path and Type are correct

4. When you cut a new release  
   - Create a new file under `docs/releases/`  
   - Update `docs/releases/index.md`  
   - Mention any documentation changes that future work depends on

---

## 5. Admin dashboard at a glance

This is a quick summary so you always remember what the admin dashboard is supposed to do.

High level:

- Runs as a web interface that talks to Flask APIs.
- Shows analytics and health for:
  - video usage
  - engagement
  - search
  - performance
  - errors
  - storage and workers
- Provides tools to:
  - clear caches
  - reprocess thumbnails
  - reindex databases
  - export analytics

Detailed behavior and endpoint contracts live in:

- `docs/API.md` for routes and response shapes
- `docs/UI.md` for layout and visual patterns
- `docs/PERFORMANCE_MONITORING.md` for metrics definitions

---

## 6. Next steps from here

When you pick up the project next time, start by:

1. Checking `docs/TODOS.md` for active tasks.  
2. Confirming that any work you plan fits into the phases above.  
3. Updating this file only when the overall project state or doc set changes in a meaningful way.
