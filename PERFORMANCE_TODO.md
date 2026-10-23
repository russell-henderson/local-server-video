# Local Video Server — Performance Optimization TODO

**Status:** In progress; source inspection, baseline completed, and Sprint B optimization planned  
**Priority:** Performance stabilization before Windows desktop launcher implementation  
**Updated:** 2026-10-23  
**Scope:** Flask application, video playback, SQLite/metadata, galleries, previews, background work, Docker and future desktop packaging

> **Evidence rule:** Existing project documents describe several optimizations as implemented, but the current source and runtime have not been inspected. Every item marked **VERIFY** must be checked before anyone writes replacement code. Historical performance estimates are not current benchmarks.

> **Audit Status:** Sprint A (read-only inspection) completed 2026-10-23. Baseline established and optimization opportunities identified. See docs/PERFORMANCE_BASELINE.md and docs/PERFORMANCE_AUDIT_FINDINGS.md.

## 0. Operating rules and non-negotiables

- [x] **P0 · VERIFY** Inspect the current source tree, running configuration, routes, schema, migrations, cache, FFmpeg jobs, static assets, and test suite. Record file paths and code references in the audit notes.
- [x] **P0 · MEASURE** Capture baseline metrics before optimization. Do not claim a speedup without before/after measurements on the same hardware, dataset, browser, and Docker configuration.
- [x] **P0 · PRESERVE** Keep tags (including sidecar/DB reconciliation), favorites, view counts, video ratings, independent playlist-level ratings, playlist editing, gallery groups, thumbnails, previews, and video seeking intact.
- [x] **P0 · SAFETY** Back up SQLite and any active JSON metadata before writes, migrations, cleanup, or maintenance. No destructive cleanup by default.
- [x] **P0 · COMPATIBILITY** Keep Docker/LAN mode operational and avoid assumptions that require Docker in the future desktop launcher.
- [x] **P0 · REGRESSION** Run automated checks and a manual playback/metadata smoke test after each change; revert changes that break data integrity or core UX.
- [x] **P0 · SCOPE** Prefer small reversible improvements. No Flask-to-React rewrite, database replacement, media-wide transcode, or blanket dependency upgrade without evidence.

## 1. Baseline: identify where the time goes

**Why first:** Page load, first frame, seek latency, and metadata writes have different causes. Optimize the measured bottleneck, not the most fashionable technology.

- [x] **P0 · MEASURE** Record library size: video/image count, total media bytes, common codecs/containers, thumbnail count, preview count, SQLite size, and storage device types. Exclude sensitive media filenames from published reports.
- [x] **P0 · MEASURE** Repair the single missing thumbnail using the existing thumbnail-generation mechanism, after confirming the source video and expected thumbnail mapping. Do not create a new warming subsystem.
- [x] **P0 · MEASURE** Time cold vs warm home/gallery load: server response, HTML parse, first visible thumbnails, and full gallery readiness.
- [x] **P0 · MEASURE** Time watch-page navigation, click-to-first-frame, rebuffer events, and seeks near beginning/middle/end for representative MP4, MKV, and large files.
- [ ] **P0 · MEASURE** Compare localhost vs LAN playback, where relevant, to distinguish disk/codec problems from network bottlenecks.
- [ ] **P0 · MEASURE** Profile representative routes (home, watch, tags, favorites, playlist, gallery, search) at p50/p95 latency, DB query count/time, disk I/O, and response size.
- [ ] **P0 · MEASURE** Record CPU, memory, FFmpeg processes, disk queue/activity, and concurrent thumbnail/preview work while browsing and playing.
- [x] **P0 · MEASURE** Inspect browser DevTools Network/Performance for duplicate requests, oversized images, JS blocking, cache misses, and unnecessary video preloads.
- [x] **P0 · MEASURE** Run a controlled repeatable workload (cold cache and warm cache) with a disposable test database and media fixtures.
- [x] **P0 · DOCUMENT** Store methodology and results in `docs/PERFORMANCE_BASELINE.md`, with hardware, software versions, sample size, raw timings, and known limitations.

