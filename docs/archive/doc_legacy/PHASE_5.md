Project: `local-video-server`

Current state:

* Stabilization/cleanup Phases 0-3 are complete  
* Documentation reconciliation is complete  
* Canonical implementation reference is now `docs/SOURCE_OF_TRUTH.md`  
* Current safe regression baseline is:

python \-m compileall \-q main.py cache\_manager.py config.py database\_migration.py file\_watcher.py thumbnail\_manager.py backend tests

python \-m pytest \-q tests/test\_ratings\_api\_contract\_phase2.py tests/test\_admin\_performance\_routes.py tests/test\_basic.py tests/test\_routes.py tests/test\_rate\_limiting.py tests/test\_cors\_support.py

Objective for this prompt: Implement tag merge hardening so `/tags` and related tag-read paths merge sidecar tags plus DB tags, and no existing tags disappear from the read experience.

Behavior to lock in:

* Read path for tags \= union of sidecar tags \+ DB tags  
* Merge must be additive and non-destructive  
* If a tag exists in either source, it should appear in the effective tag view  
* Do not silently drop tags because one source is missing or stale

Preferred write rule unless code reality makes this unsafe:

* Writes/edits from the app should continue to persist to the DB path only  
* Sidecar tags should be treated as a read-source, not overwritten in this phase

Hard constraints:

* Do not break anything currently working  
* Do not change Docker topology, ports, proxy behavior, or runtime entrypoints  
* Do not change ratings API, admin metrics contracts, DB schema, or unrelated route behavior  
* Do not remove JSON fallback behavior  
* Keep edits minimal and reversible  
* Preserve current behavior for non-tag routes  
* If a schema change seems necessary, stop and report before making it

Tasks:

1. Audit current tag read/write flow across the relevant modules and routes, including:  
     
   * `/tags`  
   * any tag listing/filter routes  
   * cache layer behavior  
   * DB tag retrieval  
   * sidecar tag ingestion/read path

   

2. Identify where tags are currently being sourced from and where one source may overwrite or hide the other.  
     
3. Implement the narrowest safe change so effective read behavior is merged/union-based.  
     
4. Normalize merge behavior:  
     
   * deduplicate tags case-safely according to current project conventions  
   * preserve stable ordering if the project already has an ordering convention

   

5. Preserve write semantics unless a clearly safer alternative is required.  
     
6. Add or update targeted tests that explicitly verify:  
     
   * DB-only tags appear  
   * sidecar-only tags appear  
   * overlapping tags are deduplicated  
   * merged tags are visible in `/tags` effective output

   

7. Do not refactor unrelated systems in this phase.

Required output:

* First, provide a short audit summary of the exact files you plan to change and why  
* Then provide the full updated contents of each changed file  
* Then provide the exact targeted test commands to run for this phase  
* Then provide a short risk check explaining why the phase is isolated and low-risk  
* If you discover ambiguity about sidecar format, precedence, or current write rules that would make this unsafe, stop and report that clearly instead of improvising

Acceptance target for this phase:

* Effective tag reads are merged from sidecar \+ DB  
* No tags disappear from the read path merely because one source is absent  
* Non-tag routes and existing runtime behavior remain unchanged  
* No Docker/proxy/entrypoint/schema drift is introduced

