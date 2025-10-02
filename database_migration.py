"""
Database Migration and Setup for Performance Optimization
Migrates JSON files to SQLite for better performance with larger datasets
"""
import sqlite3
import json
import os
from typing import Dict, List, Optional
import threading
from contextlib import contextmanager

class VideoDatabase:
    """SQLite database manager for video metadata"""
    
    def __init__(self, db_path: str = "video_metadata.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            # Create tables
            conn.executescript("""
                -- Videos table
                CREATE TABLE IF NOT EXISTS videos (
                    filename TEXT PRIMARY KEY,
                    added_date REAL,
                    file_size INTEGER,
                    duration REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Ratings table  
                CREATE TABLE IF NOT EXISTS ratings (
                    filename TEXT PRIMARY KEY REFERENCES videos(filename) ON DELETE CASCADE,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Views table
                CREATE TABLE IF NOT EXISTS views (
                    filename TEXT PRIMARY KEY REFERENCES videos(filename) ON DELETE CASCADE,
                    view_count INTEGER DEFAULT 0,
                    last_viewed TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Tags table (many-to-many relationship)
                CREATE TABLE IF NOT EXISTS video_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT REFERENCES videos(filename) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filename, tag)
                );
                
                -- Favorites table
                CREATE TABLE IF NOT EXISTS favorites (
                    filename TEXT PRIMARY KEY REFERENCES videos(filename) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_videos_added_date ON videos(added_date);
                CREATE INDEX IF NOT EXISTS idx_ratings_rating ON ratings(rating);
                CREATE INDEX IF NOT EXISTS idx_views_count ON views(view_count);
                CREATE INDEX IF NOT EXISTS idx_views_last_viewed ON views(last_viewed);
                CREATE INDEX IF NOT EXISTS idx_tags_tag ON video_tags(tag);
                CREATE INDEX IF NOT EXISTS idx_tags_filename ON video_tags(filename);
                
                -- Update triggers
                CREATE TRIGGER IF NOT EXISTS update_videos_timestamp 
                    AFTER UPDATE ON videos
                    BEGIN
                        UPDATE videos SET updated_at = CURRENT_TIMESTAMP WHERE filename = NEW.filename;
                    END;
                
                CREATE TRIGGER IF NOT EXISTS update_ratings_timestamp 
                    AFTER UPDATE ON ratings
                    BEGIN
                        UPDATE ratings SET updated_at = CURRENT_TIMESTAMP WHERE filename = NEW.filename;
                    END;
                
                CREATE TRIGGER IF NOT EXISTS update_views_timestamp 
                    AFTER UPDATE ON views
                    BEGIN
                        UPDATE views SET updated_at = CURRENT_TIMESTAMP WHERE filename = NEW.filename;
                    END;
            """)
            conn.commit()
    
    def migrate_from_json(self, ratings_file: str = "ratings.json", 
                         views_file: str = "views.json",
                         tags_file: str = "tags.json", 
                         favorites_file: str = "favorites.json",
                         video_dir: str = "videos"):
        """Migrate existing JSON data to SQLite"""
        
        def load_json_safe(filepath: str) -> Dict:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            return {}
        
        print("Starting migration from JSON to SQLite...")
        
        # Load JSON data
        ratings_data = load_json_safe(ratings_file)
        views_data = load_json_safe(views_file)
        tags_data = load_json_safe(tags_file)
        favorites_data = load_json_safe(favorites_file)
        
        with self.get_connection() as conn:
            # Get all video files
            video_files = set()
            if os.path.exists(video_dir):
                allowed_extensions = ('.mp4', '.webm', '.ogg')
                video_files = {
                    f for f in os.listdir(video_dir) 
                    if f.lower().endswith(allowed_extensions)
                }
            
            # Add all video files mentioned in JSON data
            video_files.update(ratings_data.keys())
            video_files.update(views_data.keys())
            video_files.update(tags_data.keys())
            video_files.update(favorites_data.get("favorites", []))
            
            print(f"Found {len(video_files)} unique video files")
            
            # Insert videos
            for filename in video_files:
                video_path = os.path.join(video_dir, filename)
                added_date = 0
                file_size = 0
                
                if os.path.exists(video_path):
                    try:
                        added_date = os.path.getctime(video_path)
                        file_size = os.path.getsize(video_path)
                    except OSError:
                        pass
                
                conn.execute("""
                    INSERT OR REPLACE INTO videos (filename, added_date, file_size)
                    VALUES (?, ?, ?)
                """, (filename, added_date, file_size))
            
            # Insert ratings
            for filename, rating in ratings_data.items():
                conn.execute("""
                    INSERT OR REPLACE INTO ratings (filename, rating)
                    VALUES (?, ?)
                """, (filename, rating))
            
            # Insert views
            for filename, view_count in views_data.items():
                conn.execute("""
                    INSERT OR REPLACE INTO views (filename, view_count)
                    VALUES (?, ?)
                """, (filename, view_count))
            
            # Insert tags
            for filename, tag_list in tags_data.items():
                for tag in tag_list:
                    conn.execute("""
                        INSERT OR IGNORE INTO video_tags (filename, tag)
                        VALUES (?, ?)
                    """, (filename, tag))
            
            # Insert favorites
            for filename in favorites_data.get("favorites", []):
                conn.execute("""
                    INSERT OR REPLACE INTO favorites (filename)
                    VALUES (?)
                """, (filename,))
            
            conn.commit()
            print("Migration completed successfully!")
    
    def get_all_videos(self, sort_by: str = 'added_date', order: str = 'desc') -> List[Dict]:
        """Get all videos with metadata efficiently"""
        order_clause = 'DESC' if order.lower() == 'desc' else 'ASC'
        
        # Map sort parameters to SQL columns
        sort_mapping = {
            'title': 'v.filename',
            'filename': 'v.filename', 
            'date': 'v.added_date',
            'added_date': 'v.added_date',
            'rating': 'COALESCE(r.rating, 0)',
            'views': 'COALESCE(view.view_count, 0)'
        }
        
        sort_column = sort_mapping.get(sort_by, 'v.added_date')
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT 
                    v.filename,
                    v.added_date,
                    v.file_size,
                    COALESCE(r.rating, 0) as rating,
                    COALESCE(view.view_count, 0) as views,
                    GROUP_CONCAT(vt.tag) as tags,
                    CASE WHEN f.filename IS NOT NULL THEN 1 ELSE 0 END as is_favorite
                FROM videos v
                LEFT JOIN ratings r ON v.filename = r.filename
                LEFT JOIN views view ON v.filename = view.filename
                LEFT JOIN video_tags vt ON v.filename = vt.filename
                LEFT JOIN favorites f ON v.filename = f.filename
                GROUP BY v.filename, v.added_date, v.file_size, r.rating, view.view_count, f.filename
                ORDER BY {sort_column} {order_clause}
            """)
            
            videos = []
            for row in cursor:
                tags = row['tags'].split(',') if row['tags'] else []
                videos.append({
                    'filename': row['filename'],
                    'added_date': row['added_date'],
                    'file_size': row['file_size'],
                    'rating': row['rating'],
                    'views': row['views'],
                    'tags': tags,
                    'is_favorite': bool(row['is_favorite'])
                })
            
            return videos
    
    def get_all_filenames(self) -> List[str]:
        """Get all video filenames"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT filename FROM videos ORDER BY filename")
            return [row['filename'] for row in cursor]
    
    def delete_video_by_filename(self, filename: str) -> None:
        """Delete a video and all its associated data"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM videos WHERE filename = ?", (filename,))
            conn.commit()
    
    def get_video_by_filename(self, filename: str) -> Optional[Dict]:
        """Get single video with all metadata"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    v.filename,
                    v.added_date,
                    v.file_size,
                    COALESCE(r.rating, 0) as rating,
                    COALESCE(view.view_count, 0) as views,
                    GROUP_CONCAT(vt.tag) as tags,
                    CASE WHEN f.filename IS NOT NULL THEN 1 ELSE 0 END as is_favorite
                FROM videos v
                LEFT JOIN ratings r ON v.filename = r.filename
                LEFT JOIN views view ON v.filename = view.filename
                LEFT JOIN video_tags vt ON v.filename = vt.filename
                LEFT JOIN favorites f ON v.filename = f.filename
                WHERE v.filename = ?
                GROUP BY v.filename, v.added_date, v.file_size, r.rating, view.view_count, f.filename
            """, (filename,))
            
            row = cursor.fetchone()
            if row:
                tags = row['tags'].split(',') if row['tags'] else []
                return {
                    'filename': row['filename'],
                    'added_date': row['added_date'],
                    'file_size': row['file_size'],
                    'rating': row['rating'],
                    'views': row['views'],
                    'tags': tags,
                    'is_favorite': bool(row['is_favorite'])
                }
            return None
    
    def update_rating(self, filename: str, rating: int):
        """Update video rating"""
        with self.get_connection() as conn:
            # Ensure video exists
            conn.execute("INSERT OR IGNORE INTO videos (filename) VALUES (?)", (filename,))
            # Update rating
            conn.execute("""
                INSERT OR REPLACE INTO ratings (filename, rating)
                VALUES (?, ?)
            """, (filename, rating))
            conn.commit()
    
    def increment_view_count(self, filename: str) -> int:
        """Increment view count and return new count"""
        with self.get_connection() as conn:
            # Ensure video exists
            conn.execute("INSERT OR IGNORE INTO videos (filename) VALUES (?)", (filename,))
            
            # Update view count
            conn.execute("""
                INSERT INTO views (filename, view_count, last_viewed)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(filename) DO UPDATE SET
                    view_count = view_count + 1,
                    last_viewed = CURRENT_TIMESTAMP
            """, (filename,))
            
            # Get new count
            cursor = conn.execute(
                "SELECT view_count FROM views WHERE filename = ?", 
                (filename,)
            )
            new_count = cursor.fetchone()['view_count']
            conn.commit()
            return new_count
    
    def add_tag(self, filename: str, tag: str):
        """Add tag to video"""
        with self.get_connection() as conn:
            # Ensure video exists
            conn.execute("INSERT OR IGNORE INTO videos (filename) VALUES (?)", (filename,))
            # Add tag
            conn.execute("""
                INSERT OR IGNORE INTO video_tags (filename, tag)
                VALUES (?, ?)
            """, (filename, tag))
            conn.commit()
    
    def remove_tag(self, filename: str, tag: str):
        """Remove tag from video"""
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM video_tags
                WHERE filename = ? AND tag = ?
            """, (filename, tag))
            conn.commit()
    
    def get_video_tags(self, filename: str) -> List[str]:
        """Get tags for a specific video"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT tag FROM video_tags
                WHERE filename = ?
                ORDER BY tag
            """, (filename,))
            return [row['tag'] for row in cursor]
    
    def toggle_favorite(self, filename: str) -> bool:
        """Toggle favorite status, return new status"""
        with self.get_connection() as conn:
            # Ensure video exists
            conn.execute("INSERT OR IGNORE INTO videos (filename) VALUES (?)", (filename,))
            
            # Check current status
            cursor = conn.execute(
                "SELECT filename FROM favorites WHERE filename = ?", 
                (filename,)
            )
            is_favorite = cursor.fetchone() is not None
            
            if is_favorite:
                conn.execute("DELETE FROM favorites WHERE filename = ?", (filename,))
                new_status = False
            else:
                conn.execute("INSERT INTO favorites (filename) VALUES (?)", (filename,))
                new_status = True
            
            conn.commit()
            return new_status
    
    def get_favorites(self) -> List[str]:
        """Get list of favorite video filenames"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT filename FROM favorites ORDER BY created_at DESC")
            return [row['filename'] for row in cursor]
    
    def get_videos_by_tag(self, tag: str) -> List[Dict]:
        """Get videos filtered by tag"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT
                    v.filename,
                    v.added_date,
                    v.file_size,
                    COALESCE(r.rating, 0) as rating,
                    COALESCE(view.view_count, 0) as views,
                    CASE WHEN f.filename IS NOT NULL THEN 1 ELSE 0 END as is_favorite
                FROM videos v
                JOIN video_tags vt ON v.filename = vt.filename
                LEFT JOIN ratings r ON v.filename = r.filename
                LEFT JOIN views view ON v.filename = view.filename
                LEFT JOIN favorites f ON v.filename = f.filename
                WHERE vt.tag LIKE ?
                ORDER BY v.added_date DESC
            """, (f"%{tag}%",))
            
            videos = []
            for row in cursor:
                # Get all tags for this video
                tag_cursor = conn.execute(
                    "SELECT tag FROM video_tags WHERE filename = ?", 
                    (row['filename'],)
                )
                tags = [t['tag'] for t in tag_cursor]
                
                videos.append({
                    'filename': row['filename'],
                    'added_date': row['added_date'],
                    'file_size': row['file_size'],
                    'rating': row['rating'],
                    'views': row['views'],
                    'tags': tags,
                    'is_favorite': bool(row['is_favorite'])
                })
            
            return videos
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT tag FROM video_tags
                ORDER BY tag COLLATE NOCASE
            """)
            return [row['tag'] for row in cursor]
    
    def get_related_videos(self, filename: str, limit: int = 20) -> List[Dict]:
        """Get related videos based on shared tags"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT
                    v.filename,
                    v.added_date,
                    COALESCE(r.rating, 0) as rating,
                    COALESCE(view.view_count, 0) as views,
                    COUNT(shared_tags.tag) as tag_overlap
                FROM videos v
                JOIN video_tags vt ON v.filename = vt.filename
                JOIN video_tags shared_tags ON vt.tag = shared_tags.tag
                LEFT JOIN ratings r ON v.filename = r.filename
                LEFT JOIN views view ON v.filename = view.filename
                WHERE shared_tags.filename = ? AND v.filename != ?
                GROUP BY v.filename, v.added_date, r.rating, view.view_count
                ORDER BY tag_overlap DESC, r.rating DESC
                LIMIT ?
            """, (filename, filename, limit))
            
            videos = []
            for row in cursor:
                # Get tags for this video
                tag_cursor = conn.execute(
                    "SELECT tag FROM video_tags WHERE filename = ?", 
                    (row['filename'],)
                )
                tags = [t['tag'] for t in tag_cursor]
                
                videos.append({
                    'filename': row['filename'],
                    'added_date': row['added_date'],
                    'rating': row['rating'],
                    'views': row['views'],
                    'tags': tags,
                    'tag_overlap': row['tag_overlap']
                })
            
            return videos
    
    def cleanup_orphaned_data(self):
        """Remove data for videos that no longer exist on disk"""
        video_dir = "videos"
        if not os.path.exists(video_dir):
            return
        
        # Get actual video files
        allowed_extensions = ('.mp4', '.webm', '.ogg')
        actual_files = {
            f for f in os.listdir(video_dir) 
            if f.lower().endswith(allowed_extensions)
        }
        
        with self.get_connection() as conn:
            # Get videos in database
            cursor = conn.execute("SELECT filename FROM videos")
            db_videos = {row['filename'] for row in cursor}
            
            # Find orphaned entries
            orphaned = db_videos - actual_files
            
            if orphaned:
                print(f"Removing data for {len(orphaned)} orphaned videos...")
                for filename in orphaned:
                    conn.execute("DELETE FROM videos WHERE filename = ?", (filename,))
                conn.commit()
                print("Cleanup completed")
            else:
                print("No orphaned data found")

