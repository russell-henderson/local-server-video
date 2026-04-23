Project: `local-video-server`

Current verified state:

* Cleanup/stabilization Phases 0-3 completed  
* Documentation reconciliation completed  
* Tag merge hardening completed  
* Phase 7 full-suite audit completed

Audit findings to treat as current:

* Full suite status:  
    
  * 99 collected  
  * 61 passed  
  * 21 failed  
  * 17 skipped  
  * 0 errors


* Failure concentration:  
    
  * `tests/test_rating_write_and_read.py` \-\> 14 failures  
  * `tests/test_api_hash_invariants.py` \-\> 5 failures  
  * `tests/test_rating_mapping.py` \-\> 2 failures


* Primary issue class:  
    
  * stale/drifted tests, not confirmed runtime defects


* Known drift patterns:  
    
  * legacy tests use filename where API now expects `media_hash`  
  * some DB assertions still query `ratings.value` instead of `ratings.rating`  
  * service tests call `RatingsService.set_rating` without creating a real backing file  
  * some legacy tests do not align with shared limiter reset behavior


* Playwright/browser tests are currently expected-skip unless browser deps are installed

Objective for this prompt: Patch only the stale legacy ratings tests so they align with the current implementation and increase full-suite confidence, without changing runtime code or product behavior.

Hard constraints:

* Test-only patch unless you discover a true runtime defect that cannot be avoided  
    
* Do not change runtime behavior, API semantics, Docker topology, proxy behavior, entrypoints, DB schema, ratings contract, admin contract, or tag merge behavior  
    
* Keep edits minimal and reversible  
    
* Preserve current contract:  
    
  * unknown/unresolved `media_hash` \=\> 404  
  * invalid payload \=\> 400  
  * valid known hash POST \=\> 201


* Preserve Playwright tests as optional/skip-by-default in this phase

Tasks:

1. Patch `tests/test_rating_write_and_read.py` to current behavior:  
     
   * resolve or create a real `media_hash` before API GET/POST calls  
   * align status expectations with 404-on-unknown-hash behavior  
   * update direct DB assertions from `ratings.value` to `ratings.rating` where appropriate  
   * align limiter-related assumptions with the shared fixture/reset pattern

   

2. Patch `tests/test_api_hash_invariants.py`:  
     
   * ensure temp or fixture-backed video files exist before calling `RatingsService.set_rating`  
   * align hash/path assumptions with current implementation

   

3. Patch `tests/test_rating_mapping.py`:  
     
   * ensure service-level assumptions match current filename/hash/file-existence rules

   

4. Do not modify unrelated tests in this phase.  
     
5. Do not touch runtime files unless you uncover a genuine runtime defect and can prove it.

Required output:

* First, provide a short audit summary of the exact test files you plan to change and why  
* Then provide the full updated contents of each changed test file  
* Then provide the exact targeted validation commands  
* Then provide a short risk check explaining why the patch is test-only and non-breaking  
* If any failure appears to be a real runtime bug rather than stale test drift, stop and report it clearly instead of improvising

Acceptance target:

* The three legacy ratings test files align with the current implementation  
* No runtime code changes are introduced  
* Targeted legacy-ratings validation passes  
* The current targeted regression slice still passes

## **Validation sequence after that**

Use exactly this order:

python \-m pytest \-q \--color=no tests/test\_rating\_write\_and\_read.py tests/test\_api\_hash\_invariants.py tests/test\_rating\_mapping.py python \-m pytest \-q \--color=no tests/test\_ratings\_api\_contract\_phase2.py tests/test\_admin\_performance\_routes.py tests/test\_basic.py tests/test\_routes.py tests/test\_rate\_limiting.py tests/test\_cors\_support.py tests/test\_tag\_merge\_phase5.py python \-m pytest \-q \--color=no \--junitxml=.tmp/phase7-next.xml  