**Exit gate:** At least three ranked, evidence-backed bottlenecks, each with a baseline metric and owner.

## 2. Video playback: fastest path to first frame and smooth seeking

- [x] **P0 · VERIFY** Inspect Flask streaming response: HTTP `Range` handling, `206 Partial Content`, `Content-Range`, `Accept-Ranges`, `Content-Length`, MIME type, `HEAD`, and invalid range behavior.
- [x] **P0 · TEST** Confirm browser seek and resume work without downloading the entire file; test large files and multiple simultaneous streams.
- [ ] **P0 · VERIFY** Determine whether Python is copying media chunks unnecessarily. Compare current implementation against a production-grade range-serving path; use nginx/sendfile/X-Accel-Redirect only if compatible with deployment and security model.
- [ ] **P1 · EXPERIMENT** Compare chunk size, buffering, and streaming worker configuration under identical conditions; avoid one-size-fits-all buffer changes.
- [ ] **P1 · EXPERIMENT** Identify MP4 files with `moov` atom at end. Trial lossless fast-start remux on a **copy** of a representative file; preserve original and measure startup difference. Do not remux all media automatically.
- [ ] **P1 · VERIFY** Detect codec/container compatibility in actual target clients (desktop, mobile, VR). Separate unsupported decode paths from server throughput issues.
- [ ] **P1 · EXPERIMENT** Offer opt-in compatible playback versions or on-demand transcoding for unsupported media only. Benchmark startup delay, disk usage, CPU, and visual quality.
- [ ] **P2 · EVALUATE** HLS/DASH/adaptive bitrate only if LAN/mobile/VR measurements justify it. Review the existing adaptive-streaming implementation first; multiple renditions and segment creation carry storage/CPU costs.
- [ ] **P1 · TEST** Ensure thumbnails/previews/background scans cannot starve active playback of CPU or disk bandwidth.
- [ ] **P1 · UX** Display a meaningful loading/buffering state and actionable unsupported-format errors; avoid hiding slow startup behind indefinite spinners.

**Exit gate:** Playback range correctness preserved; first-frame and seek measurements improve on tested media without increasing failures or rebuffering.

## 3. Gallery, thumbnails, previews, and frontend rendering

- [ ] **P0 · VERIFY** Determine whether gallery pages scan media directories, rebuild metadata, or generate thumbnails during requests.
- [ ] **P0 · VERIFY** Audit current lazy-loading, thumbnail dimensions, responsive `srcset`, browser cache headers, and image formats before changing them.
- [ ] **P1 · IMPLEMENT IF NEEDED** Render initial visible items first; lazy-load offscreen cards/images and paginate or virtualize large galleries while retaining sorting, filtering, selection, and navigation.
- [ ] **P1 · IMPLEMENT IF NEEDED** Use appropriately sized thumbnails instead of original-resolution images; preserve aspect ratio and image quality.
- [ ] **P1 · VERIFY** Ensure thumbnail/preview generation is asynchronous, bounded, deduplicated per asset, and does not block HTTP responses.
- [ ] **P1 · VERIFY** Confirm preview concurrency caps and cleanup. Existing preview documentation describes a max of two concurrent previews, device-specific behavior, and fallback to static thumbnails; check the live code.
- [ ] **P1 · IMPLEMENT IF NEEDED** Delay hover preview startup, stop previews on leave/navigation, and cancel stale requests. Avoid aggressive media preloading on initial gallery load.
- [ ] **P1 · IMPLEMENT IF NEEDED** Use `loading=lazy`, explicit image dimensions, and deferred noncritical JS/CSS where appropriate; test layout shift and mobile behavior.
- [ ] **P1 · EXPERIMENT** Evaluate WebP/AVIF thumbnails versus JPEG based on decode time, size, browser support, and generation overhead. Do not change formats solely for novelty.
- [ ] **P2 · EVALUATE** Precompute a bounded first-screen thumbnail set after library changes, not on every visit.
- [ ] **P1 · TEST** Confirm gallery-group covers, lightbox, favorites, video stars, and playlist controls continue to update correctly.

