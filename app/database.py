"""SQLite database setup for persistent journey storage."""

import sqlite3
from pathlib import Path

DB_PATH = Path("journeys.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the journeys table if it does not already exist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS journeys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                lines TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
