"""
Cache Manager for Video Server Performance Optimization
Implements in-memory caching with periodic refresh and write-through caching
Supports both JSON (backward compatibility) and SQLite (performance) backends
"""
import os
import json
import time
import threading
from typing import Dict, List, Optional
from functools import wraps

# Try to import database backend
try:
    from database_migration import VideoDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

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
                print("✅ Database backend initialized")
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
        
        # Cache timestamps
        self._last_refresh: Dict[str, float] = {
            'ratings': 0.0,
            'views': 0.0,
            'tags': 0.0,
            'favorites': 0.0,
            'video_list': 0.0
        }
        
        # File paths (for JSON fallback)
        self.ratings_file = "ratings.json"
        self.views_file = "views.json"
        self.tags_file = "tags.json"
        self.favorites_file = "favorites.json"
        self.video_dir = "videos"
        
        # Initialize cache
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
        """Load JSON file with error handling"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_json_file(self, filepath: str, data: Dict):
        """Save JSON file atomically"""
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
            if not self._is_cache_valid('ratings'):
                if self.use_database and self.db:
                    # Load from database
                    videos = self.db.get_all_videos()
                    self._ratings = {v['filename']: v['rating'] for v in videos}
                else:
                    # Load from JSON
                    self._ratings = self._load_json_file(self.ratings_file)
                self._last_refresh['ratings'] = time.time()
            return self._ratings.copy()
    
    def get_views(self) -> Dict[str, int]:
        """Get views with cache check"""
        with self._lock:
            if not self._is_cache_valid('views'):
                if self.use_database and self.db:
                    # Load from database
                    videos = self.db.get_all_videos()
                    self._views = {v['filename']: v['views'] for v in videos}
                else:
                    # Load from JSON
                    self._views = self._load_json_file(self.views_file)
                self._last_refresh['views'] = time.time()
            return self._views.copy()
    
    def get_tags(self) -> Dict[str, List[str]]:
        """Get tags with cache check"""
        with self._lock:
            if not self._is_cache_valid('tags'):
                if self.use_database and self.db:
                    # Load from database
                    videos = self.db.get_all_videos()
                    self._tags = {v['filename']: v['tags'] for v in videos}
                else:
                    # Load from JSON
                    self._tags = self._load_json_file(self.tags_file)
                self._last_refresh['tags'] = time.time()
            return self._tags.copy()
    
    def get_favorites(self) -> List[str]:
        """Get favorites with cache check"""
        with self._lock:
            if not self._is_cache_valid('favorites'):
                if self.use_database and self.db:
                    # Load from database
                    self._favorites = self.db.get_favorites()
                else:
                    # Load from JSON
                    data = self._load_json_file(self.favorites_file)
                    self._favorites = data.get("favorites", [])
                self._last_refresh['favorites'] = time.time()
            return self._favorites.copy()
    
    def get_video_list(self) -> List[str]:
        """Get video list with cache check and improved file detection"""
        with self._lock:
            if not self._is_cache_valid('video_list'):
                allowed_extensions = ('.mp4', '.webm', '.ogg')
                if os.path.exists(self.video_dir):
                    current_videos = [
                        video for video in os.listdir(self.video_dir) 
                        if video.lower().endswith(allowed_extensions)
                    ]
                    
                    # Check if we have new videos
                    if set(current_videos) != set(self._video_list):
                        print(f"🔄 Video list changed: {len(current_videos)} videos found (was {len(self._video_list)})")
                        
                        # Clear video metadata cache for new videos
                        new_videos = set(current_videos) - set(self._video_list)
                        removed_videos = set(self._video_list) - set(current_videos)
                        
                        if new_videos:
                            print(f"➕ New videos detected: {', '.join(list(new_videos)[:5])}{'...' if len(new_videos) > 5 else ''}")
                        
                        if removed_videos:
                            print(f"➖ Videos removed: {', '.join(list(removed_videos)[:5])}{'...' if len(removed_videos) > 5 else ''}")
                            # Clean up metadata for removed videos
                            for video in removed_videos:
                                self._video_metadata.pop(video, None)
                    
                    self._video_list = current_videos
                else:
                    self._video_list = []
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
                        'rating': self._ratings.get(video_filename, 0),
                        'views': self._views.get(video_filename, 0),
                        'tags': self._tags.get(video_filename, [])
                    }
                else:
                    return None
            
            return self._video_metadata[video_filename].copy()
    
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
            
            # Invalidate video metadata cache
            if filename in self._video_metadata:
                self._video_metadata[filename]['rating'] = rating
    
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
            
            # Invalidate video metadata cache
            if filename in self._video_metadata:
                self._video_metadata[filename]['views'] = new_count
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
            
            # Invalidate video metadata cache
            if filename in self._video_metadata:
                self._video_metadata[filename]['tags'] = tags
    
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
            self.get_favorites()
            self.get_video_list()
    
    def _ensure_videos_in_database(self):
        """Ensure all videos from file system are in database"""
        if not (self.use_database and self.db):
            return
            
        # Get current video list from file system
        video_list = self.get_video_list()
        
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
        
        if new_videos:
            print(f"🔄 Adding {len(new_videos)} new videos to database...")
            
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
                        
                        print(f"✅ Added {video_filename} to database")
                
            except Exception as e:
                print(f"❌ Error adding videos to database: {e}")

    def get_all_video_data(self, sort_by: str = 'date', reverse: bool = True) -> List[Dict]:
        """Get all video data with efficient bulk operation"""
        if self.use_database and self.db:
            # Ensure all videos are in database first
            self._ensure_videos_in_database()
            
            # Use database bulk operation
            order = 'desc' if reverse else 'asc'
            return self._filter_existing(self.db.get_all_videos(sort_by, order))
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
                video_data.sort(key=lambda x: x['rating'], reverse=reverse)
            elif sort_by == 'title':
                video_data.sort(key=lambda x: x['filename'], reverse=reverse)
            elif sort_by == 'views':
                video_data.sort(key=lambda x: x['views'], reverse=reverse)
            else:  # default to date
                video_data.sort(key=lambda x: x['added_date'], reverse=reverse)
            
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
            related_videos = []
            
            for video, video_tags in all_tags.items():
                if video != filename:
                    overlap = len(current_tags_set & set(video_tags))
                    if overlap > 0:
                        metadata = self.get_video_metadata(video)
                        if metadata:
                            metadata['tag_overlap'] = overlap
                            related_videos.append(metadata)
            
            # Sort by overlap, then by rating
            related_videos.sort(key=lambda x: (x.get('tag_overlap', 0), x['rating']), reverse=True)
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