**Exit gate:** Faster first meaningful gallery render and lower network payload, with no missing cards, broken preview interactions, or layout regressions.

## 4. SQLite, metadata, and query optimization

- [ ] **P0 · VERIFY** Identify the active metadata source of truth for each feature: SQLite tables, JSON, sidecars, or a merged view. Map read/write ownership and synchronization.
- [ ] **P0 · VERIFY** Inventory database schema, indexes, foreign keys, migrations, triggers, connection lifetimes, busy timeouts, transaction scopes, and journal mode.
- [ ] **P0 · MEASURE** Use `EXPLAIN QUERY PLAN` and query timing for the slowest real gallery, tag, favorite, playlist, and search operations.
- [ ] **P1 · IMPLEMENT IF NEEDED** Add only workload-justified indexes, including join/filter/sort paths. Check write amplification and index size before and after.
- [ ] **P1 · IMPLEMENT IF NEEDED** Eliminate N+1 queries with batch reads, joins, or precomputed counts, especially playlist video counts, ratings, and gallery-group summaries.
- [ ] **P1 · VERIFY** Check SQLite WAL suitability and `busy_timeout` for actual concurrency. Enable only after confirming filesystem and backup implications; do not use WAL across unsupported shared/network filesystems.
- [ ] **P1 · VERIFY** Keep transactions short and parameterized; avoid per-item commits or connection churn during bulk operations.
- [ ] **P1 · VERIFY** Confirm independent video rating and playlist rating tables/columns/updates cannot overwrite one another; regression-test both flows.
- [ ] **P1 · VERIFY** Confirm new favorites, tags, ratings, and views persist after restart and remain consistent across JSON/sidecar/DB read paths.
- [ ] **P1 · EVALUATE** Consider SQLite FTS5 for substantial free-text search workloads; benchmark and document index maintenance before adopting.
- [ ] **P2 · MAINTENANCE** Add non-destructive integrity checks and documented backup procedure. Use `PRAGMA optimize`/`ANALYZE` only as justified; `VACUUM` only after backup, with space/time estimates and an explicit maintenance window.
- [ ] **P1 · TEST** Exercise concurrent metadata reads and writes; verify no `database is locked` errors or lost updates.

**Exit gate:** Verified query plans and lower p95 metadata latency; no lost or cross-contaminated metadata; integrity checks pass.

## 5. Library indexing, filesystem scans, and caching

- [ ] **P0 · VERIFY** Trace all calls that enumerate media directories or call `stat()` on every file during page requests.
- [ ] **P1 · IMPLEMENT IF NEEDED** Maintain an indexed media catalog updated incrementally, with a reliable manual/full rescan fallback and clear detection of deleted/moved media.
- [ ] **P1 · EVALUATE** Use filesystem change notifications where reliable; reconcile with periodic scans because file watchers can miss events and mounted drives behave differently.
- [x] **P0 · VERIFY** Inspect existing `cache_manager.py`, TTLs, invalidation hooks, memory footprint, and multi-process behavior. Earlier docs describe five-minute in-memory caching and write-through JSON persistence.
- [ ] **P1 · IMPLEMENT IF NEEDED** Cache expensive derived metadata and stable lists with event-driven invalidation after add/remove/rate/tag/favorite/playlist edits. Do not cache mutable results indefinitely.
- [ ] **P1 · IMPLEMENT IF NEEDED** Avoid repeated sort/filter of the entire catalog for common requests; compare DB-side ordering and cached summaries.
- [ ] **P1 · VERIFY** Set cache headers by asset type: fingerprinted static assets and immutable generated thumbnails may cache longer; mutable HTML/API responses need appropriate freshness semantics.
- [x] **P1 · TEST** Confirm edits appear promptly across gallery, watch, playlist, and favorites pages without manual cache clearing.
- [ ] **P2 · EVALUATE** Warm only high-value caches after startup, without blocking the UI or causing disk storms.

