"""
Cache Manager for Video Server Performance Optimization
Implements in-memory caching with periodic refresh and write-through caching

Primary Backend: SQLite database (required at runtime)
- All runtime operations read from and write to SQLite database
- Database is the canonical source of truth for all video metadata

JSON files are backup/export artifacts only and are not used for runtime fallback.
"""
import os
import json
import time
import threading
from collections import Counter
from typing import Any, Dict, List, Optional
from functools import wraps

# Try to import database backend
try:
    from database_migration import VideoDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Optional performance monitoring integration (non-fatal)
try:
    from performance_monitor import monitor as perf_monitor  # type: ignore
except Exception:
    perf_monitor = None

class VideoCache:
    """Centralized cache manager for video metadata and file listings"""
    
    def __init__(self, cache_ttl: int = 300, use_database: bool = True):
        self.cache_ttl = cache_ttl
        self.video_list_ttl = min(60, cache_ttl)
        self.use_database = use_database and DATABASE_AVAILABLE
        self._lock = threading.RLock()
        
        self.db = None
        if self.use_database:
            try:
                self.db = VideoDatabase()
                print("[OK] Database backend initialized")
            except Exception as e:
                raise RuntimeError(f"Database initialization failed: {e}") from e
        
        # Cache storage
        self._ratings: Dict[str, int] = {}
        self._views: Dict[str, int] = {}
        self._tags: Dict[str, List[str]] = {}
        self._favorites: List[str] = []
        self._video_list: List[str] = []
        self._video_metadata: Dict[str, Dict] = {}
        self._popular_tags: List[Dict[str, Any]] = []
        self._popular_tag_cache_limit = 200

        # Cache timestamps
        self._last_refresh: Dict[str, float] = {
            'ratings': 0.0,
            'views': 0.0,
            'tags': 0.0,
            'favorites': 0.0,
            'video_list': 0.0,
            'popular_tags': 0.0
        }
        
        self.ratings_file = "ratings.json"
        self.views_file = "views.json"
        self.tags_file = "tags.json"
        self.favorites_file = "favorites.json"
        self.video_dir = "videos"
        
        if os.getenv('LVS_SKIP_INIT_REFRESH'):
            self._last_refresh = {key: 0 for key in self._last_refresh}
            self._video_metadata.clear()
        else:
            self.refresh_all()

    def _filter_existing(self, items: List[Dict]) -> List[Dict]:
        """Return only rows whose filename exists on disk."""
        existing: List[Dict] = []
        for item in items:
            try:
                if os.path.exists(os.path.join(self.video_dir, item['filename'])):
                    existing.append(item)
            except Exception:
                continue
        return existing
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        ttl = self.video_list_ttl if cache_key == 'video_list' else self.cache_ttl
        return (time.time() - self._last_refresh[cache_key]) < ttl
    
    def _load_json_file(self, filepath: str) -> Dict:
        """Load JSON file with error handling."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_json_file(self, filepath: str, data: Dict):
        """Save JSON file atomically."""
        temp_file = filepath + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            if os.path.exists(filepath):
                os.replace(temp_file, filepath)
            else:
                os.rename(temp_file, filepath)
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def _get_sidecar_tags(self, filename: str) -> List[str]:
        """Read tags from adjacent sidecar file (<video>.<ext>.json)."""
        sidecar_path = os.path.join(self.video_dir, f"{filename}.json")
        if not os.path.exists(sidecar_path):
            return []
        try:
            with open(sidecar_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                tags = data.get("tags", [])
                if isinstance(tags, list):
                    return [str(t).strip() for t in tags if t]
        except Exception:
            pass
        return []

    def _merge_sidecar_tags(self, filename: str, db_tags: List[str]) -> List[str]:
        """Case-insensitive union of sidecar + DB tags."""
        merged: dict[str, str] = {}
        for source in (db_tags, self._get_sidecar_tags(filename)):
            for raw in source:
                tag = str(raw).strip()
                if not tag: continue
                if not tag.startswith("#"): tag = f"#{tag}"
                key = tag.lower()
                if key not in merged:
                    merged[key] = tag
        return sorted(merged.values(), key=lambda x: x.lower())
    
    def get_ratings(self) -> Dict[str, int]:
        """Get ratings with cache check and legacy merging."""
        with self._lock:
            was_valid = self._is_cache_valid('ratings')
            if not was_valid:
                if self.use_database and self.db:
                    self._ratings = self.db.get_ratings_map()
                    legacy = self._load_json_file(self.ratings_file)
                    for filename, rating in legacy.items():
                        if filename not in self._ratings:
                            self._ratings[filename] = rating
                else:
                    self._ratings = self._load_json_file(self.ratings_file)
                self._last_refresh['ratings'] = time.time()
            return self._ratings.copy()
    
    def get_views(self) -> Dict[str, int]:
        """Get views with cache check and legacy merging."""
        with self._lock:
            was_valid = self._is_cache_valid('views')
            if not was_valid:
                if self.use_database and self.db:
                    self._views = self.db.get_views_map()
                    legacy = self._load_json_file(self.views_file)
                    for filename, count in legacy.items():
                        if filename not in self._views:
                            self._views[filename] = count
                else:
                    self._views = self._load_json_file(self.views_file)
                self._last_refresh['views'] = time.time()
            return self._views.copy()
    
    def get_tags(self) -> Dict[str, List[str]]:
        """Get tags with cache check and dynamic sidecar merging."""
        with self._lock:
            was_valid = self._is_cache_valid('tags')
            if not was_valid:
                if self.use_database and self.db:
                    db_tags_map = self.db.get_tags_map()
                    self._tags = {}
                    all_filenames = self.db.get_all_filenames()
                    for fname in all_filenames:
                        self._tags[fname] = self._merge_sidecar_tags(fname, db_tags_map.get(fname, []))
                else:
                    self._tags = self._load_json_file(self.tags_file)
                self._last_refresh['tags'] = time.time()
            return self._tags.copy()
    
    def get_favorites(self) -> List[str]:
        """Get favorites with cache check and legacy merging."""
        with self._lock:
            was_valid = self._is_cache_valid('favorites')
            if not was_valid:
                if self.use_database and self.db:
                    db_favs = self.db.get_favorites()
                    legacy_data = self._load_json_file(self.favorites_file)
                    legacy_favs = legacy_data.get("favorites", [])
                    self._favorites = list(set(db_favs) | set(legacy_favs))
                else:
                    data = self._load_json_file(self.favorites_file)
                    self._favorites = data.get("favorites", [])
                self._last_refresh['favorites'] = time.time()
            return self._favorites.copy()
    
    def _scan_video_directory(self) -> List[str]:
        """Scan the filesystem for video files."""
        allowed_extensions = ('.mp4', '.webm', '.ogg')
        if not os.path.exists(self.video_dir):
            return []
        return [
            video for video in os.listdir(self.video_dir)
            if video.lower().endswith(allowed_extensions)
        ]
    
    def get_video_list(self) -> List[str]:
        """Get video list with cache check and improved file detection"""
        with self._lock:
            was_valid = self._is_cache_valid('video_list')
            if not was_valid:
                if self.use_database and self.db:
                    self._ensure_videos_in_database()
                    try:
                        current_videos = self.db.get_all_filenames()
                    except Exception as exc:
                        print(f"[WARN] Could not read filenames from database: {exc}")
                        current_videos = self._scan_video_directory()
                else:
                    current_videos = self._scan_video_directory()
                
                self._video_list = current_videos
                self._last_refresh['video_list'] = time.time()
            return self._video_list.copy()
    
    def get_video_metadata(self, video_filename: str) -> Optional[Dict]:
        """Get cached video metadata or compute it"""
        with self._lock:
            if video_filename not in self._video_metadata:
                video_path = os.path.join(self.video_dir, video_filename)
                if os.path.exists(video_path):
                    try:
                        added_date = os.path.getctime(video_path)
                    except OSError:
                        added_date = 0
                    
                    self._video_metadata[video_filename] = {
                        'filename': video_filename,
                        'added_date': added_date,
                        'rating': self.get_ratings().get(video_filename, 0),
                        'views': self.get_views().get(video_filename, 0),
                        'tags': self.get_tags().get(video_filename, [])
                    }
                else:
                    return None
            return self._video_metadata[video_filename].copy()

    def get(self, key: str, force_refresh: bool = False):
        """Generic getter to support legacy cache.get(...) usage."""
        if force_refresh:
            base = key.split('_', 1)[0]
            if base in self._last_refresh:
                self._last_refresh[base] = 0

        if key == 'all_videos': return self.get_all_video_data()
        if key == 'video_list': return self.get_video_list()
        if key == 'ratings': return self.get_ratings()
        if key == 'views': return self.get_views()
        if key == 'tags': return self.get_tags()
        if key == 'favorites': return self.get_favorites()

        if key.startswith('tags_'):
            return self.get_tags().get(key[len('tags_'):], [])
        if key.startswith('views_'):
            return self.get_views().get(key[len('views_'):], 0)
        if key.startswith('rating_'):
            return self.get_ratings().get(key[len('rating_'):], 0)
        return None

    @property
    def last_refresh(self) -> Dict[str, float]:
        with self._lock: return self._last_refresh.copy()

    def is_cache_valid(self, key: str) -> bool:
        return self._is_cache_valid(key)
    
    def update_rating(self, filename: str, rating: int):
        """Update rating with write-through cache"""
        with self._lock:
            if self.use_database and self.db:
                self.db.update_rating(filename, rating)
                self._ratings[filename] = rating
                self._video_metadata.pop(filename, None)
            else:
                self._ratings[filename] = rating
                self._save_json_file(self.ratings_file, self._ratings)
            
    def update_view(self, filename: str):
        """Increment view count with write-through cache"""
        with self._lock:
            if self.use_database and self.db:
                new_count = self.db.increment_view_count(filename)
                self._views[filename] = new_count
                self._video_metadata.pop(filename, None)
            else:
                new_count = self.get_views().get(filename, 0) + 1
                self._views[filename] = new_count
                self._save_json_file(self.views_file, self._views)
            return new_count
    
    def update_tags(self, filename: str, tags: List[str]):
        """Update tags with write-through cache"""
        with self._lock:
            normalized = []
            for t in tags:
                t = str(t).strip()
                if not t: continue
                if not t.startswith("#"): t = f"#{t}"
                normalized.append(t)
            
            if self.use_database and self.db:
                existing_tags = self.db.get_video_tags(filename)
                for tag in existing_tags: self.db.remove_tag(filename, tag)
                for tag in normalized: self.db.add_tag(filename, tag)
                self._tags[filename] = self._merge_sidecar_tags(filename, normalized)
                self._video_metadata.pop(filename, None)
            else:
                self._tags[filename] = normalized
                self._save_json_file(self.tags_file, self._tags)
            self.invalidate_popular_tags()
    
    def update_favorites(self, favorites: List[str]):
        """Update favorites with full state synchronization."""
        with self._lock:
            if self.use_database and self.db:
                current_db_favs = set(self.db.get_favorites())
                new_favs = set(favorites)
                for fav in (new_favs - current_db_favs): self.db.set_favorite(fav, True)
                for fav in (current_db_favs - new_favs): self.db.set_favorite(fav, False)
                self._favorites = list(new_favs)
            else:
                self._favorites = favorites
                self._save_json_file(self.favorites_file, {"favorites": self._favorites})
    
    def refresh_all(self):
        """Force refresh all cache entries"""
        with self._lock:
            self._last_refresh = {key: 0 for key in self._last_refresh}
            self._video_metadata.clear()
            self.get_ratings(); self.get_views(); self.get_tags(); self.get_popular_tags(); self.get_favorites(); self.get_video_list()
    
    def invalidate_ratings(self):
        with self._lock: self._last_refresh['ratings'] = 0; self._ratings.clear()
    def invalidate_views(self):
        with self._lock: self._last_refresh['views'] = 0; self._views.clear()
    def invalidate_tags(self):
        with self._lock: self._last_refresh['tags'] = 0; self._tags.clear()
    def invalidate_favorites(self):
        with self._lock: self._last_refresh['favorites'] = 0; self._favorites.clear()
    def invalidate_video_list(self):
        with self._lock: self._last_refresh['video_list'] = 0; self._video_list.clear()
    def invalidate_metadata(self):
        with self._lock: self._last_refresh['metadata'] = 0; self._video_metadata.clear()
    def invalidate_popular_tags(self):
        with self._lock: self._last_refresh['popular_tags'] = 0; self._popular_tags.clear()

    def prune_metadata_for_missing_videos(self, valid_videos: set[str]) -> Dict[str, int]:
        """Cleanup for metadata rows whose filenames are no longer on disk."""
        with self._lock:
            ratings = self.get_ratings()
            views = self.get_views()
            tags = self.get_tags()
            favorites = self.get_favorites()
            stale_filenames = (set(ratings.keys()) | set(views.keys()) | set(tags.keys()) | set(favorites)) - set(valid_videos)

            summary = {"videos_on_disk": len(valid_videos), "ratings_removed": 0, "views_removed": 0, "favorites_removed": 0, "tag_entries_removed": 0, "tag_values_removed": 0}
            if not stale_filenames: return summary

            if self.use_database and self.db:
                placeholders = ",".join("?" for _ in stale_filenames)
                params = tuple(stale_filenames)
                with self.db.get_connection() as conn:
                    ratings_deleted = conn.execute(f"DELETE FROM ratings WHERE filename IN ({placeholders})", params)
                    views_deleted = conn.execute(f"DELETE FROM views WHERE filename IN ({placeholders})", params)
                    favorites_deleted = conn.execute(f"DELETE FROM favorites WHERE filename IN ({placeholders})", params)
                    tags_deleted = conn.execute(f"DELETE FROM video_tags WHERE filename IN ({placeholders})", params)
                    conn.commit()
                summary["ratings_removed"] = int(ratings_deleted.rowcount or 0)
                summary["views_removed"] = int(views_deleted.rowcount or 0)
                summary["favorites_removed"] = int(favorites_deleted.rowcount or 0)
                summary["tag_entries_removed"] = int(tags_deleted.rowcount or 0)
            
            self.refresh_all()
            return summary
    
    def _ensure_videos_in_database(self):
        """Ensure all videos from file system are in database"""
        if not (self.use_database and self.db): return
        video_list = self._scan_video_directory()
        try:
            db_videos = self.db.get_all_videos()
            existing_videos = {v['filename'] for v in db_videos}
        except Exception: return
        
        new_videos = set(video_list) - existing_videos
        removed_videos = existing_videos - set(video_list)
        
        if new_videos:
            for video_filename in new_videos:
                video_path = os.path.join(self.video_dir, video_filename)
                added_date = os.path.getctime(video_path) if os.path.exists(video_path) else 0
                with self.db.get_connection() as conn:
                    conn.execute("INSERT OR REPLACE INTO videos (filename, added_date) VALUES (?, ?)", (video_filename, added_date))
                    conn.commit()
        
        if removed_videos:
            with self.db.get_connection() as conn:
                conn.executemany("DELETE FROM videos WHERE filename = ?", ((video,) for video in removed_videos))
                conn.commit()

    def get_all_video_data(self, sort_by: str = 'date', reverse: bool = True, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Get video data with optional pagination"""
        if self.use_database and self.db:
            self._ensure_videos_in_database()
            order = 'desc' if reverse else 'asc'
            return self._filter_existing(self.db.get_all_videos(sort_by, order, limit=limit, offset=offset))
        else:
            videos = self.get_video_list()
            video_data = [self.get_video_metadata(v) for v in videos if self.get_video_metadata(v)]
            if sort_by == 'rating': video_data.sort(key=lambda x: x['rating'], reverse=reverse)
            elif sort_by == 'title': video_data.sort(key=lambda x: x['filename'], reverse=reverse)
            elif sort_by == 'views': video_data.sort(key=lambda x: x['views'], reverse=reverse)
            else: video_data.sort(key=lambda x: x['added_date'], reverse=reverse)
            if limit is not None: return video_data[offset:offset + max(1, limit)]
            return video_data
        
    def get_videos_by_tag_optimized(self, tag: str) -> List[Dict]:
        if self.use_database and self.db: return self._filter_existing(self.db.get_videos_by_tag(tag))
        raise RuntimeError("Runtime DB backend unavailable")
    
    def get_related_videos_optimized(self, filename: str, limit: int = 20) -> List[Dict]:
        if self.use_database and self.db: return self._filter_existing(self.db.get_related_videos(filename, limit))
        raise RuntimeError("Runtime DB backend unavailable")
    
    def get_all_unique_tags(self) -> List[str]:
        if self.use_database and self.db: return self.db.get_all_tags()
        raise RuntimeError("Runtime DB backend unavailable")

    def get_popular_tags(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            was_valid = self._is_cache_valid('popular_tags') and len(self._popular_tags) >= limit
            if not was_valid:
                if self.use_database and self.db: self._popular_tags = self.db.get_popular_tags(max(limit, 200))
                else: raise RuntimeError("Runtime DB backend unavailable")
                self._last_refresh['popular_tags'] = time.time()
            return self._popular_tags[:limit]

# Global cache instance
cache = VideoCache()

def cache_warmup():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs): return func(*args, **kwargs)
        return wrapper
    return decorator
