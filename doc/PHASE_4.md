Project: `local-video-server`

Phases 0-3 are complete.

Verified current status:

* Phase 0: test harness stabilization completed  
* Phase 1: `psutil` optional dependency hardening completed  
* Phase 2: ratings API contract alignment completed  
* Phase 3: deprecation cleanup and duplicate-definition removal completed  
* Validation after Phase 3: 40 passed  
* No new functional regressions observed  
* No API contract, DB schema, Docker/proxy/runtime entrypoint, or metadata persistence changes were introduced in these phases

Objective for this prompt:  
Perform a source-of-truth and documentation reconciliation pass so the repository documentation accurately reflects the current implementation, without changing runtime behavior.

Hard constraints:

* Do not change runtime code, Docker topology, ports, proxy behavior, entrypoints, DB schema, or metadata persistence in this pass  
* Documentation-only changes unless you discover a doc/code mismatch that is dangerous enough to require escalation  
* Do not invent features that are not implemented  
* Clearly separate:  
  * implemented now  
  * partially implemented / behind flags / optional  
  * planned but not yet implemented  
* Keep edits minimal, high-signal, and maintainable

Tasks:

1. Audit the current repository docs and identify which files are now stale, conflicting, or misleading relative to current code and the completed cleanup phases.  
2. Produce a source-of-truth map that answers:  
   * canonical runtime entrypoints  
   * actual Docker/container topology  
   * actual metadata authority and fallback behavior  
   * actual admin/performance surfaces  
   * actual ratings API contract  
   * current test command(s) that should be considered the safe regression baseline  
3. Update the docs so they reflect the current implementation accurately.  
4. Prefer updating or consolidating these kinds of files if present:  
   * `README.md`  
   * architecture / backend docs  
   * admin/performance docs  
   * developer test instructions  
5. Remove ambiguity around:  
   * SQLite-first vs JSON fallback  
   * current ratings API behavior  
   * optional `psutil` behavior  
   * what is truly production/current vs future/planned  
6. If multiple docs conflict, recommend one canonical source-of-truth file and align others to it.  
7. Do not modify runtime behavior in this pass.

Required output:

* First, provide a short audit summary listing:  
  * docs that are accurate  
  * docs that are stale  
  * docs that conflict  
  * docs that should become canonical  
* Then provide the full updated contents of each changed documentation file  
* Then provide a concise “source-of-truth summary” suitable for pasting into a fresh project PRD  
* Then provide a short risk check explaining why this pass is non-breaking  
* If you find a dangerous code/doc mismatch that cannot be resolved documentation-only, stop and report it clearly instead of improvising

Acceptance target for this phase:

* Repository docs accurately describe the current implementation  
* One clear canonical source-of-truth path is established  
* No runtime/API/DB/Docker/proxy behavior changes are introduced

