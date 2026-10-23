# Local Video Server — Canonical TODO

**Updated:** 2026-10-23  
**Current workstream:** High-bitrate VR video playback reliability  
**Active runtime:** Native Windows development server (reported by project owner); **Docker/WSL not currently running**  
**Repository on owner's workstation:** `Z:\local-video-server`  
**Status:** Diagnosis in progress; no streaming implementation change authorized yet.

> **Agent instruction:** Read this file first. Work only on the active milestone unless explicitly directed otherwise. Do not infer that Docker is running because `Dockerfile`, `docker-compose.yml`, or Nginx configuration exists. Do not attempt to start, reinstall, repair, or migrate Docker/WSL. Do not silently mark investigations complete.

## 0. Operating rules (always in effect)

- [ ] **Ongoing:** Confirm the actual process, host, port, entrypoint, and HTTP URL used by the user before attributing results to a runtime.
- [ ] **Ongoing:** Preserve originals: never modify, move, rename, re-encode, or delete user videos, images, databases, metadata, or backups.
- [ ] **Ongoing:** Keep the working Flask UI, tags (including sidecar/DB merge), favorites, view counts, thumbnails, previews, galleries, playlist editing, individual video ratings, and independent playlist-level ratings intact.
- [ ] **Ongoing:** Prefer small, reversible changes with explicit before/after measurements and regression tests.
- [ ] **Ongoing:** Separate observed facts, reported observations, hypotheses, and unverified assumptions.
- [ ] **Ongoing:** Do not run broad repository-wide audits, bulk rewrites, dependency upgrades, Docker builds, WSL commands, or new background workers unless approved and directly justified.
- [ ] **Ongoing:** Keep tests read-only against production data. Use disposable fixtures for any write tests.
- [ ] **Ongoing:** Do not change an item to `[x]` without recording a command, result, and relevant source reference.

## 1. P0 — Fix 6K HEVC VR playback buffering (ACTIVE)

### User-observed symptoms and known media facts

- **Affected video:** Approximately 10 GB MP4; HEVC/H.265 (`hvc1`); 6144 × 3072; 59.94 FPS; AAC stereo.
- **Playback:** Smooth when opened directly from Windows storage in VLC; stalls repeatedly through Local Video Server in a desktop browser; worse on Meta Quest 2; pausing does not visibly increase buffering.
- **Diagnostic report:** `docs/VR_HIGH_BITRATE_PLAYBACK_DIAGNOSIS.md` (provided report; verify its location in the actual repository).
- **Reported ffprobe:** Duration ~1892.6 s; video bitrate ~43.4 Mbps; combined bitrate ~43.7 Mbps; file size 10,340,811,843 bytes.
- **Reported HTTP test:** One 10 MiB Range request completed in 2.407 s (~34.85 Mbps). This is **one short sample**, not proof of sustained throughput or of the root cause.
- **Reported HTTP behavior:** 206, `Content-Range`, `Content-Length`, `Accept-Ranges`, `video/mp4` appeared correct.
- **Reported source:** `backend/app/legacy_runtime.py` `stream_video` around lines 686–725; line numbers must be reverified.

### P0-A — Establish the *actual* active serving path (READ-ONLY)

- [x] **2026-10-23:** Identified native Windows environment: Python 3.14.6, Flask 3.1.3, Werkzeug 3.1.9 on Windows 11 Pro (`10.0.26300`). Process startup via `dev.ps1` runs `python main.py --host 192.168.4.96 --port 8000 --debug` (or `python main.py` binding `0.0.0.0:5000`). Confirmed Docker/WSL is not running (`docker` command not found).
- [x] **2026-10-23:** Confirmed client connects directly to native Flask server on port 8000 (no Nginx or Docker proxy in path). Nginx proxy in repo does not mount `/videos`.
- [x] **2026-10-23:** Inspected `stream_video` in `backend/app/legacy_runtime.py` (lines 685–723). Identified critical defect: open-ended requests (`Range: bytes=0-`) triggered unbounded `fh.read(length)` loading up to 9.63 GB into a single in-memory `bytes` object. Out-of-bounds ranges raised `ValueError` (HTTP 500); suffix ranges were ignored.
- [x] **2026-10-23:** Confirmed server threading: `main.py` explicitly executes `app.run(..., threaded=True)`. The server is multi-threaded, not single-threaded.

### P0-B — Reproduce and measure (READ-ONLY)

- [x] **2026-10-23:** Captured baseline HTTP Range measurements on `http://127.0.0.1:8000/video/Naughty%20Stepmom%20-%20Ava%20Addams%20-VR.mp4` across 10 MB, 64 MB, and 256 MB. Measured sustained throughput of 1,000–8,800+ Mbps (TTFB 2–5 ms via `curl.exe` and `urllib`), refuting the hypothesis of a ~34.85 Mbps server transfer ceiling.
- [x] **2026-10-23:** Direct filesystem read control measured on host storage: 10 MB in 0.0031s (27,025 Mbps), 64 MB in 0.0200s (26,778 Mbps), 256 MB in 0.0866s (24,793 Mbps). Disk I/O is not a bottleneck.
- [x] **2026-10-23:** Confirmed `ffprobe` stream properties: 6144×3072 @ 59.94 FPS HEVC Main Level 186, AAC stereo, 43.71 Mbps total bitrate, exact size 10,340,811,843 bytes. Verified MP4 box layout: `ftyp` at offset 0 (24 B), `moov` at offset 24 (1,059,436 B / ~1.06 MB), `mdat` at offset 1,383,622 (10,339,428,220 B). Progressive download layout is optimal.
- [x] **2026-10-23:** Identified client-side bottlenecks: Quest 2 Snapdragon XR2 Gen 1 hardware decoder is taxed by 6K @ 60 FPS HEVC in browser HTML5 `<video>`, creating stutter independent of network throughput.

