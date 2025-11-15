#!/usr/bin/env python3
"""
maintenance.py - Unified Video Server Maintenance Tool
─────────────────────────────────────────────────────────────────────────────
All-in-one maintenance script for the local video server.

Commands:
  cleanup     - Remove orphaned thumbnails and metadata
  thumbnails  - Regenerate all video thumbnails
  sanitize    - Clean up video filenames and update metadata
  test        - Test database and cache functionality
  all         - Run all maintenance tasks

Usage:
  python maintenance.py cleanup [--dry-run]
  python maintenance.py thumbnails [--force]
  python maintenance.py sanitize [--dry-run]
  python maintenance.py test
  python maintenance.py all [--dry-run]
"""

import argparse
import json
import os
import re
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, List, Set

# Configuration
VIDEO_DIR = Path("videos")
THUMB_DIR = Path("static") / "thumbnails"
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".ogg"}
META_FILES = ["favorites.json", "ratings.json", "tags.json", "views.json"]
SQLITE_PATH = Path("video_cache.db")


class MaintenanceTool:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.action_prefix = "DRY-RUN would" if dry_run else "Will"
        
    def get_valid_videos(self) -> Set[str]:
        """Get set of valid video filenames (case-insensitive stems)"""
        return {p.stem.lower() for p in VIDEO_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in VIDEO_EXTS}
    
    def cleanup_orphans(self):
        """Remove orphaned thumbnails and metadata entries"""
        print("🧹 Starting cleanup of orphaned data...")
        
        valid_stems = self.get_valid_videos()
        print(f"Found {len(valid_stems)} valid videos")
        
        # 1. Clean orphaned thumbnails
        removed_thumbs = 0
        for thumb in THUMB_DIR.glob("*.jpg"):
            if thumb.stem.lower() not in valid_stems:
                print(f"{self.action_prefix} delete thumbnail {thumb.name}")
                if not self.dry_run:
                    thumb.unlink(missing_ok=True)
                removed_thumbs += 1
        
        if removed_thumbs == 0:
            print("✅ No orphaned thumbnails found")
        
        # 2. Clean JSON metadata files
        for meta_file in META_FILES:
            path = Path(meta_file)
            if not path.exists():
                continue
                
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                original_data = data.copy() if isinstance(data, dict) else data[:]
                
                if isinstance(data, list):
                    data = [v for v in data if Path(v).stem.lower() in valid_stems]
                elif isinstance(data, dict):
                    data = {k: v for k, v in data.items() 
                           if Path(k).stem.lower() in valid_stems}
                
                if data != original_data:
                    print(f"{self.action_prefix} clean {meta_file}")
                    if not self.dry_run:
                        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                        
            except Exception as e:
                print(f"⚠️  Skip {meta_file}: {e}")
        
        # 3. Clean SQLite database
        try:
            from cache_manager import cache
            if cache.use_database and cache.db:
                all_videos = cache.db.get_all_videos()
                orphaned_videos = []
                
                for video in all_videos:
                    vid = video['filename']
                    if Path(vid).stem.lower() not in valid_stems:
                        orphaned_videos.append(vid)
                        print(f"{self.action_prefix} delete DB row {vid}")
                
                if orphaned_videos and not self.dry_run:
                    # Delete orphaned videos from database
                    with cache.db.get_connection() as conn:
                        for vid in orphaned_videos:
                            conn.execute("DELETE FROM videos WHERE filename = ?", (vid,))
                            conn.execute("DELETE FROM video_tags WHERE filename = ?", (vid,))
                            conn.execute("DELETE FROM favorites WHERE filename = ?", (vid,))
                        conn.commit()
                    
                    cache.refresh_all()
                    print("🔄 Cache refreshed")
                elif not orphaned_videos:
                    print("✅ No orphaned database entries found")
                    
        except Exception as e:
            print(f"ℹ️  Database cleanup skipped: {e}")
        
        print("✅ Cleanup complete")
    
    def regenerate_thumbnails(self, force: bool = False):
        """Regenerate video thumbnails"""
        print("🖼️  Starting thumbnail regeneration...")
        
        # Create thumbnail directory if it doesn't exist
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
        
        if force:
            # Delete all existing thumbnails
            for thumb in THUMB_DIR.glob("*.jpg"):
                print(f"Removing existing thumbnail: {thumb.name}")
                if not self.dry_run:
                    thumb.unlink()
        
        # Generate thumbnails for all videos
        video_files = [f for f in VIDEO_DIR.iterdir() 
                      if f.is_file() and f.suffix.lower() in VIDEO_EXTS]
        
        print(f"Processing {len(video_files)} videos...")
        
        for video_path in video_files:
            thumbnail_path = THUMB_DIR / f"{video_path.stem}.jpg"
            
            if thumbnail_path.exists() and not force:
                print(f"⏭️  Skipping {video_path.name} (thumbnail exists)")
                continue
            
            print(f"🎬 Generating thumbnail for {video_path.name}")
            
            if not self.dry_run:
                try:
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', str(video_path),
                        '-ss', '00:00:30.000',
                        '-frames:v', '1',
                        '-vf', 'scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(320-iw)/2:(180-ih)/2',
                        str(thumbnail_path)
                    ], check=True, capture_output=True)
                    print(f"✅ Created {thumbnail_path.name}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to create thumbnail for {video_path.name}: {e}")
                except FileNotFoundError:
                    print("❌ FFmpeg not found. Please install FFmpeg to generate thumbnails.")
                    break
        
        print("✅ Thumbnail generation complete")
    
    def sanitize_filenames(self):
        """Sanitize video filenames and update metadata"""
        print("🔧 Starting filename sanitization...")
        
        def sanitize_filename(name: str) -> str:
            """Clean filename to safe characters"""
            base, ext = os.path.splitext(name)
            safe_base = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base)
            return safe_base + ext
        
        def load_json_safe(filepath: Path) -> dict:
            """Load JSON file safely"""
            if filepath.exists():
                try:
                    return json.loads(filepath.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"⚠️  Error loading {filepath}: {e}")
            return {}
        
        def save_json_safe(filepath: Path, data: dict):
            """Save JSON file safely"""
            if not self.dry_run:
                filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
        # Step 1: Rename video files
        renamed_map = {}
        for video_file in VIDEO_DIR.iterdir():
            if not video_file.is_file():
                continue
                
            old_name = video_file.name
            new_name = sanitize_filename(old_name)
            
            if old_name != new_name:
                new_path = VIDEO_DIR / new_name
                print(f"{self.action_prefix} rename: {old_name} → {new_name}")
                
                if not self.dry_run:
                    video_file.rename(new_path)
                renamed_map[old_name] = new_name
        
        if not renamed_map:
            print("✅ All filenames are already clean")
            return
        
        # Step 2: Update metadata files
        for meta_file in META_FILES:
            path = Path(meta_file)
            data = load_json_safe(path)
            
            if not data:
                continue
            
            updated = False
            if isinstance(data, list):
                # Handle favorites.json (list of filenames)
                for i, filename in enumerate(data):
                    if filename in renamed_map:
                        data[i] = renamed_map[filename]
                        updated = True
            elif isinstance(data, dict):
                # Handle other JSON files (filename -> value mappings)
                new_data = {}
                for filename, value in data.items():
                    new_filename = renamed_map.get(filename, filename)
                    new_data[new_filename] = value
                    if new_filename != filename:
                        updated = True
                data = new_data
            
            if updated:
                print(f"{self.action_prefix} update {meta_file}")
                save_json_safe(path, data)
        
        # Step 3: Update database if present
        try:
            from cache_manager import cache
            if cache.use_database and cache.db and not self.dry_run:
                for old_name, new_name in renamed_map.items():
                    # This would need to be implemented in the database layer
                    print(f"ℹ️  Database update needed: {old_name} → {new_name}")
                cache.refresh_all()
        except Exception as e:
            print(f"ℹ️  Database update skipped: {e}")
        
        print("✅ Filename sanitization complete")
    
    def test_system(self):
        """Test database and cache functionality"""
        print("🧪 Running system tests...")
        
        # Test database
        try:
            from database_migration import VideoDatabase
            db = VideoDatabase()
            videos = db.get_all_videos()
            print(f"✅ Database: {len(videos)} videos found")
            
            if videos:
                print("   Sample videos:")
                for v in videos[:3]:
                    print(f"   - {v['filename']}")
        except Exception as e:
            print(f"❌ Database test failed: {e}")
        
        # Test cache
        try:
            from cache_manager import cache
            video_list = cache.get_video_list()
            print(f"✅ Cache: {len(video_list)} videos found")
            
            video_data = cache.get_all_video_data()
            print(f"✅ Cache metadata: {len(video_data)} entries")
            
            if video_list:
                print("   Sample videos:")
                for v in video_list[:3]:
                    print(f"   - {v}")
        except Exception as e:
            print(f"❌ Cache test failed: {e}")
        
        # Test file system
        video_files = list(VIDEO_DIR.glob("*"))
        video_count = len([f for f in video_files if f.suffix.lower() in VIDEO_EXTS])
        print(f"✅ File system: {video_count} video files found")
        
        thumb_count = len(list(THUMB_DIR.glob("*.jpg")))
        print(f"✅ Thumbnails: {thumb_count} thumbnail files found")
        
        print("✅ System test complete")


def main():
    parser = argparse.ArgumentParser(description="Video Server Maintenance Tool")
    parser.add_argument("command", choices=["cleanup", "thumbnails", "sanitize", "test", "all"],
                       help="Maintenance command to run")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--force", action="store_true",
                       help="Force regeneration of existing thumbnails")
    
    args = parser.parse_args()
    
    tool = MaintenanceTool(dry_run=args.dry_run)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    if args.command == "cleanup":
        tool.cleanup_orphans()
    elif args.command == "thumbnails":
        tool.regenerate_thumbnails(force=args.force)
    elif args.command == "sanitize":
        tool.sanitize_filenames()
    elif args.command == "test":
        tool.test_system()
    elif args.command == "all":
        print("🚀 Running all maintenance tasks...\n")
        tool.cleanup_orphans()
        print()
        tool.sanitize_filenames()
        print()
        tool.regenerate_thumbnails()
        print()
        tool.test_system()
        print("\n🎉 All maintenance tasks complete!")


if __name__ == "__main__":
    main()