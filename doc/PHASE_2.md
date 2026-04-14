Project: `local-video-server`

Phase 0 and Phase 1 are complete.

Verified completed work:

* Phase 0: test harness stabilization succeeded  
* Phase 1: `psutil` optional dependency hardening succeeded  
* No runtime routes, DB schema, Docker topology, proxy behavior, metadata persistence, or entrypoints were changed in those phases  
* When `psutil` is present, behavior is preserved  
* When `psutil` is absent, imports and system-metric snapshots degrade gracefully with the same key structure and numeric defaults

Objective for this prompt: Execute PHASE 2 ONLY: ratings API contract alignment for unknown `media_hash`, with minimal, isolated behavior change.

Contract to implement:

* Unknown/unresolved `media_hash` must return **404 Not Found**  
* Invalid rating payloads must remain **400 Bad Request**  
* Valid known hash requests must preserve current successful behavior

Hard constraints:

* Do not break anything currently working  
* Do not change Docker topology, ports, proxy behavior, or runtime entrypoints  
* Do not modify DB schema in this phase unless absolutely required  
* Do not mix in Phase 3 maintainability cleanup or unrelated refactors  
* Keep edits minimal and reversible  
* Preserve metadata persistence behavior  
* Keep rate limiting behavior unchanged  
* Keep response shape unchanged for valid requests unless a change is required by the contract fix

Tasks:

1. Audit the current ratings flow across:  
     
   * `backend/services/ratings_service.py`  
   * `backend/app/api/ratings.py`  
   * any related exception mapping or helper functions

   

2. Identify exactly where unknown `media_hash` currently falls into a 400 path.  
     
3. Implement the narrowest safe change so unresolved hash maps to HTTP 404 instead.  
     
4. Preserve 400 behavior for:  
     
   * invalid `value`  
   * malformed payloads  
   * validation/type/range errors

   

5. Update or align tests so they explicitly enforce:  
     
   * missing/unknown media hash → 404  
   * invalid rating payload → 400  
   * known valid media hash \+ valid payload → success path unchanged

   

6. Do not alter unrelated route behavior.

Required output:

* First, provide a short audit summary of the exact files you plan to change and why  
* Then provide the full updated contents of each changed file  
* Then provide the exact targeted test commands to run for this phase  
* Then provide a short risk check explaining why the phase is isolated and low-risk  
* If you discover that the current implementation makes 404 impossible without broader architectural changes, stop and report that clearly instead of improvising

Acceptance target for this phase:

* Unknown `media_hash` is consistently 404  
* Invalid rating payload remains 400  
* Successful known-hash rating flows remain unchanged  
* No DB schema, Docker, proxy, or unrelated route changes are introduced

