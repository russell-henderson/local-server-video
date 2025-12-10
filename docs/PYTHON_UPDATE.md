# Python Files Audit & Cleanup Guide

**Last Updated:** November 15, 2025  
**Purpose:** Inventory and assessment of all Python files in root directory to identify what can be safely removed

---

## Executive Summary

**Total Python Files:** 10 (after Phase 1 cleanup - Nov 15, 2025)  
**Currently Active:** 8 (essential, actively used)  
**Deprecated Stubs:** 0 (removed in Phase 1 cleanup ✅)  
**Empty/Placeholder:** 0 (removed in Phase 1 cleanup ✅)  
**Already Removed:** 1 (`subtitles.py` - removed earlier)

---

## Python Files Inventory

### 🟢 ACTIVE & REQUIRED

#### 1. **cache_manager.py** (621 lines)

- **Purpose:** Centralized cache manager for video metadata and file listings
- **Function:** Implements in-memory caching with periodic refresh and write-through caching
- **Features:**
  - Dual backend support (JSON fallback + SQLite performance)
  - Thread-safe with `threading.RLock()`
  - TTL-based cache refresh (5 minutes default)
  - Bulk metadata operations (ratings, views, tags, favorites, related videos)
- **Used By:** `main.py` (imported as `cache` singleton)
- **Dependencies:** `database_migration.VideoDatabase` (optional)
- **Status:** ✅ **KEEP** - Core infrastructure, actively used by all routes

---

#### 2. **config.py** (247 lines)

- **Purpose:** Configuration system with cascade support
- **Function:** Loads config from environment variables → `.env` → `config.json` → defaults
- **Features:**
  - `ServerConfig` dataclass with validation
  - `ConfigManager` singleton for config loading/reloading
  - Feature flags (VR simplification, preview generation)
  - Server, database, performance, search, and security settings
- **Used By:** `main.py` (imported as `get_config()`)
- **Status:** ✅ **KEEP** - Essential for application configuration

---

#### 3. **database_migration.py** (811 lines)

- **Purpose:** SQLite database manager and schema initialization
- **Function:** Single source of truth for video metadata persistence
- **Features:**
  - Schema management with foreign keys and CASCADE deletes
  - Thread-safe database operations
  - Gallery group management (new feature)
  - JSON fallback compatibility
  - Multiple metadata tables: videos, ratings, views, tags, favorites, gallery groups
- **Used By:** `main.py`, `cache_manager.py`, gallery API endpoints
- **Status:** ✅ **KEEP** - Database authority, critical for data persistence

---

#### 4. **file_watcher.py** (402 lines)

- **Purpose:** Intelligent file system monitoring for video directory
- **Function:** Detects new/modified/deleted video files with debouncing
- **Features:**
  - Watchdog-based directory monitoring
  - Debounce mechanism to prevent rapid re-processing
  - Batch processing for efficiency
  - Duplicate detection via checksum
  - Integration with thumbnail generation
- **Used By:** Potential usage in startup/maintenance workflows
- **Dependencies:** `watchdog` library (optional, gracefully fails)
- **Status:** ✅ **KEEP** - Enables automatic file discovery

---

#### 5. **performance_monitor.py** (303 lines)

- **Purpose:** Performance monitoring and latency tracking for routes
- **Function:** Records and reports route execution times and cache stats
- **Features:**
  - Singleton performance monitor with thread safety
  - Route-specific latency tracking
  - Cache hit/miss ratio calculation
  - Flask integration decorator (`flask_route_monitor`)
  - Memory usage tracking
- **Used By:** `main.py` (imported and applied as `@performance_monitor` decorator)
- **Status:** ✅ **KEEP** - Optional but actively monitoring, non-fatal if missing

---

#### 6. **thumbnail_manager.py** (272 lines)

- **Purpose:** Centralized thumbnail generation and maintenance
- **Function:** Maps videos → thumbnails, generates on-demand, syncs/cleans orphans
- **Features:**
  - Background thumbnail generation with ThreadPoolExecutor
  - Case-preserving filename mapping
  - One-shot `sync()` for cleaning orphan thumbnails and stale metadata
  - FFmpeg-based thumbnail extraction
  - CLI mode with `--force` rebuild option
