#!/usr/bin/env python3
"""
Quick SQLite health check for Local Video Server.

- Prints table row counts for critical metadata tables
- Verifies that expected indexes exist
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("video_metadata.db")

TABLES = {
    "videos": "SELECT COUNT(*) FROM videos",
    "ratings": "SELECT COUNT(*) FROM ratings",
    "views": "SELECT COUNT(*) FROM views",
    "video_tags": "SELECT COUNT(*) FROM video_tags",
    "favorites": "SELECT COUNT(*) FROM favorites",
}

EXPECTED_INDEXES = [
    "idx_videos_added_date",
    "idx_ratings_rating",
    "idx_views_count",
    "idx_views_last_viewed",
    "idx_tags_tag",
    "idx_tags_filename",
]


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit(f"❌ Database file not found at {DB_PATH.resolve()}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def print_counts(conn: sqlite3.Connection) -> None:
    print("📊 Table counts")
    for table, query in TABLES.items():
        cursor = conn.execute(query)
        count = cursor.fetchone()[0]
        print(f"  • {table:11s}: {count}")


def check_indexes(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA index_list('videos')")
    indexes = {row[1] for row in cursor.fetchall()}

    cursor = conn.execute("PRAGMA index_list('ratings')")
    indexes.update(row[1] for row in cursor.fetchall())

    cursor = conn.execute("PRAGMA index_list('views')")
    indexes.update(row[1] for row in cursor.fetchall())

    cursor = conn.execute("PRAGMA index_list('video_tags')")
    indexes.update(row[1] for row in cursor.fetchall())

    missing = [idx for idx in EXPECTED_INDEXES if idx not in indexes]
    if missing:
        print("⚠️  Missing indexes:")
        for idx in missing:
            print(f"  - {idx}")
    else:
        print("✅ All expected indexes present")


def main() -> None:
    conn = get_connection()
    try:
        print(f"🔍 Checking database: {DB_PATH.resolve()}")
        print_counts(conn)
        check_indexes(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

