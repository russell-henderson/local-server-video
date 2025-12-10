# Performance Overview

Purpose: provide a single, stable source of truth for how Local Video Server performs, what the main bottlenecks are, what improvements are planned, and how we measure success.

This file replaces scattered notes in:

- `PERFORMANCE_ANALYSIS_SUMMARY.md`
- `PERFORMANCE_OPTIMIZATION_GUIDE.md`
- `OPTIMIZATION_SUMMARY.md`
- Copies under `docs/deferred/`

Those files are now treated as historical sources only.

---

## 1. Current state snapshot

### 1.1 Scale

- Approximate videos in collection: 333
- JSON metadata files:
  - ratings, views, tags, favorites
  - up to about 21 KB per file
- Flask application with multiple routes:
  - gallery home
  - watch page
  - favorites
  - tag filtered views
  - admin and utility routes

### 1.2 Key bottlenecks observed

These are distilled from the earlier analysis and optimization guide.

1. File I/O per request
   - 4 JSON files loaded on many requests:
     - ratings
     - views
     - tags
     - favorites
   - Adds roughly 80 KB or more of disk I/O per page load.

2. Directory scanning
   - `get_video_list()` and similar helpers rescan the full video directory each time.
   - For a few hundred videos this is noticeable and grows with library size.

3. Thumbnail generation
   - Some code paths risk regenerating or rechecking thumbnails too often.
   - Slow or failing thumbnail generation creates a bad first impression.

4. Route complexity
   - Route functions mix:
     - data loading
     - filtering
     - view logic
   - This makes caching and reuse harder.

5. Lack of central caching
   - Without a cache layer:
     - repeated reads of JSON and directory listings
     - higher latency
     - wasted CPU and disk

6. Future database migration pressure
   - Long term plan is to migrate ratings, views, tags, and favorites to SQLite.
   - Until then, JSON based paths must be tightly optimized.

---

## 2. Target performance goals

These goals are based on the earlier analysis and expected improvement ranges.

### 2.1 Latency goals

For a typical local network setup:

- Home page:
  - Target p95 latency: 50 to 100 ms
- Watch page:
  - Target p95 latency: 30 to 75 ms
- API endpoints:
  - Target p95 latency: under 100 ms for common JSON APIs

### 2.2 Resource goals

- Disk I/O per request:
  - Reduce to about 1 to 5 KB for cached paths
  - Aim for about 95 percent reduction compared to naive JSON loading
- Memory usage:
  - Reduce high water marks by roughly 30 to 40 percent through simpler data paths and limited cache size
- Concurrency:
  - Support several times more concurrent users compared to the original naive implementation
- Cache efficiency:
  - Cache hit rate above 90 percent for common gallery and watch routes

These ranges reflect the earlier estimate of:

- 60 to 85 percent performance improvement
- 95 percent reduction in disk I/O
- About 5x improvement in concurrent user capacity

---

## 3. Optimization strategy

This section merges the prescriptions from the optimization guide into a single playbook.

### 3.1 Phase 1 – caching and JSON load reduction

Focus: high impact changes with low risk.

Core ideas:

- Introduce a central cache manager that:
  - keeps hot metadata in memory
  - avoids reading JSON files repeatedly
- Replace repeated `load_ratings`, `load_views`, `load_tags`, `load_favorites` calls with:
  - cached accessors
  - or a preloaded metadata structure at request start
- Add HTTP cache headers for stable resources where safe:
  - `Cache-Control: public, max-age=3600` for thumbnails and static assets

Checklist:

- [ ] Cache manager module in place and imported in main app
- [ ] All high traffic routes use cache helper functions rather than raw JSON loads
- [ ] Response cache headers set for thumbnails and other safe static resources

### 3.2 Phase 2 – directory scanning and thumbnails

Focus: reduce work done per request and stabilize the thumbnail pipeline.

Core ideas:

- Scan the video directory once per period rather than on each page render.
  - Maintain an in memory or on disk index of video files.
- Make thumbnail generation fully asynchronous:
  - use a small worker pool
  - do not block HTTP request paths on thumbnail work
- Add clear logging for thumbnail errors for admin dashboard use.

Checklist:

- [ ] Single source of truth for video list (no repeated directory scans in route handlers)
- [ ] Thumbnail generation runs in background workers
- [ ] Thumbnail error log is written in a structured and predictable format

### 3.3 Phase 3 – SQLite migration for hot data

Focus: move write heavy and query heavy data out of JSON.

Core ideas:

- Ratings, views, and favorites move into SQLite tables.
- JSON files become either:
  - a backup format
  - or are phased out entirely
- Indexes support fast lookup by filename and date.

Checklist:

- [ ] Schema defined for ratings, views, favorites, and tags
- [ ] Migration helpers in `database_migration.py` to populate initial tables from JSON
- [ ] Routes updated to use database helpers instead of JSON loads

### 3.4 Phase 4 – continuous monitoring and tuning

Focus: connect the work above to real measurements.

Core ideas:

- Wrap key routes with a performance monitor decorator.
- Record latency statistics in a small metrics store.
- Surface these numbers in the admin dashboard.

Checklist:

- [ ] Performance monitor decorator applied to high traffic routes
- [ ] Metrics persisted and visible through admin APIs
- [ ] Admin dashboard cards built for route performance and storage

---

## 4. Metrics and monitoring

Detailed monitoring behavior is defined in `PERFORMANCE_MONITORING.md`. This section summarizes how it connects to performance work.

### 4.1 Key metrics

- Route level:
  - count
  - p50, p95, p99 latency
  - error counts
- Cache:
  - hit rate by route or endpoint
  - size and eviction counts
- Thumbnails:
  - jobs succeeded
  - jobs failed
  - average generation time
- Storage:
  - video storage footprint
  - thumbnail cache size
  - database size

### 4.2 Data sources

- In memory metrics structures
- SQLite tables for longer term aggregates
- Log files such as `thumbnail_errors.log`

---

## 5. Implementation status

Use this section as a living tracker for performance work. Update it as features land.

### 5.1 High level status

- [ ] Phase 1 caching complete
- [ ] Phase 2 directory and thumbnail improvements complete
- [ ] Phase 3 SQLite migration complete
- [ ] Phase 4 monitoring and dashboard integration complete

### 5.2 Notes

- When a phase is complete, link to the relevant entries in `LATEST.md` and the release notes.
- If any optimization idea is dropped or changed, record the reasoning here so future work does not reintroduce the same experiments.

---

## 6. How to extend this file

When you discover new bottlenecks or ship new improvements:

1. Add a concise description under section 1.2 or 3.
2. If the change touches architecture or APIs, also update:
   - `ARCHITECTURE.md`
   - `API.md`
3. Add a short note to `LATEST.md` with:
   - what changed
   - why it was done
   - a reference back to this file

This keeps performance work discoverable and avoids new scattered performance notes in separate files.
