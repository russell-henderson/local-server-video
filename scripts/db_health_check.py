#!/usr/bin/env python3
"""
Quick SQLite health check for Local Video Server.

Usage:
    python scripts/db_health_check.py

Outputs:
    • Row counts for key tables
    • Whether required indexes are present

Exit codes:
    0 -> All checks passed
    1 -> Database file missing or an index/table check failed
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DB_PATH = Path("data/video_metadata.db")

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
    db_path = resolve_db_path()
    if not db_path.exists():
        raise SystemExit(f"❌ Database file not found at {db_path.resolve()}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def resolve_db_path() -> Path:
    env_path = os.getenv("LVS_DB_PATH")
    if env_path:
        return Path(env_path)
    if DB_PATH.exists():
        return DB_PATH
    return Path("video_metadata.db")


def print_counts(conn: sqlite3.Connection) -> None:
    print("[DB] Table counts")
    for table, query in TABLES.items():
        cursor = conn.execute(query)
        count = cursor.fetchone()[0]
        print(f"  - {table:11s}: {count}")


def check_indexes(conn: sqlite3.Connection) -> bool:
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
        print("[WARN] Missing indexes:")
        for idx in missing:
            print(f"  - {idx}")
        return False

    print("[OK] All expected indexes present")
    return True


def main() -> None:
    db_path = resolve_db_path()
    conn = get_connection()
    try:
        print(f"[DB] Checking database: {db_path.resolve()}")
        print_counts(conn)
        indexes_ok = check_indexes(conn)
    finally:
        conn.close()

    if not indexes_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
