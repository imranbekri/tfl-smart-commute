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
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                lines TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_journey_to_db(name: str, origin: str, destination: str, lines: list[str]) -> int:
    """Insert a new journey into the SQLite database and return its id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        lines_str = ",".join(lines)
        cursor.execute(
            "INSERT INTO journeys (name, origin, destination, lines) VALUES (?, ?, ?, ?)",
            (name, origin, destination, lines_str),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_journey_in_db(journey_id: int, name: str, origin: str, destination: str, lines: list[str]) -> None:
    """Update an existing journey in the SQLite database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        lines_str = ",".join(lines)
        cursor.execute(
            """
            UPDATE journeys
            SET name = ?, origin = ?, destination = ?, lines = ?
            WHERE id = ?
            """,
            (name, origin, destination, lines_str, journey_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_journey_from_db(journey_id: int) -> None:
    """Delete a journey from the SQLite database by its id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM journeys WHERE id = ?", (journey_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_journeys() -> list[dict]:
    """Load all journeys from the database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, origin, destination, lines FROM journeys ORDER BY id")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "origin": row["origin"],
                    "destination": row["destination"],
                    "lines": [ln.strip() for ln in (row["lines"] or "").split(",") if ln.strip()],
                }
            )
        return result
    finally:
        conn.close()


def get_journey_by_id(journey_id: int) -> dict | None:
    """Load a single journey from the SQLite database by its id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, origin, destination, lines FROM journeys WHERE id = ?",
            (journey_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "origin": row["origin"],
            "destination": row["destination"],
            "lines": [ln.strip() for ln in (row["lines"] or "").split(",") if ln.strip()],
        }
    finally:
        conn.close()
