Project: `local-video-server`

Phase 0, Phase 1, and Phase 2 are complete.

Verified completed work:

* Phase 0: test harness stabilization succeeded  
* Phase 1: `psutil` optional dependency hardening succeeded  
* Phase 2: ratings API contract alignment succeeded  
* Unknown/unresolved `media_hash` now returns 404  
* Invalid rating payload remains 400  
* Valid known-hash success path remains 201 with same response structure  
* No DB schema, Docker topology, proxy behavior, metadata persistence, or runtime entrypoints were changed in Phases 0-2

Objective for this prompt: Execute PHASE 3 ONLY: maintainability and deprecation cleanup, with no intended product behavior changes.

Scope for this phase:

1. Deduplicate repeated helper methods in `database_migration.py` without changing behavior  
2. Migrate Pydantic schema config to v2 style where applicable, preserving schema/output behavior  
3. Replace `datetime.utcnow()` with timezone-aware UTC generation where applicable, preserving stored values/semantics as closely as possible

Hard constraints:

* Do not break anything currently working  
* Do not change Docker topology, ports, proxy behavior, or runtime entrypoints  
* Do not change route contracts, ratings semantics, CORS behavior, rate limiting, or admin API shapes  
* Do not change DB schema unless absolutely required, and if you think it is required, stop and report before editing  
* Do not mix in unrelated refactors  
* Keep edits minimal, reversible, and behavior-preserving  
* Preserve metadata persistence behavior  
* Preserve response shapes and existing successful test behavior

Tasks:

1. Audit:  
     
   * `database_migration.py` for duplicated helper methods or duplicated logic blocks  
   * schema modules using Pydantic v1-style `class Config`  
   * runtime paths using `datetime.utcnow()`

   

2. Implement the smallest safe cleanup for each item in scope.  
     
3. Preserve runtime behavior and output as closely as possible.  
     
4. Update tests only if necessary to reflect warning/deprecation cleanup, not product behavior changes.  
     
5. Do not alter unrelated files.

Required output:

* First, provide a short audit summary of the exact files you plan to change and why  
* Then provide the full updated contents of each changed file  
* Then provide the exact targeted test commands to run for this phase  
* Then provide a short risk check explaining why the phase is non-breaking  
* If any cleanup item would require behavior-changing edits or schema changes, stop and report that clearly instead of improvising

Acceptance target for this phase:

* Duplicated helper definitions in `database_migration.py` are removed or consolidated safely  
* Pydantic config is updated to v2 style where applicable without changing behavior  
* `datetime.utcnow()` usage in scoped runtime paths is replaced with timezone-aware UTC handling  
* No route/API/DB-contract/Docker/proxy changes are introduced

