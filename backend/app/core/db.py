"""
backend/app/core/db.py

Database session factory and SQLAlchemy configuration.
Provides connection pooling, session management, and migrations via Alembic.
"""
from contextlib import contextmanager
from typing import Generator, Optional
import os
from pathlib import Path

# Note: This is a bridge to the existing SQLite implementation
# For production, this would use SQLAlchemy ORM with Alembic migrations


class DatabaseSession:
    """Database session management wrapper."""

    def __init__(self, db_path: str = "video_metadata.db"):
        """
        Initialize database session.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)

    @contextmanager
    def get_session(self) -> Generator:
        """
        Context manager for database sessions.

        Usage:
            with db.get_session() as conn:
                conn.execute(...)
                conn.commit()
        """
        # Import here to avoid circular dependencies
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_with_retry(self, query: str, params: tuple = (),
                           max_retries: int = 3):
        """
        Execute query with automatic retry on lock.

        Args:
            query: SQL query string
            params: Query parameters
            max_retries: Number of retry attempts

        Returns:
            Query result
        """
        import sqlite3
        import time

        last_error: Optional[sqlite3.OperationalError] = None
        for attempt in range(max_retries):
            try:
                with self.get_session() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchall()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    last_error = e
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    raise
        if last_error:
            raise last_error
        raise RuntimeError("execute_with_retry failed unexpectedly")


# Singleton instance
_db_session: Optional[DatabaseSession] = None


def get_db_session() -> DatabaseSession:
    """
    Get or create database session instance.

    Returns:
        DatabaseSession singleton
    """
    global _db_session
    if _db_session is None:
        db_path = os.environ.get(
            'LVS_DB_PATH',
            'video_metadata.db'
        )
        _db_session = DatabaseSession(db_path)
    return _db_session


def init_db() -> None:
    """Initialize database (idempotent)."""
    # Import here to avoid circular imports
    from database_migration import VideoDatabase
    db = VideoDatabase()
    db.init_database()


# Alembic configuration (placeholder for future migration support)
class AlembicConfig:
    """Alembic migration configuration."""

    def __init__(self, db_path: str = "video_metadata.db"):
        """
        Initialize Alembic config.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.script_location = Path(__file__).parent / "migrations"
        self.sqlalchemy_url = f"sqlite:///{db_path}"

    def get_version_table_name(self) -> str:
        """Get Alembic version table name."""
        return "alembic_version"


def get_alembic_config() -> AlembicConfig:
    """Get Alembic configuration."""
    db_path = os.environ.get('LVS_DB_PATH', 'video_metadata.db')
    return AlembicConfig(db_path)
