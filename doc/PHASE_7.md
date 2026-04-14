Project: `local-video-server`

Current verified state:

* Cleanup/stabilization Phases 0-3 completed  
    
* Documentation reconciliation completed  
    
* Canonical implementation reference is `docs/SOURCE_OF_TRUTH.md`  
    
* Tag merge hardening completed  
    
* Tag reads now merge sidecar \+ DB  
    
* Tag writes remain DB-path only  
    
* Latest validations passed:  
    
  1. `python -m pytest -q tests/test_tag_merge_phase5.py`  
  2. `python -m pytest -q tests/test_ratings_api_contract_phase2.py tests/test_admin_performance_routes.py tests/test_basic.py tests/test_routes.py tests/test_rate_limiting.py tests/test_cors_support.py`


* Results:  
    
  * `tests/test_tag_merge_phase5.py` passed (`4 passed`)  
  * targeted non-tag regression slice passed (`40 passed`)


* Only observed warning:  
    
  * pytest cache path creation warning under `.pytest_cache` (non-functional)

Objective for this prompt: Perform a full-suite stabilization audit and identify the smallest safe next patch set to increase confidence beyond the current targeted regression baseline, without breaking currently working runtime behavior.

Hard constraints:

* Audit first  
    
* Do not change runtime behavior in this pass unless a fix is clearly low-risk, tightly scoped, and required to resolve a real test/code mismatch  
    
* Do not change Docker topology, ports, proxy behavior, entrypoints, DB schema, ratings contract, admin contract, or tag merge behavior  
    
* Keep changes minimal and reversible  
    
* Clearly distinguish:  
    
  * stale/bad tests  
  * flaky/environment-sensitive tests  
  * real runtime defects  
  * tooling/setup issues  
  * optional dependency issues  
  * browser/Playwright setup issues

Tasks:

1. Run or audit the broader/full pytest suite.  
     
2. Classify all remaining failures, skips, warnings, and unstable areas by category and risk.  
     
3. Identify which failures are:  
     
   * stale tests that should be rewritten/aligned  
   * environment/path/temp/cache issues  
   * genuine product defects  
   * low-value noise

   

4. Recommend the smallest safe next patch set, in phased order.  
     
5. Only implement fixes in this prompt if they are obviously low-risk and behavior-preserving. Otherwise stop at audit \+ plan.  
     
6. Include a recommendation for the `.pytest_cache` warning:  
     
   * ignore  
   * configure  
   * clean up

Required output:

* First, provide a full-suite audit summary  
* Then classify each failure/unstable area by category and risk  
* Then propose the next smallest safe patch set  
* Only if appropriate, provide the full updated contents of any changed files  
* Then provide the exact commands for the recommended next validation run  
* Then provide a short risk check

Acceptance target:

* Clear map from current targeted confidence to broader suite confidence  
* No unintended runtime/API/schema/Docker/proxy behavior changes  
* One sharply scoped next patch set identified

