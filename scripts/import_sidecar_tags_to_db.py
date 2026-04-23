"""
Explicit one-shot sidecar tag importer.

Usage:
  python scripts/import_sidecar_tags_to_db.py
"""

from database_migration import VideoDatabase


def main() -> None:
    db = VideoDatabase()
    summary = db.import_sidecar_tags("videos")
    print(
        f"[IMPORT] scanned={summary['sidecars_scanned']} "
        f"added={summary['tag_rows_added']}"
    )


if __name__ == "__main__":
    main()
