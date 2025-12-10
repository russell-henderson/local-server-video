# Data Backend Architecture

## Overview

The Local Video Server uses **SQLite** as the primary backend for all video metadata including ratings, views, tags, and favorites. The application has migrated from JSON file-based storage to a database-backed architecture for improved performance, scalability, and data integrity.

## Primary Backend: SQLite Database

### Database File

- **Location**: `video_metadata.db` (root directory)
- **Type**: SQLite 3 database
- **Schema**: Managed by `database_migration.py`

### Data Stored

- **Videos**: Video file metadata (filename, added_date, file_size, duration)
- **Ratings**: User ratings (1-5 stars) per video
- **Views**: View counts and last viewed timestamps
- **Tags**: Many-to-many relationship between videos and tags
- **Favorites**: User favorite video selections

### Access Pattern

- All runtime operations read from and write to the database
- `cache_manager.py` defaults to `use_database=True`
- Database is initialized automatically on application startup
- All queries use indexed tables for optimal performance

## Cache Manager Configuration

The `cache_manager.py` module provides a unified interface for accessing video metadata:

```python
# Default configuration
cache = VideoCache(use_database=True)  # Database is primary backend
```

### Runtime Behavior

- **Primary Path**: All data operations use SQLite database
- **Fallback Path**: JSON files are only used if database initialization fails (emergency fallback)
- **Caching**: In-memory cache with TTL (5 minutes default) for performance
- **Thread Safety**: All operations are thread-safe with RLock

### Data Access Methods

- `get_ratings()` → Reads from database (cached)
- `get_views()` → Reads from database (cached)
- `get_tags()` → Reads from database (cached)
- `get_favorites()` → Reads from database (cached)
- `update_rating()` → Writes to database
- `update_view()` → Writes to database
- `update_tags()` → Writes to database
- `update_favorites()` → Writes to database

## JSON Files: Backup Snapshots Only

### File Locations

- `ratings.json` (root directory)
- `views.json` (root directory)
- `tags.json` (root directory)
- `favorites.json` (root directory)
- `backup_json/` (directory containing backup copies)

### Purpose

- **Backup snapshots**: JSON files are backup copies of data, not the source of truth
- **Migration source**: Used by `database_migration.py` for initial data import
- **Emergency fallback**: Only used if database is unavailable (should not occur in normal operation)
- **Diagnostics**: Can be used for data inspection without affecting the live database

### Git Status

- **Ignored by Git**: All JSON files and `backup_json/` directory are in `.gitignore`
- **Not committed**: These files contain user-specific data and should not be pushed to GitHub
- **Local only**: JSON files remain on disk for backup purposes but are not tracked in version control

## Migration and Restore

### Running a Migration

If you need to migrate JSON data to the database (e.g., after restoring from backup):

```python
from database_migration import VideoDatabase

db = VideoDatabase()
db.migrate_from_json()  # Migrates all JSON files to database
```

The migration function:

- Loads data from all JSON files
- Merges with existing database data (uses `INSERT OR REPLACE` for safe updates)
- Handles missing videos by adding them to the videos table
- Preserves existing database data that isn't in JSON files

### Using Backup Files for Diagnostics

To inspect backup data without affecting the live database:

```python
import json

# Read backup file
with open('backup_json/ratings.json', 'r') as f:
    backup_ratings = json.load(f)

# Inspect data (read-only operation)
print(f"Backup contains {len(backup_ratings)} ratings")
```

**Important**: The `backup_json/` directory is never accessed by the application at runtime. It is purely for manual backup and diagnostic purposes.

## Verification Checklist

To verify the application is using the database backend correctly:

1. **Check startup logs**: Application should print `[OK] Database backend initialized`
2. **Verify no JSON reads**: JSON files should not be accessed during normal operation
3. **Test without JSON**: Delete JSON files (in test environment) - application should continue working
4. **Check cache manager**: `cache.use_database` should be `True` and `cache.db` should not be `None`
5. **Verify writes**: Updates should persist to database, not JSON files

## Architecture Benefits

### Performance

- **Indexed queries**: Sub-millisecond data access
- **Reduced I/O**: No file system reads per request
- **Efficient caching**: In-memory cache with database persistence

### Reliability

- **ACID compliance**: Database transactions ensure data integrity
- **Concurrent access**: Thread-safe operations with proper locking
- **Data relationships**: Foreign keys maintain referential integrity

### Scalability

- **Efficient queries**: SQL queries with indexes scale better than JSON parsing
- **Bulk operations**: Database supports efficient batch updates
- **Future-ready**: Easy to migrate to PostgreSQL or other databases if needed

## Maintenance

### Database Backup

Regular database backups are recommended:

```bash
# Backup database
cp video_metadata.db video_metadata.db.backup_$(date +%Y%m%d)
```

### Orphaned Data Cleanup

The database automatically cleans up orphaned data (videos that no longer exist on disk):

```python
from database_migration import VideoDatabase

db = VideoDatabase()
db.cleanup_orphaned_data()  # Removes data for deleted video files
```

## Summary

- **Primary Backend**: SQLite database (`video_metadata.db`)
- **Cache Manager**: Defaults to `use_database=True`
- **JSON Files**: Backup snapshots only, ignored by Git
- **Runtime**: All operations use database, JSON is emergency fallback only
- **Backup Strategy**: JSON files and `backup_json/` directory for manual backups
