"""
Cache Manager for Video Server Performance Optimization
Implements in-memory caching with periodic refresh and write-through caching

Primary Backend: SQLite database (default, use_database=True)
- All runtime operations read from and write to SQLite database
- Database is the canonical source of truth for all video metadata

Legacy Fallback: JSON files (emergency fallback only)
- JSON files are backup snapshots, not the source of truth
- Only used if database initialization fails (should not occur in normal operation)
- See docs/DATA_BACKEND.md for architecture details
"""
import os
import json
import time
import threading
from collections import Counter
from typing import Any, Dict, List, Optional
from functools import wraps

# Import search engine

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
    
    def __init__(self, cache_ttl: int = 300, use_database: bool = True):  # 5 minutes default TTL
        self.cache_ttl = cache_ttl
        # Use shorter TTL for video list to detect new files faster
        self.video_list_ttl = min(60, cache_ttl)  # 1 minute max for video list
        self.use_database = use_database and DATABASE_AVAILABLE
        self._lock = threading.RLock()
        
        # Initialize database if available
        self.db = None
        if self.use_database:
            try:
                self.db = VideoDatabase()
                print("[OK] Database backend initialized")
            except (ImportError, OSError) as e:
                print(f"⚠️  Database initialization failed, falling back to JSON: {e}")
                self.use_database = False
        
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
        
        # File paths (for JSON fallback only - database is primary backend)
        # JSON files are used only if database is unavailable (emergency fallback)
        self.ratings_file = "ratings.json"
        self.views_file = "views.json"
        self.tags_file = "tags.json"
        self.favorites_file = "favorites.json"
        self.video_dir = "videos"
        
        # Initialize cache
        # Allow tests to opt-out of the automatic refresh on construction by setting
        # LVS_SKIP_INIT_REFRESH=1 in the environment. This helps test isolation so
        # tests can set `cache.video_dir` before triggering a refresh.
        if os.getenv('LVS_SKIP_INIT_REFRESH'):
            # Do not refresh now; tests may set paths and trigger refresh later
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
        """Load JSON file with error handling (legacy fallback only - not used in normal operation)"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_json_file(self, filepath: str, data: Dict):
        """Save JSON file atomically (legacy fallback only - not used when database is enabled)"""
        temp_file = filepath + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            # Atomic move
            if os.path.exists(filepath):
                os.replace(temp_file, filepath)
            else:
                os.rename(temp_file, filepath)
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
    
    def get_ratings(self) -> Dict[str, int]:
        """Get ratings with cache check"""
        with self._lock:
            was_valid = self._is_cache_valid('ratings')
            if not was_valid:
                if self.use_database and self.db:
                    self._ratings = self.db.get_ratings_map()
                else:
                    # Load from JSON
                    self._ratings = self._load_json_file(self.ratings_file)
                self._last_refresh['ratings'] = time.time()

            # Record cache metrics if available
            try:
                if perf_monitor:
                    if was_valid:
                        perf_monitor.record_cache_hit()
                    else:
                        perf_monitor.record_cache_miss()
            except Exception:
                pass

            return self._ratings.copy()
    
    def get_views(self) -> Dict[str, int]:
        """Get views with cache check"""
        with self._lock:
            was_valid = self._is_cache_valid('views')
            if not was_valid:
                if self.use_database and self.db:
                    self._views = self.db.get_views_map()
                else:
                    # Load from JSON
                    self._views = self._load_json_file(self.views_file)
                self._last_refresh['views'] = time.time()

            try:
                if perf_monitor:
                    if was_valid:
                        perf_monitor.record_cache_hit()
                    else:
                        perf_monitor.record_cache_miss()
            except Exception:
                pass

            return self._views.copy()
    
    def get_tags(self) -> Dict[str, List[str]]:
        """Get tags with cache check"""
        with self._lock:
            was_valid = self._is_cache_valid('tags')
            if not was_valid:
                if self.use_database and self.db:
                    self._tags = self.db.get_tags_map()
                else:
                    # Load from JSON
                    self._tags = self._load_json_file(self.tags_file)
                self._last_refresh['tags'] = time.time()

            try:
                if perf_monitor:
                    if was_valid:
                        perf_monitor.record_cache_hit()
                    else:
                        perf_monitor.record_cache_miss()
            except Exception:
                pass

            return self._tags.copy()
    
    def get_favorites(self) -> List[str]:
        """Get favorites with cache check"""
        with self._lock:
            was_valid = self._is_cache_valid('favorites')
            if not was_valid:
                if self.use_database and self.db:
                    # Load from database
                    self._favorites = self.db.get_favorites()
                else:
                    # Load from JSON
                    data = self._load_json_file(self.favorites_file)
                    self._favorites = data.get("favorites", [])
                self._last_refresh['favorites'] = time.time()

            try:
                if perf_monitor:
                    if was_valid:
                        perf_monitor.record_cache_hit()
                    else:
                        perf_monitor.record_cache_miss()
            except Exception:
                pass

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
                
                if set(current_videos) != set(self._video_list):
                    videos_found = len(current_videos)
                    was_videos = len(self._video_list)
                    print(f"[REFRESH] Video list changed: {videos_found} videos found (was {was_videos})")
                    
                    new_videos = set(current_videos) - set(self._video_list)
                    removed_videos = set(self._video_list) - set(current_videos)
                    
                    if new_videos:
                        sample = list(new_videos)[:5]
                        more = '...' if len(new_videos) > 5 else ''
                        print(f"[NEW] New videos detected: {', '.join(sample)}{more}")
                    
                    if removed_videos:
                        sample = list(removed_videos)[:5]
                        more = '...' if len(removed_videos) > 5 else ''
                        print(f"[REMOVED] Videos removed: {', '.join(sample)}{more}")
                        for video in removed_videos:
                            self._video_metadata.pop(video, None)
                
                self._video_list = current_videos
                self._last_refresh['video_list'] = time.time()
            try:
                if perf_monitor:
                    if was_valid:
                        perf_monitor.record_cache_hit()
                    else:
                        perf_monitor.record_cache_miss()
            except Exception:
                pass

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
                        'rating': self._ratings.get(video_filename, 0),
                        'views': self._views.get(video_filename, 0),
                        'tags': self._tags.get(video_filename, [])
                    }
                else:
                    return None
            
            return self._video_metadata[video_filename].copy()

    def get(self, key: str, force_refresh: bool = False):
        """Generic getter to support legacy cache.get(...) usage.

        Supports keys like:
          - 'all_videos', 'video_list', 'ratings', 'views', 'tags', 'favorites'
          - 'tags_<filename>', 'views_<filename>', 'rating_<filename>'
        """
        if force_refresh:
            base = key.split('_', 1)[0]
            if base in self._last_refresh:
                self._last_refresh[base] = 0

        if key == 'all_videos':
            return self.get_all_video_data()
        if key == 'video_list':
            return self.get_video_list()
        if key == 'ratings':
            return self.get_ratings()
        if key == 'views':
            return self.get_views()
        if key == 'tags':
            return self.get_tags()
        if key == 'favorites':
            return self.get_favorites()

        if key.startswith('tags_'):
            filename = key[len('tags_'):]
            return self.get_tags().get(filename, [])
        if key.startswith('views_'):
            filename = key[len('views_'):]
            return self.get_views().get(filename, 0)
        if key.startswith('rating_'):
            filename = key[len('rating_'):]
            return self.get_ratings().get(filename, 0)

        return None

    @property
    def last_refresh(self) -> Dict[str, float]:
        """Expose last refresh timestamps for admin endpoints."""
        with self._lock:
            return self._last_refresh.copy()

    def is_cache_valid(self, key: str) -> bool:
        """Public wrapper to check cache validity."""
        return self._is_cache_valid(key)
    
    def update_rating(self, filename: str, rating: int):
        """Update rating with write-through cache"""
        with self._lock:
            self._ratings[filename] = rating
            
            if self.use_database and self.db:
                # Save to database
                self.db.update_rating(filename, rating)
            else:
                # Save to JSON
                self._save_json_file(self.ratings_file, self._ratings)
            
    
    def update_view(self, filename: str):
        """Increment view count with write-through cache"""
        with self._lock:
            if self.use_database and self.db:
                # Database handles the increment
                new_count = self.db.increment_view_count(filename)
                self._views[filename] = new_count
            else:
                # Manual increment for JSON
                current_views = self._views.get(filename, 0) + 1
                self._views[filename] = current_views
                self._save_json_file(self.views_file, self._views)
                new_count = current_views
            
            return new_count
    
    def update_tags(self, filename: str, tags: List[str]):
        """Update tags with write-through cache"""
        with self._lock:
            self._tags[filename] = tags
            
            if self.use_database and self.db:
                # Update database - first clear existing tags, then add new ones
                existing_tags = self.db.get_video_tags(filename)
                for tag in existing_tags:
                    self.db.remove_tag(filename, tag)
                for tag in tags:
                    self.db.add_tag(filename, tag)
            else:
                # Save to JSON
                self._save_json_file(self.tags_file, self._tags)
            
            # Popular tags depend on overall usage counts
            self.invalidate_popular_tags()
    
    def update_favorites(self, favorites: List[str]):
        """Update favorites with write-through cache"""
        with self._lock:
            self._favorites = favorites
            
            if self.use_database and self.db:
                # For database, we need to sync the favorites table
                # This is more complex, so we'll implement a simpler approach
                # by clearing and re-adding favorites
                current_favorites = self.db.get_favorites()
                for fav in current_favorites:
                    if fav not in favorites:
                        self.db.toggle_favorite(fav)  # Remove
                for fav in favorites:
                    if fav not in current_favorites:
                        self.db.toggle_favorite(fav)  # Add
            else:
                # Save to JSON
                self._save_json_file(self.favorites_file, {"favorites": favorites})
    
    def refresh_all(self):
        """Force refresh all cache entries"""
        with self._lock:
            self._last_refresh = {key: 0 for key in self._last_refresh}
            self._video_metadata.clear()
            # Trigger reload on next access
            self.get_ratings()
            self.get_views()
            self.get_tags()
            self.get_popular_tags()
            self.get_favorites()
            self.get_video_list()
    
    def invalidate_ratings(self):
        """Invalidate ratings cache entry"""
        with self._lock:
            self._last_refresh['ratings'] = 0
            self._ratings.clear()
    
    def invalidate_views(self):
        """Invalidate views cache entry"""
        with self._lock:
            self._last_refresh['views'] = 0
            self._views.clear()
    
    def invalidate_tags(self):
        """Invalidate tags cache entry"""
        with self._lock:
            self._last_refresh['tags'] = 0
            self._tags.clear()
    
    def invalidate_favorites(self):
        """Invalidate favorites cache entry"""
        with self._lock:
            self._last_refresh['favorites'] = 0
            self._favorites.clear()
    
    def invalidate_video_list(self):
        """Invalidate video list cache entry"""
        with self._lock:
            self._last_refresh['video_list'] = 0
            self._video_list.clear()
    
    def invalidate_metadata(self):
        """Invalidate metadata cache entry"""
        with self._lock:
            self._last_refresh['metadata'] = 0
            self._video_metadata.clear()

    def invalidate_popular_tags(self):
        """Invalidate cached popular tag rankings."""
        with self._lock:
            self._last_refresh['popular_tags'] = 0
            self._popular_tags.clear()
    
    def _ensure_videos_in_database(self):
        """Ensure all videos from file system are in database"""
        if not (self.use_database and self.db):
            return
            
        # Get current video list from file system
        video_list = self._scan_video_directory()
        
        # Get videos already in database
        existing_videos = set()
        try:
            db_videos = self.db.get_all_videos()
            existing_videos = {v['filename'] for v in db_videos}
        except Exception as e:
            print(f"⚠️  Error getting videos from database: {e}")
            return
        
        # Find videos that need to be added to database
        new_videos = set(video_list) - existing_videos
        removed_videos = existing_videos - set(video_list)
        
        if new_videos:
            print(f"[SYNC] Adding {len(new_videos)} new videos to database...")
            
            # Add new videos to database
            try:
                for video_filename in new_videos:
                    video_path = os.path.join(self.video_dir, video_filename)
                    if os.path.exists(video_path):
                        try:
                            added_date = os.path.getctime(video_path)
                            file_size = os.path.getsize(video_path)
                        except OSError:
                            added_date = 0
                            file_size = 0
                        
                        # Insert video into database
                        with self.db.get_connection() as conn:
                            conn.execute("""
                                INSERT OR REPLACE INTO videos (filename, added_date, file_size)
                                VALUES (?, ?, ?)
                            """, (video_filename, added_date, file_size))
                            conn.commit()
                        
                        print(f"[OK] Added {video_filename} to database")
                
            except Exception as e:
                print(f"[ERROR] Error adding videos to database: {e}")
        
        if removed_videos:
            print(f"[SYNC] Removing {len(removed_videos)} videos missing on disk from database...")
            try:
                with self.db.get_connection() as conn:
                    conn.executemany(
                        "DELETE FROM videos WHERE filename = ?",
                        ((video,) for video in removed_videos)
                    )
                    conn.commit()
                for video_filename in removed_videos:
                    print(f"[OK] Removed {video_filename} from database")
            except Exception as e:
                print(f"[ERROR] Error removing videos from database: {e}")

    def get_all_video_data(self, sort_by: str = 'date',
                           reverse: bool = True) -> List[Dict]:
        """Get all video data with efficient bulk operation"""
        if self.use_database and self.db:
            # Ensure all videos are in database first
            self._ensure_videos_in_database()

            # Use database bulk operation
            order = 'desc' if reverse else 'asc'
            return self._filter_existing(
                self.db.get_all_videos(sort_by, order)
            )
        else:
            # Use JSON files with caching
            videos = self.get_video_list()
            video_data = []

            for video in videos:
                metadata = self.get_video_metadata(video)
                if metadata:
                    video_data.append(metadata)

            # Sort efficiently
            if sort_by == 'rating':
                video_data.sort(key=lambda x: x['rating'],
                                reverse=reverse)
            elif sort_by == 'title':
                video_data.sort(key=lambda x: x['filename'],
                                reverse=reverse)
            elif sort_by == 'views':
                video_data.sort(key=lambda x: x['views'],
                                reverse=reverse)
            else:  # default to date
                video_data.sort(key=lambda x: x['added_date'],
                                reverse=reverse)

            return video_data
        
    def get_videos_by_tag_optimized(self, tag: str) -> List[Dict]:
        """Get videos filtered by tag with database optimization"""
        if self.use_database and self.db:
            return self._filter_existing(self.db.get_videos_by_tag(tag))
        else:
            # Fallback to cache-based filtering
            all_tags = self.get_tags()
            filtered_videos = []
            for video, video_tags in all_tags.items():
                if any(tag.lower() in t.lower() for t in video_tags):
                    metadata = self.get_video_metadata(video)
                    if metadata:
                        filtered_videos.append(metadata)
            return filtered_videos
    
    def get_related_videos_optimized(self, filename: str, limit: int = 20) -> List[Dict]:
        """Get related videos with database optimization"""
        if self.use_database and self.db:
            return self._filter_existing(self.db.get_related_videos(filename, limit))
        else:
            # Fallback to cache-based related video logic
            all_tags = self.get_tags()
            current_tags = all_tags.get(filename, [])
            if not current_tags:
                return []

            current_tags_set = set(current_tags)
            related_videos: List[Dict] = []

            # Heuristic scoring to make recommendations feel smarter without DB support
            for video, video_tags in all_tags.items():
                if video == filename:
                    continue
                overlap = len(current_tags_set & set(video_tags))
                if overlap <= 0:
                    continue

                metadata = self.get_video_metadata(video)
                if not metadata:
                    continue

                rating = float(metadata.get('rating', 0) or 0)
                views = int(metadata.get('views', 0) or 0)
                recency = float(metadata.get('added_date', 0) or 0)

                score = (
                    overlap * 3.0
                    + rating * 0.6
                    + min(views, 5000) / 500.0
                    + (recency / 1e9) * 0.1  # lightweight bias toward newer items
                )

                metadata['tag_overlap'] = overlap
                metadata['related_score'] = score
                related_videos.append(metadata)

            related_videos.sort(
                key=lambda x: (
                    x.get('related_score', 0),
                    x.get('tag_overlap', 0),
                    x.get('rating', 0),
                    x.get('views', 0),
                ),
                reverse=True,
            )
            return related_videos[:limit]
    
    def get_all_unique_tags(self) -> List[str]:
        """Get all unique tags with database optimization"""
        if self.use_database and self.db:
            return self.db.get_all_tags()
        else:
            # Fallback to cache-based tag extraction
            all_tags = self.get_tags()
            unique_tags = set()
            for tag_list in all_tags.values():
                unique_tags.update(tag_list)
            return sorted(unique_tags, key=lambda x: x.lower())

    def get_popular_tags(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return most-used tags with basic caching."""
        with self._lock:
            limit = max(1, min(limit, 500))
            cached_limit = getattr(self, "_popular_tag_cache_limit", 200)
            needs_limit_refresh = len(self._popular_tags) < limit and limit > cached_limit
            was_valid = self._is_cache_valid('popular_tags') and not needs_limit_refresh

            if not was_valid:
                target_limit = max(limit, self._popular_tag_cache_limit)
                if self.use_database and self.db:
                    self._popular_tags = self.db.get_popular_tags(target_limit)
                else:
                    counter: Counter = Counter()
                    all_tags = self.get_tags()
                    for tag_list in all_tags.values():
                        counter.update(tag_list)
                    most_common = counter.most_common(target_limit)
                    self._popular_tags = [
                        {'tag': tag, 'count': count}
                        for tag, count in most_common
                    ]
                self._popular_tag_cache_limit = target_limit
                self._last_refresh['popular_tags'] = time.time()

            return self._popular_tags[:limit]

# Global cache instance
cache = VideoCache()

def cache_warmup():
    """Decorator to ensure cache is warmed up"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache is automatically warmed on first access
            return func(*args, **kwargs)
        return wrapper
    return decorator
