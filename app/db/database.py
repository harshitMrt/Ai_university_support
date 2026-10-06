import sqlite3
from pathlib import Path
from typing import Generator
# pyrefly: ignore [missing-import]
from app.config import settings
from app.db.models import ALL_TABLE_SCHEMAS


def get_db_path() -> str:
    path = Path(settings.SQLITE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        with conn:
            for schema in ALL_TABLE_SCHEMAS:
                conn.execute(schema)
    finally:
        conn.close()


def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()
