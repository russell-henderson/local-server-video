#!/usr/bin/env python3
"""Recover ratings, views, and favorites data from backup JSON files"""

import sys
import os

# Add project to path
sys.path.insert(0, os.getcwd())

from database_migration import VideoDatabase

print("=" * 60)
print("DATA RECOVERY: Restoring ratings, views, and favorites")
print("=" * 60)

db = VideoDatabase(db_path="data/video_metadata.db")

# Run migration from JSON backup files
print("\n[1/2] Migrating from JSON backup files...")
db.migrate_from_json(
    ratings_file="ratings.json",
    views_file="views.json",
    tags_file="tags.json",
    favorites_file="favorites.json",
    video_dir="videos"
)

print("\n[2/2] Importing sidecar tags (if present)...")
result = db.import_sidecar_tags(video_dir="videos")
print(f"  Sidecar tags imported: {result}")

# Verify recovery
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

with db.get_connection() as conn:
    ratings_count = conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
    views_count = conn.execute("SELECT COUNT(*) FROM views").fetchone()[0]
    favorites_count = conn.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    video_count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

print(f"✓ Total videos in database: {video_count}")
print(f"✓ Ratings recovered: {ratings_count}")
print(f"✓ Views recovered: {views_count}")
print(f"✓ Favorites recovered: {favorites_count}")

print("\n" + "=" * 60)
print("RECOVERY COMPLETE!")
print("=" * 60)
