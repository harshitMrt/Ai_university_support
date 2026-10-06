"""
Production SQLite connection manager and pool provider.
Configures foreign key enforcement, WAL mode, and connection context management.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from app.core.config import settings
from app.core.logging import logger
from app.db.models import ALL_TABLE_SCHEMAS


def get_db_path() -> str:
    path = Path(settings.SQLITE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_connection() -> sqlite3.Connection:
    """
    Creates a new SQLite connection with foreign keys and WAL mode enabled.
    """
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception as e:
        logger.debug(f"WAL mode pragma notice: {e}")
    return conn


@contextmanager
def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager providing managed SQLite connection with automatic commit on success
    and rollback on exception.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """
    Generator yielding a cursor, committing upon completion.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """
    Initializes all database tables from schema definitions.
    """
    with get_db_session() as conn:
        for schema in ALL_TABLE_SCHEMAS:
            conn.execute(schema)
