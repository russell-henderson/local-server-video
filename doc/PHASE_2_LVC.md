Project: `local-video-server`

Phase 0 is complete.

Verified result:

* Targeted pytest command now runs cleanly in this environment  
* 28 tests passed  
* No fixture-related collection failures remain in the targeted suites  
* Only test harness/config/tooling files were changed  
* No production route handlers, DB schema, Docker compose, ports, proxy config, or runtime entrypoints were modified  
* API semantics and metadata persistence behavior were not changed

Objective for this prompt:  
Execute PHASE 1 ONLY: dependency/import hardening, specifically making performance monitoring resilient when `psutil` is absent, without changing product behavior when `psutil` is installed.

Hard constraints:

* Do not break anything currently working  
* Do not change Docker topology, ports, proxy behavior, or runtime entrypoints  
* Do not modify ratings API contract, route semantics, DB schema, or metadata persistence in this phase  
* Do not mix Phase 2 contract alignment or Phase 3 cleanup into this patch  
* Keep edits minimal and reversible  
* Preserve current behavior when `psutil` is present  
* When `psutil` is missing, the app/test collection must degrade gracefully rather than fail at import time

Tasks:

1. Audit the current `performance_monitor.py` import path and any upstream imports that make `psutil` a hard dependency at module import time.  
2. Implement a minimal graceful fallback so missing `psutil` does not break:  
   * test collection  
   * app import  
   * admin/performance route import  
3. Fallback mode should:  
   * preserve existing APIs/interfaces as much as possible  
   * return limited or no-op system metrics where required  
   * avoid raising import-time exceptions  
4. Inspect tests touching performance/admin behavior and update them only if necessary so they:  
   * pass in fallback mode, or  
   * skip explicitly with a clear reason when the optional dependency is absent  
5. Do not change runtime behavior beyond optional dependency hardening.

Required output:

* First, provide a short audit summary of the exact files you plan to change and why  
* Then provide the full updated contents of each changed file  
* Then provide the exact test commands to run for this phase  
* Then provide a short risk check explaining why the phase is non-breaking  
* If you discover that the fallback would require interface-breaking changes, stop and report that instead of improvising

Acceptance target for this phase:

* Test collection does not fail when `psutil` is absent  
* App import does not fail when `psutil` is absent  
* Existing behavior is preserved when `psutil` is installed  
* No API, DB, Docker, proxy, or route contract changes are introduced