- **Used By:** `main.py` (imported as `generate_async`, `sync`)
- **Dependencies:** FFmpeg in PATH
- **Status:** ✅ **KEEP** - Critical for video presentation

---

### 🟡 DEPRECATED STUBS (Safe to Remove)

These are **lightweight compatibility stubs** that prevent ImportError but provide no functionality. The original implementations are archived in `archive/python_legacy/`. These can be **safely removed** once imports are cleaned up.

#### 7. **app_subs_integration.py** (No-op stub)

- **Purpose:** Compatibility stub for removed subtitle system
- **Function:** Provides no-op functions to maintain backward compatibility
- **Contains:**
  - `register_subtitle_routes(app)` → no-op
  - `lazy_subtitle_check(video_path)` → returns `{"has_subtitles": False}`
  - `enhance_video_context(video_info)` → passthrough
- **Original Archive:** `archive/python_legacy/app_subs_integration.py`
- **Status:** ⚠️ **REMOVE** - Check for any remaining imports in `main.py` first
- **Action:** `git rm app_subs_integration.py`

---

#### 8. **config_subtitles.py** (No-op stub)

- **Purpose:** Compatibility stub for removed subtitle configuration
- **Function:** Provides empty `SubtitleConfig` dataclass
- **Contains:**
  - `SubtitleConfig` dataclass with disabled defaults
  - `SUBTITLES` global singleton with `enabled=False`
- **Original Archive:** `archive/python_legacy/config_subtitles.py`
- **Status:** ⚠️ **REMOVE** - Check for imports in `main.py`
- **Action:** `git rm config_subtitles.py`

---

#### 9. **manage_subs.py** (No-op stub)

- **Purpose:** Compatibility stub for removed subtitle CLI
- **Function:** Prints deprecation message
- **Contains:**
  - `main()` → prints "Subtitle CLI is archived and unavailable"
- **Original Archive:** `archive/python_legacy/manage_subs.py`
- **Status:** ⚠️ **REMOVE** - No remaining references expected
- **Action:** `git rm manage_subs.py`

---

#### 10. **test_subtitles.py** (Stub test file)

- **Purpose:** Placeholder test file for removed subtitle system
- **Function:** `main()` → prints deprecation message
- **Original Archive:** Original tests in `archive/python_legacy/`
- **Status:** ⚠️ **REMOVE** - No tests to run
- **Action:** `git rm test_subtitles.py`

---

#### 11. **maintenance.py** (Deprecation notice)

- **Purpose:** Redirect to new maintenance script location
- **Function:** Prints error message directing users to `tools/safe_maintenance.py`
- **Status:** ⚠️ **REMOVE** - Users should use `tools/safe_maintenance.py`
- **Action:** `git rm maintenance.py`

---

### 🔴 EMPTY/UNUSED

#### 12. **purge_orphans.py** (Empty file)

- **Purpose:** Unknown, file is completely empty
- **Status:** 🗑️ **REMOVE** - No purpose, no content
- **Action:** `git rm purge_orphans.py`

---

### 📊 QUESTIONABLE (Requires Review)

#### 13. **healthcheck.py** (886 lines)

- **Purpose:** Comprehensive system health check utility
- **Function:** Verifies app port, SQLite, cache, videos, ffmpeg, backups, SSL, quiet hours
- **Features:**
  - Standalone CLI: `python healthcheck.py`
  - Optional FastAPI mount (if available)
  - Checks: app port, SQLite integrity, Meilisearch, cache usage, video files, FFmpeg, backups, SSL certs, quiet hours, admin privileges
  - Returns JSON report with exit codes (0=ok, 1=warn, 2=fail)
- **Current Usage:** ⚠️ **Unclear** - Not referenced in `main.py`
- **Decision Needed:** 
  - Is this actively used? 
  - Should it be moved to `tools/` instead?
  - Does the current app config align with what it checks?
- **Status:** ❓ **CONDITIONAL KEEP** - Only if actively used for monitoring

---

#### 14. **search_engine.py** (removed)

