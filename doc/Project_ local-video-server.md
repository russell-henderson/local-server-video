Project: `local-video-server`

Objective: clean up and stabilize the project without breaking any currently working runtime behavior, Docker behavior, routes, or metadata persistence.

Context you must treat as current:

* Core backend runtime is functional.  
    
* `python -m compileall -q main.py cache_manager.py config.py database_migration.py file_watcher.py thumbnail_manager.py backend tests` passed.  
    
* `python -m pytest -q tests/test_basic.py tests/test_routes.py` passed.  
    
* Full suite is not yet trustworthy due to test harness inconsistency, temp-dir assumptions, optional dependency fragility, and at least one API contract drift.  
    
* Safe sequence already identified:  
    
  1. test harness stabilization  
  2. dependency/import hardening  
  3. contract alignment  
  4. maintainability cleanup

Hard constraints:

* Do not break anything currently working.  
* Do not change Docker compose topology, ports, proxy behavior, or runtime entrypoints.  
* Do not refactor production routes or data flows unless required for the scoped phase.  
* Do not mix behavior-changing API contract changes into the same patch as test harness fixes.  
* Prefer smallest safe edits with clear rollback.  
* Preserve SQLite-first metadata behavior and existing JSON fallback/backups.  
* Keep changes phase-scoped and test-gated.

Phase to execute now: PHASE 0 ONLY: test harness stabilization with no product behavior change.

Tasks:

1. Inspect the existing `tests/` tree and identify all fixture dependencies currently assumed but not globally defined.  
     
2. Add a canonical `tests/conftest.py` that provides shared fixtures needed for the currently failing suites, including:  
     
   * `app`  
   * `client`  
   * `mock_ratings_service`  
   * any minimal reset fixture needed for deterministic rate-limit-related tests

   

3. Standardize temporary path behavior so tests do not fail because of constrained OS temp directory behavior. Prefer a workspace-local pytest temp base such as `.tmp/pytest`, using `pytest.ini` or equivalent minimal configuration.  
     
4. Update developer test commands only if they are currently misleading, so local execution targets the real pytest entrypoints.  
     
5. Do not change runtime product behavior, API semantics, or database contracts in this phase.

Required output:

* First, provide a short audit summary of the exact files you plan to change and why.  
* Then provide the full updated contents of each changed file.  
* Then provide the exact test commands to run for this phase.  
* Then provide a short risk check explaining why the phase is non-breaking.  
* If you discover a blocker that would force product-behavior changes, stop and report it instead of improvising.

Acceptance target for this phase:

* No fixture-related test collection failures for the targeted suites.  
* Targeted tests run reproducibly in the workspace environment.  
* No runtime route, DB, Docker, or proxy behavior changes.