**Exit gate:** No unnecessary full-library scan on normal page requests; cache hit/miss behavior is observable and updates remain correct.

## 6. Background jobs and FFmpeg resource control

- [ ] **P0 · VERIFY** Inventory thumbnail, preview, probe, scan, transcode, and cleanup jobs, including when they start and how they terminate.
- [ ] **P1 · IMPLEMENT IF NEEDED** Centralize job scheduling with bounded worker count, per-asset deduplication, retries, timeouts, and persistent status where appropriate.
- [ ] **P1 · IMPLEMENT IF NEEDED** Prioritize foreground playback and user-requested thumbnails over bulk library maintenance.
- [ ] **P1 · IMPLEMENT IF NEEDED** Debounce rapid file-change events; avoid multiple FFmpeg invocations for the same video.
- [ ] **P1 · VERIFY** Make generated assets atomic: write to temporary path, validate, then replace; handle interruption without leaving corrupt visible files.
- [ ] **P1 · VERIFY** Reuse cached `ffprobe` metadata rather than probing on every request.
- [ ] **P2 · EVALUATE** Hardware acceleration only for workloads where it helps and supported codecs/drivers are known. Measure overhead and provide software fallback.
- [ ] **P1 · TEST** Validate process cleanup on app shutdown, Docker restart, and future desktop launcher termination.

**Exit gate:** Bounded CPU/disk load under batch work; no duplicate jobs; playback responsiveness preserved.

## 7. Search, sorting, navigation, and interaction workflow

- [ ] **P1 · MEASURE** Time search/filter/sort with typical and worst-case library sizes; identify client-side vs server-side work.
- [ ] **P1 · IMPLEMENT IF NEEDED** Debounce search input, cancel stale requests, and preserve keyboard navigation and focus.
- [ ] **P1 · IMPLEMENT IF NEEDED** Persist user-selected sort, filter, page size, and view mode without expensive reloads.
- [ ] **P1 · IMPLEMENT IF NEEDED** Batch metadata fetches for visible cards rather than issuing one request per card.
- [ ] **P1 · VERIFY** Ensure playlist editing and rating updates modify only the affected UI/records rather than reloading the entire library unnecessarily.
- [ ] **P2 · EVALUATE** Add an optional quick-actions panel (rescan selected folder, rebuild missing previews, inspect cache, view queued jobs), using existing admin controls where possible.
- [ ] **P1 · UX** Show progress and cancellation for long-running scans; keep browsing usable while work proceeds.

**Exit gate:** Responsive common workflows, correct state after navigation, and fewer redundant requests.

## 8. Flask runtime, Docker, and Windows desktop readiness

- [ ] **P0 · VERIFY** Determine the actual production WSGI/server setup, worker/thread model, nginx proxy role, and current Docker volumes.
- [ ] **P1 · EXPERIMENT** Tune worker/thread count only after confirming SQLite connection safety and streaming behavior; more workers are not automatically faster.
- [ ] **P1 · VERIFY** Disable Flask debug/reloader in production; prevent duplicate initialization and duplicate background jobs.
- [ ] **P1 · VERIFY** Ensure static/media paths resolve from configuration rather than hardcoded Docker paths; support Windows drive paths safely.
- [ ] **P1 · VERIFY** Ensure writable metadata, logs, thumbnails, and cache are outside read-only packaged application resources.
- [ ] **P1 · TEST** Compare Docker and direct Windows localhost performance to isolate proxy, volume mount, antivirus, and filesystem overhead.
- [ ] **P2 · EVALUATE** Test whether media on a local NTFS drive vs a Docker bind mount materially changes startup and seeking. Do not migrate media without measured benefit and a rollback plan.
- [ ] **P1 · SECURITY** In future desktop mode, bind Flask to `127.0.0.1`, choose a managed port, and prevent unintended LAN exposure; retain intentional LAN access in server mode.
- [ ] **P1 · COMPATIBILITY** Preserve the admin dashboard and nginx-proxy service where used; do not assume desktop mode needs either.

