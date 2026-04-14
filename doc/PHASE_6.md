Project: `local-video-server`

Current state:

* Cleanup/stabilization Phases 0-3 completed  
    
* Documentation reconciliation completed  
    
* Canonical implementation reference is `docs/SOURCE_OF_TRUTH.md`  
    
* Tag merge hardening completed  
    
* Tag reads now merge sidecar \+ DB  
    
* Tag writes remain DB-path only  
    
* Latest validations passed:  
    
  * `python -m pytest -q tests/test_tag_merge_phase5.py`  
  * `python -m pytest -q tests/test_ratings_api_contract_phase2.py tests/test_admin_performance_routes.py tests/test_basic.py tests/test_routes.py tests/test_rate_limiting.py tests/test_cors_support.py`


* Only observed warning was non-functional pytest cache path creation under `.pytest_cache`

Objective for this prompt: Perform a full-suite stabilization audit and produce the smallest safe next plan to raise confidence beyond the current targeted regression slice, without breaking currently working runtime behavior.

Hard constraints:

* Do not change runtime behavior in this pass unless explicitly required to fix a real test/code mismatch  
    
* Audit first, patch second only if the fix is low-risk and tightly scoped  
    
* Do not change Docker topology, ports, proxy behavior, entrypoints, DB schema, ratings contract, admin contract, or tag merge behavior in this pass  
    
* Keep changes minimal and reversible  
    
* Distinguish clearly between:  
    
  * broken tests caused by stale assumptions  
  * flaky/environment-sensitive tests  
  * real product defects  
  * low-value tests that should be rewritten, skipped, or removed

Tasks:

1. Run or audit the broader/full pytest suite and classify remaining failures, skips, warnings, and unstable areas.  
     
2. Group findings into categories:  
     
   * stale/bad tests  
   * environment/path/temp issues  
   * optional dependency issues  
   * real runtime defects  
   * Playwright/browser test setup issues  
   * documentation/tooling gaps

   

3. Identify the smallest safe subset of remaining failures that should be fixed next.  
     
4. Recommend a phased order for full-suite improvement, prioritizing low-risk/high-signal work.  
     
5. Only implement fixes in this prompt if they are clearly low-risk, tightly scoped, and do not alter product behavior. Otherwise stop at audit \+ plan.  
     
6. Include special attention to the pytest cache warning and recommend whether it should be ignored, configured, or cleaned up.

Required output:

* First, provide an audit summary of full-suite status  
* Then classify each failure/unstable area by category and risk  
* Then propose the next smallest safe patch set  
* Only if appropriate, provide the full updated contents of any changed files  
* Then provide the exact commands for the recommended next validation run  
* Then provide a short risk check

Acceptance target for this phase:

* Clear map of what remains between current targeted confidence and broader suite confidence  
* No unintended runtime/API/schema/Docker/proxy behavior changes  
* One sharply scoped next patch set identified