def migration_script():
    """Run the migration from JSON to SQLite"""
    print("Video Server Database Migration")
    print("=" * 40)
    
    # Initialize database
    db = VideoDatabase()
    
    # Check if migration is needed
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM videos")
        video_count = cursor.fetchone()['count']
    
    if video_count > 0:
        response = input(f"Database already contains {video_count} videos. Re-run migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled")
            return
    
    # Run migration
    db.migrate_from_json()
    
    # Cleanup orphaned data
    db.cleanup_orphaned_data()
    
    # Show final stats
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                (SELECT COUNT(*) FROM videos) as video_count,
                (SELECT COUNT(*) FROM ratings) as rating_count,
                (SELECT COUNT(*) FROM views) as view_count,
                (SELECT COUNT(*) FROM video_tags) as tag_count,
                (SELECT COUNT(*) FROM favorites) as favorite_count
        """)
        stats = cursor.fetchone()
    
    print("\\nMigration Summary:")
    print(f"  Videos: {stats['video_count']}")
    print(f"  Ratings: {stats['rating_count']}")
    print(f"  Views: {stats['view_count']}")
    print(f"  Tags: {stats['tag_count']}")
    print(f"  Favorites: {stats['favorite_count']}")
    print("\\nMigration completed! You can now use the optimized database backend.")

if __name__ == "__main__":
    migration_script()