**Exit gate:** No Docker-specific assumptions in performance fixes; launcher architecture remains feasible.

## 9. Observability, automated regression, and release gates

- [ ] **P0 · VERIFY** Inspect existing `performance_monitor.py` and dashboard metrics before adding another telemetry system.
- [ ] **P1 · IMPLEMENT IF NEEDED** Expose route latency, DB query count/time, cache hit rate, active streams, active FFmpeg jobs, queue depth, and playback errors with low overhead.
- [ ] **P1 · IMPLEMENT IF NEEDED** Add structured timing logs with request IDs and a simple local diagnostic export that excludes private media names/paths by default.
- [ ] **P1 · TEST** Add HTTP range tests: `200`, `206`, `416`, byte correctness, `HEAD`, end-of-file, and simultaneous streams.
- [ ] **P1 · TEST** Add persistence tests for tags, favorites, view counts, individual video ratings, playlist-level ratings, and gallery groups.
- [ ] **P1 · TEST** Add thumbnail generation, deduplication, cache invalidation, and job cancellation tests.
- [ ] **P1 · TEST** Run representative smoke tests on desktop browser, mobile browser, and VR where available.
- [ ] **P0 · REPORT** Publish before/after results, regressions, resource cost, and rollback instructions for each completed optimization.

**Exit gate:** Changes are demonstrably faster, observable, reversible, and covered by relevant tests.

## 10. Candidate experiments and decision matrix

| Candidate | Expected benefit | Cost/risk | Priority | Decision rule |
|---|---|---|---|---|
| Correct HTTP range streaming | Faster seeks, avoids whole-file transfers | Medium; playback regression risk | P0 | Fix only if headers/byte tests reveal a defect |
| Remove per-request directory scans | Faster gallery and route responses | Medium; invalidation complexity | P1 | Adopt if scans dominate measured latency |
| Right-size and lazy-load thumbnails | Faster first paint, less transfer | Low–medium | P1 | Adopt if image/network/render cost is material |
| Deduplicated background previews | Fewer stalls and FFmpeg spikes | Medium | P1 | Adopt if request path blocks or jobs overlap |
| Targeted SQLite indexes and batched queries | Faster tags/search/playlist operations | Low–medium; write cost | P1 | Require slow query evidence and query-plan improvement |
| SQLite WAL / transaction tuning | Better concurrent read/write behavior | Medium; filesystem caveats | P1 | Require lock/contention evidence and safe storage |
| Cache invalidation improvements | Faster repeated navigation | Medium; stale-data risk | P1 | Require repeat-work evidence and correctness tests |
| MP4 fast-start remux (opt-in) | Faster startup for some MP4s | Medium; extra I/O and backups | P1 | Pilot on copies; keep originals |
| Direct Windows vs Docker performance comparison | Identifies virtualization/mount overhead | Low; measurement only | P1 | Inform launcher decisions; no migration by assumption |
| HLS/DASH adaptive renditions | Better variable-network playback | High; CPU/storage/complexity | P2 | Only if measured LAN/mobile/VR problems justify it |
| FTS5 search index | Faster large-library text search | Medium; index maintenance | P2 | Only if existing search becomes a proven bottleneck |
| Hardware video acceleration | Faster selected transcodes | Medium–high; driver variance | P2 | Require reproducible supported workload improvement |

## 11. Suggested execution order: four short optimization sprints

### Sprint A — Audit and measurement (no behavior changes)

- [ ] Capture source inventory, route map, active data sources, playback path, Docker topology, and baseline metrics.
- [ ] Rank top three bottlenecks by user-visible delay and implementation risk.
- [ ] Produce `docs/PERFORMANCE_BASELINE.md` and a prioritized evidence log.

### Sprint B — Safe perceived-speed wins

- [ ] Address confirmed gallery thumbnail sizing/lazy-loading gaps.
- [ ] Remove confirmed blocking thumbnail/preview work from request path.
- [ ] Fix duplicate requests and avoid unnecessary full-page refreshes.
- [ ] Verify no UI or metadata regression; publish measured delta.