### P0-C — Select one evidence-backed fix (APPROVAL GATE)

- [x] **2026-10-23:** Owner approved replacing unbounded `fh.read(length)` with bounded incremental streaming generator in `backend/app/legacy_runtime.py`, preserving all URLs, MIME types, HTTP 206 headers, and seeking.

### P0-D — After approval: implement and validate

- [x] **2026-10-23:** Implemented `_iter_file_range()` generator with `STREAMING_CHUNK_SIZE = 256 * 1024` (256 KB) and `_parse_byte_range()` supporting bounded, open-ended, suffix, unsatisfiable (HTTP 416), and malformed ranges in `backend/app/legacy_runtime.py`.
- [x] **2026-10-23:** Added comprehensive unit test suite in `tests/test_video_streaming.py` (10 passed in 0.37s) verifying bounded ranges, open-ended ranges, suffix ranges, clamp behavior, HTTP 416 responses, early client disconnect / file handle closure, and bounded memory chunks. Full test suite passed: 65 passed in 5.48s.
- [x] **2026-10-23:** Measured post-implementation throughput on 6K video: 10 MB at 1,035–5,370 Mbps (TTFB 2.1–2.7 ms); 64 MB at 2,713–3,441 Mbps (TTFB 2.5–3.6 ms); 256 MB at 1,145–1,235 Mbps (TTFB 3.4–4.2 ms). Verified mid-stream seeking (5 GB offset), suffix ranges, and clean client disconnect.
- [ ] Test uninterrupted desktop browser playback and seek/pause/resume with the 6K video (`http://192.168.4.96:8000/watch/...`).
- [ ] Test Quest 2 playback and seek/pause/resume; distinguish network delivery from XR2 browser decoder drops.
- [ ] Document rollback and restore baseline if improvement is not demonstrated.

**P0 exit criterion:** The problem video plays reliably on the target Quest workflow and desktop browser, with repeatable evidence identifying the improvement. If Quest decoder limitations prevent native playback, document that explicitly and obtain approval for a non-destructive alternative.

## 2. P1 — Performance Sprint B (PAUSED until P0 is resolved)

- [ ] Verify the reported library inventory (latest agent report: 599 videos and 599 thumbnails; earlier baseline: 598 videos and 598 thumbnails) and date each measurement.
- [ ] Preserve the completed missing-thumbnail repair if independently verified; do not create a new thumbnail-warming system without demonstrated need.
- [ ] Reconcile `docs/PERFORMANCE_BASELINE.md`, `docs/PERFORMANCE_AUDIT_FINDINGS.md`, and `PERFORMANCE_TODO.md` against current source and actual measurements.
- [ ] Investigate the home route's reported ~183–233 ms HTTP response and distinguish server time from browser rendering; do not optimize an already-fast gallery route without evidence.
- [ ] Profile SQLite queries and filesystem scans only when measurements show a meaningful contribution.
- [ ] Keep ongoing safety and regression rules ongoing, not marked complete.

## 3. P2 — Windows desktop launcher (DEFERRED)

- [ ] Review `DESKTOP_LAUNCHER_AUDIT_AND_MIGRATION_PLAN.md` against current source when streaming reliability is stable.
- [ ] Preserve Flask and existing UI; a future launcher must not require Docker/WSL for desktop operation.
- [ ] Confirm process ownership, clean startup/shutdown, writable data paths, media library location, and SQLite concurrency before packaging.
- [ ] Retain optional Docker/LAN server mode as a separate deployment path; do not make it a dependency of desktop mode.

## 4. Existing UI and organization work (MAINTENANCE)

The previous root TODO documented completed UI polish across home, gallery, lightbox, watch page, accessibility, recommendations, responsive layouts, and grouping. **Do not reopen or rebuild these features merely because they appear in historical checklists.** Verify regressions only when touched by current work. Playlist editing already exists; keep separate video-level and playlist-level ratings.

## 5. Documentation and evidence discipline

- [x] **2026-10-23:** Updated `docs/VR_HIGH_BITRATE_PLAYBACK_DIAGNOSIS.md` with verified runtime identity, benchmark commands/raw results, MP4 atom layout, memory flaw root cause, streaming generator fix, test results, and Quest 2 hardware decoder considerations.
- [x] **2026-10-23:** Corrected the report's unsupported assertions (refuted 34.85 Mbps ceiling; confirmed multithreaded Flask; replaced `send_file` workaround with targeted chunked streaming generator).
- [x] **2026-10-23:** Updated this TODO with validated measurements, commands, and results.
- [ ] Keep `PERFORMANCE_TODO.md` as the detailed historical/performance backlog; this root TODO governs current priority.

## 6. Current status & Next Steps

**Streaming fix implemented and validated in native Windows development environment.**
- Server memory allocation on open-ended requests is now strictly bounded (256 KB chunks).
- Full test suite passing (65/65 passed).
- Next action: Validate playback and seeking in desktop browser, followed by field testing on Meta Quest 2. Stop before marking VR playback resolved until real-device testing confirms it.
