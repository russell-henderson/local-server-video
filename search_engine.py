"""
Advanced Search Engine for Local Video Server
Provides intelligent search with FTS5, fuzzy matching, and real-time results
"""

import sqlite3
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import json

@dataclass
class SearchResult:
    """Represents a search result with relevance scoring"""
    video_path: str
    filename: str
    title: str
    tags: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    match_type: str = ""  # 'exact', 'fuzzy', 'tag', 'partial'
    snippet: str = ""
    duration: int = 0
    size: int = 0
    view_count: int = 0
    rating: float = 0.0
    last_watched: Optional[str] = None

@dataclass 
class SearchQuery:
    """Represents a search query with filters and options"""
    query: str
    tags: List[str] = field(default_factory=list)
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    min_rating: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sort_by: str = "relevance"  # relevance, name, date, rating, duration, views
    sort_order: str = "desc"
    limit: int = 50
    include_fuzzy: bool = True
    fuzzy_threshold: float = 0.6

class AdvancedSearchEngine:
    """
    Advanced search engine with features:
    - SQLite FTS5 for fast full-text search
    - Fuzzy matching for typos and partial matches
    - Tag-based filtering and search
    - Advanced filters (duration, rating, date)
    - Search result ranking and relevance scoring
    - Search history and analytics
    """
    
    def __init__(self, db_path: str = "video_search.db"):
        self.db_path = db_path
        self.search_history = []
        self.popular_queries = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize the search database with FTS5 tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Create FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS video_fts USING fts5(
                    video_path UNINDEXED,
                    filename,
                    title,
                    tags,
                    description,
                    performer_names,
                    content='video_index',
                    content_rowid='rowid'
                )
            """)
            
            # Main video index table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_index (
                    rowid INTEGER PRIMARY KEY,
                    video_path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    title TEXT,
                    tags TEXT,
                    description TEXT,
                    performer_names TEXT,
                    duration INTEGER DEFAULT 0,
                    file_size INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    date_added TEXT,
                    last_watched TEXT,
                    last_modified TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_filename ON video_index(filename)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_date_added ON video_index(date_added)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rating ON video_index(rating)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_view_count ON video_index(view_count)")
            
            # Search history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    results_count INTEGER,
                    execution_time REAL
                )
            """)
            
            # Popular queries view
            conn.execute("""
                CREATE VIEW IF NOT EXISTS popular_queries AS
                SELECT query, COUNT(*) as frequency, MAX(timestamp) as last_used
                FROM search_history 
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY query 
                ORDER BY frequency DESC
            """)
    
    def index_video(self, video_path: str, metadata: Dict[str, Any]) -> bool:
        """Index a single video for search"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Extract searchable text
                filename = Path(video_path).name
                title = metadata.get('title', filename)
                tags = json.dumps(metadata.get('tags', []))
                description = metadata.get('description', '')
                performer_names = ' '.join(metadata.get('performer_names', []))
                
                # Insert/update main index
                conn.execute("""
                    INSERT OR REPLACE INTO video_index 
                    (video_path, filename, title, tags, description, performer_names,
                     duration, file_size, view_count, rating, date_added, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_path, filename, title, tags, description, performer_names,
                    metadata.get('duration', 0),
                    metadata.get('file_size', 0),
                    metadata.get('view_count', 0),
                    metadata.get('rating', 0.0),
                    metadata.get('date_added', time.strftime('%Y-%m-%d %H:%M:%S')),
                    metadata.get('last_modified', time.strftime('%Y-%m-%d %H:%M:%S'))
                ))
                
                # Update FTS5 index
                conn.execute("""
                    INSERT OR REPLACE INTO video_fts 
                    (video_path, filename, title, tags, description, performer_names)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (video_path, filename, title, tags, description, performer_names))
                
                return True
                
        except Exception as e:
            print(f"❌ Error indexing video {video_path}: {e}")
            return False
    
    def reindex_all_videos(self, video_metadata: Dict[str, Dict[str, Any]]) -> int:
        """Reindex all videos from metadata"""
        print("🔄 Starting full reindex of video search database...")
        
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing indexes
            conn.execute("DELETE FROM video_fts")
            conn.execute("DELETE FROM video_index")
        
        indexed_count = 0
        total_videos = len(video_metadata)
        
        for video_path, metadata in video_metadata.items():
            if self.index_video(video_path, metadata):
                indexed_count += 1
            
            # Progress indicator
            if indexed_count % 100 == 0:
                print(f"📋 Indexed {indexed_count}/{total_videos} videos...")
        
        print(f"✅ Reindex complete: {indexed_count} videos indexed")
        return indexed_count
    
    def search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Perform advanced search with multiple strategies"""
        start_time = time.time()
        results = []
        
        try:
            # Strategy 1: FTS5 full-text search
            if search_query.query.strip():
                fts_results = self._fts_search(search_query)
                results.extend(fts_results)
            
            # Strategy 2: Fuzzy matching for typos
            if search_query.include_fuzzy and search_query.query.strip():
                fuzzy_results = self._fuzzy_search(search_query)
                results.extend(fuzzy_results)
            
            # Strategy 3: Tag-based search
            if search_query.tags:
                tag_results = self._tag_search(search_query)
                results.extend(tag_results)
            
            # Remove duplicates and merge scores
            results = self._deduplicate_results(results)
            
            # Apply filters
            results = self._apply_filters(results, search_query)
            
            # Sort results
            results = self._sort_results(results, search_query.sort_by, search_query.sort_order)
            
            # Limit results
            results = results[:search_query.limit]
            
            # Record search in history
            execution_time = time.time() - start_time
            self._record_search(search_query.query, len(results), execution_time)
            
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def _fts_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Perform FTS5 full-text search"""
        results = []
        
        # Prepare FTS5 query
        query_terms = search_query.query.strip().split()
        fts_query = ' AND '.join(f'"{term}"*' for term in query_terms)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT vi.*, rank
                    FROM video_fts 
                    JOIN video_index vi ON video_fts.video_path = vi.video_path
                    WHERE video_fts MATCH ?
                    ORDER BY rank
                """, (fts_query,))
                
                for row in cursor.fetchall():
                    result = self._row_to_search_result(row, "exact", 1.0)
                    results.append(result)
        
        except Exception as e:
            print(f"⚠️  FTS search error: {e}")
        
        return results
    
    def _fuzzy_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Perform fuzzy matching search for typos"""
        results = []
        query_lower = search_query.query.lower()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM video_index
                """)
                
                for row in cursor.fetchall():
                    # Check filename similarity
                    filename_similarity = SequenceMatcher(
                        None, query_lower, row[2].lower()
                    ).ratio()
                    
                    # Check title similarity
                    title_similarity = SequenceMatcher(
                        None, query_lower, (row[3] or '').lower()
                    ).ratio()
                    
                    # Check performer names similarity
                    performer_similarity = SequenceMatcher(
                        None, query_lower, (row[6] or '').lower()
                    ).ratio()
                    
                    # Use best similarity score
                    best_similarity = max(filename_similarity, title_similarity, performer_similarity)
                    
                    if best_similarity >= search_query.fuzzy_threshold:
                        result = self._row_to_search_result(row, "fuzzy", best_similarity)
                        results.append(result)
        
        except Exception as e:
            print(f"⚠️  Fuzzy search error: {e}")
        
        return results
    
    def _tag_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Search by tags"""
        results = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build tag filter query
                tag_conditions = []
                params = []
                
                for tag in search_query.tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                
                query = f"""
                    SELECT * FROM video_index
                    WHERE {' AND '.join(tag_conditions)}
                """
                
                cursor = conn.execute(query, params)
                
                for row in cursor.fetchall():
                    result = self._row_to_search_result(row, "tag", 0.9)
                    results.append(result)
        
        except Exception as e:
            print(f"⚠️  Tag search error: {e}")
        
        return results
    
    def _row_to_search_result(self, row: Tuple, match_type: str, relevance: float) -> SearchResult:
        """Convert database row to SearchResult object"""
        tags = json.loads(row[4]) if row[4] else []
        
        return SearchResult(
            video_path=row[1],
            filename=row[2],
            title=row[3] or row[2],
            tags=tags,
            relevance_score=relevance,
            match_type=match_type,
            duration=row[7],
            size=row[8],
            view_count=row[9],
            rating=row[10],
            last_watched=row[12]
        )
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicates and merge relevance scores"""
        unique_results = {}
        
        for result in results:
            path = result.video_path
            if path in unique_results:
                # Keep result with higher relevance score
                if result.relevance_score > unique_results[path].relevance_score:
                    unique_results[path] = result
            else:
                unique_results[path] = result
        
        return list(unique_results.values())
    
    def _apply_filters(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Apply duration, rating, and date filters"""
        filtered = []
        
        for result in results:
            # Duration filter
            if query.min_duration and result.duration < query.min_duration:
                continue
            if query.max_duration and result.duration > query.max_duration:
                continue
            
            # Rating filter
            if query.min_rating and result.rating < query.min_rating:
                continue
            
            # Date filters would require additional metadata
            # TODO: Implement date filtering when date metadata is available
            
            filtered.append(result)
        
        return filtered
    
    def _sort_results(self, results: List[SearchResult], sort_by: str, sort_order: str) -> List[SearchResult]:
        """Sort search results by specified criteria"""
        reverse = sort_order.lower() == "desc"
        
        if sort_by == "relevance":
            results.sort(key=lambda x: x.relevance_score, reverse=reverse)
        elif sort_by == "name":
            results.sort(key=lambda x: x.filename.lower(), reverse=reverse)
        elif sort_by == "rating":
            results.sort(key=lambda x: x.rating, reverse=reverse)
        elif sort_by == "duration":
            results.sort(key=lambda x: x.duration, reverse=reverse)
        elif sort_by == "views":
            results.sort(key=lambda x: x.view_count, reverse=reverse)
        elif sort_by == "date":
            results.sort(key=lambda x: x.last_watched or '', reverse=reverse)
        
        return results
    
    def _record_search(self, query: str, results_count: int, execution_time: float):
        """Record search in history for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO search_history (query, timestamp, results_count, execution_time)
                    VALUES (?, ?, ?, ?)
                """, (query, time.strftime('%Y-%m-%d %H:%M:%S'), results_count, execution_time))
        except Exception as e:
            print(f"⚠️  Error recording search: {e}")
    
    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on history and popular queries"""
        suggestions = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get suggestions from search history
                cursor = conn.execute("""
                    SELECT DISTINCT query FROM search_history
                    WHERE query LIKE ? 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (f'%{partial_query}%', limit))
                
                suggestions = [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            print(f"⚠️  Error getting suggestions: {e}")
        
        return suggestions
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular search queries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT query, frequency, last_used 
                    FROM popular_queries
                    LIMIT ?
                """, (limit,))
                
                return [
                    {"query": row[0], "frequency": row[1], "last_used": row[2]}
                    for row in cursor.fetchall()
                ]
        
        except Exception as e:
            print(f"⚠️  Error getting popular searches: {e}")
            return []
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total indexed videos
                total_videos = conn.execute("SELECT COUNT(*) FROM video_index").fetchone()[0]
                
                # Total searches
                total_searches = conn.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]
                
                # Average execution time
                avg_time = conn.execute("""
                    SELECT AVG(execution_time) FROM search_history
                    WHERE timestamp > datetime('now', '-7 days')
                """).fetchone()[0] or 0
                
                # Recent search count
                recent_searches = conn.execute("""
                    SELECT COUNT(*) FROM search_history
                    WHERE timestamp > datetime('now', '-24 hours')
                """).fetchone()[0]
                
                return {
                    "total_videos": total_videos,
                    "total_searches": total_searches,
                    "recent_searches_24h": recent_searches,
                    "avg_execution_time": round(avg_time, 3),
                    "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                }
        
        except Exception as e:
            print(f"⚠️  Error getting search stats: {e}")
            return {}

# Global search engine instance
_search_engine = None

def get_search_engine() -> AdvancedSearchEngine:
    """Get the global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = AdvancedSearchEngine()
    return _search_engine

def search_videos(query: str, **kwargs) -> List[SearchResult]:
    """Simple search interface"""
    search_query = SearchQuery(query=query, **kwargs)
    return get_search_engine().search(search_query)

if __name__ == "__main__":
    # Test the search engine
    print("Testing Advanced Search Engine...")
    
    engine = AdvancedSearchEngine()
    
    # Test indexing
    test_metadata = {
        "test_video.mp4": {
            "title": "Test Video",
            "tags": ["test", "sample"],
            "duration": 120,
            "view_count": 5,
            "rating": 4.5
        }
    }
    
    engine.reindex_all_videos(test_metadata)
    
    # Test search
    results = search_videos("test")
    print(f"Search results: {len(results)}")
    
    # Test stats
    stats = engine.get_search_stats()
    print(f"Search stats: {stats}")