### Sprint C — Metadata and media pipeline

- [ ] Optimize confirmed slow SQLite queries, transactions, and catalog scans.
- [ ] Correct any HTTP range/seek issues and trial fast-start remux on copies if indicated.
- [ ] Test concurrent playback and metadata writes; publish measured delta.

### Sprint D — Stability and launcher handoff

- [ ] Bound background FFmpeg work and validate cancellation/cleanup.
- [ ] Run full regression and cross-device smoke tests.
- [ ] Record performance acceptance results and remaining tradeoffs.
- [ ] Hand verified startup, storage, streaming, and resource requirements to `DESKTOP_LAUNCHER_AUDIT_AND_MIGRATION_PLAN.md`.

## 12. Performance scorecard template (fill with actual measurements)

| Metric | Baseline | After | Target/acceptance |
|---|---|---|---|
| Home/gallery p95 server response | TBD | TBD | Lower without regression |
| First visible gallery thumbnails | TBD | TBD | Lower |
| Watch click-to-first-frame p50/p95 | TBD | TBD | Lower on same sample files |
| Seek-to-play p50/p95 | TBD | TBD | Lower; no range failures |
| Metadata route p95 | TBD | TBD | Lower; correct writes |
| Search/filter p95 | TBD | TBD | Lower; accurate results |
| Full scans per normal page load | TBD | TBD | Zero if safely achievable |
| Cache hit rate and stale-read incidents | TBD | TBD | Better hit rate; zero stale-write defects |
| Active FFmpeg jobs during playback | TBD | TBD | Bounded; no playback starvation |
| Peak memory/CPU during browse/playback | TBD | TBD | No unacceptable increase |
| Playback failures/rebuffers | TBD | TBD | No increase |
| Data integrity and feature regression | TBD | TBD | All tests pass |

**Targets must be set after baseline.** Do not copy older documentation's percentage-improvement claims into release acceptance criteria without reproduction.

## 13. Existing project references and interpretation

- `PERFORMANCE_ANALYSIS_SUMMARY.md` and `PERFORMANCE_OPTIMIZATION_GUIDE.md` identify historical JSON I/O, per-request directory scans, synchronous thumbnails, and caching gaps; they also describe `cache_manager.py`, `main_optimized.py`, `database_migration.py`, and `performance_monitor.py` as delivered. **Current activation and effectiveness are unverified.** Their projected speedups are not measured current results.
- `ADAPTIVE_STREAMING_SYSTEM.md` describes an adaptive streaming controller, network monitor, quality selection, and buffer management. **Current integration and actual rendition support must be verified** before adding a second streaming system.
- `VIDEO_PREVIEW_IMPROVEMENTS.md` describes device-specific preview behavior, a two-preview concurrency cap, timeouts, and static-thumbnail fallbacks. **Confirm present implementation before revising it.**
- `DESKTOP_LAUNCHER_AUDIT_AND_MIGRATION_PLAN.md` establishes the Windows launcher direction and requirement to preserve Docker/LAN mode and metadata semantics.
- Project handoff decisions preserve **individual video ratings** and a **separate playlist-level rating**; playlist editing is already present and is not a missing feature.

## 14. Explicitly deferred until evidence justifies them

- [ ] Replace Flask, SQLite, or the current UI framework.
- [ ] Introduce Redis, PostgreSQL, Elasticsearch, or a distributed queue for a single-machine library.
- [ ] Transcode the entire library or pre-generate every quality rendition.
- [ ] Rebuild working playlist editing, gallery grouping, or existing preview systems.
- [ ] Enable aggressive `VACUUM`, automatic deletion, or metadata pruning on production data.
- [ ] Merge desktop and Docker metadata writes into a shared SQLite file without a concurrency/ownership design.

---

**Immediate next action:** Complete **Sprint A** as a read-only source and runtime audit. Select the first implementation task only after identifying the top measured bottleneck. This TODO is an optimization decision backlog, not a claim that every proposed feature is missing.