- Removed along with the search/LLM features; related endpoints were deleted from `main.py`.
- **Database:** `video_search.db` (separate from main metadata DB)
- **Status:** ✅ **LIKELY KEEP** - Search API exists in main.py

---

## Cleanup Action Plan

### ✅ Phase 1: Remove Deprecated Stubs (COMPLETED)

**Date Completed:** November 15, 2025  
**Verification:** No remaining imports found in any Python files

```powershell
git rm app_subs_integration.py       # ✅ REMOVED
git rm config_subtitles.py           # ✅ REMOVED
git rm manage_subs.py                # ✅ REMOVED
git rm test_subtitles.py             # ⚠️  ALREADY MOVED TO DOCS
git rm maintenance.py                # ✅ REMOVED
git rm purge_orphans.py              # ✅ REMOVED
git commit -m "chore: remove deprecated subtitle and maintenance stub files"
```

**Files Removed:** 5  
**Reclaimed Lines:** ~108  
**Risk Level:** ✅ Low - These were no-ops with no active imports  
**Result:** Successfully cleaned up root directory

---

### Phase 2: Conditional Review (Requires Decision)

**healthcheck.py (886 lines):**

- Question: Is this actively monitoring the system?
- If Yes → KEEP
- If No → Consider moving to `tools/` or `docs/archive/`
- Current Status: Not imported by main.py, likely utility script

**search_engine.py (removed):**

- Status: Removed with search/LLM features
- Current Action: None

---

## Summary Table

| File | Lines | Status | Action | Reason |
|------|-------|--------|--------|--------|
| cache_manager.py | 621 | 🟢 Active | **KEEP** | Core infrastructure |
| config.py | 247 | 🟢 Active | **KEEP** | Config system |
| database_migration.py | 811 | 🟢 Active | **KEEP** | Database authority |
| file_watcher.py | 402 | 🟢 Active | **KEEP** | File monitoring |
| performance_monitor.py | 303 | 🟢 Active | **KEEP** | Performance tracking |
| search_engine.py | - | ✅ Removed | **DONE** | Search/LLM functionality retired |
| thumbnail_manager.py | 272 | 🟢 Active | **KEEP** | Thumbnail generation |
| healthcheck.py | 886 | ❓ Utility | **REVIEW** | May be unused or should move to `tools/` |
| **app_subs_integration.py** | ~20 | ✅ Removed | **DONE** | No-op stub, no imports found |
| **config_subtitles.py** | ~30 | ✅ Removed | **DONE** | No-op stub, no imports found |
| **manage_subs.py** | ~20 | ✅ Removed | **DONE** | No-op stub, no imports found |
| **maintenance.py** | ~10 | ✅ Removed | **DONE** | Redirects to tools/, no imports found |
| **purge_orphans.py** | 0 | ✅ Removed | **DONE** | Empty file |

---

## Recommendations

### ✅ Completed Actions (Phase 1)

1. ✅ Removed 5 deprecated subtitle stubs (verified no imports)
2. ✅ Removed empty `purge_orphans.py`
3. ✅ Verified `subtitles.py` was previously removed
4. ✅ Preserved 8 active Python files in root:
   - Core: `config.py`, `cache_manager.py`, `database_migration.py`
   - Performance: `performance_monitor.py`, `thumbnail_manager.py`
   - Monitoring: `file_watcher.py`
   - Utilities: `healthcheck.py` (pending review)

### Future Considerations

- Review `healthcheck.py` usage: Is it actively used for monitoring or should it move to `tools/`?
- Monitor root directory for new files and keep documentation up-to-date

---

## Notes

- **subtitles.py** was already removed in commit `405acf5`
- **app_subs_integration.py**, **config_subtitles.py**, **manage_subs.py**, **maintenance.py**, **purge_orphans.py** removed in commit `638d6d8` (verified no imports)
- All deprecated files have archived copies in `archive/python_legacy/`
- Main.py verified to have no imports of removed stub files
- Database and cache systems are tightly coupled; keep both together
- Thumbnail and file watcher are critical for video discovery and performance
- Root directory now contains only 10 essential Python files (down from 15 originally)
