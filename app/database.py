"""SQLite database setup for persistent journey storage.

The database file is stored in the project root (next to the app/ directory)
so journeys survive restarts regardless of the working directory from which
the server is started.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "journeys.db"


class DatabaseError(Exception):
    """Raised when a database operation fails."""

    def __init__(self, message: str, user_message: str | None = None):
        super().__init__(message)
        self.user_message = user_message or "A database error occurred. Please try again later."


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as exc:
        logger.error("Failed to connect to database: %s", exc)
        raise DatabaseError(f"Connection failed: {exc}") from exc


def init_db() -> None:
    """Create the journeys table if it does not already exist."""
    conn = None
    try:
        conn = get_connection()
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
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        logger.error("Failed to initialise database: %s", exc)
        raise DatabaseError(f"Initialisation failed: {exc}") from exc
    finally:
        if conn:
            conn.close()


def add_journey_to_db(name: str, origin: str, destination: str, lines: list[str]) -> int:
    """Insert a new journey into the SQLite database and return its id."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        lines_str = ",".join(lines)
        cursor.execute(
            "INSERT INTO journeys (name, origin, destination, lines) VALUES (?, ?, ?, ?)",
            (name, origin, destination, lines_str),
        )
        conn.commit()
        return cursor.lastrowid
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        logger.error("Failed to add journey: %s", exc)
        raise DatabaseError(
            f"Insert failed: {exc}",
            "Could not save the journey. Please try again.",
        ) from exc
    finally:
        if conn:
            conn.close()


def update_journey_in_db(journey_id: int, name: str, origin: str, destination: str, lines: list[str]) -> int:
    """Update an existing journey in the SQLite database. Returns number of rows affected."""
    conn = None
    try:
        conn = get_connection()
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
        return cursor.rowcount
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        logger.error("Failed to update journey %s: %s", journey_id, exc)
        raise DatabaseError(
            f"Update failed: {exc}",
            "Could not update the journey. Please try again.",
        ) from exc
    finally:
        if conn:
            conn.close()


def delete_journey_from_db(journey_id: int) -> None:
    """Delete a journey from the SQLite database by its id."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM journeys WHERE id = ?", (journey_id,))
        conn.commit()
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        logger.error("Failed to delete journey %s: %s", journey_id, exc)
        raise DatabaseError(
            f"Delete failed: {exc}",
            "Could not delete the journey. Please try again.",
        ) from exc
    finally:
        if conn:
            conn.close()


def get_all_journeys() -> list[dict]:
    """Load all journeys from the database."""
    conn = None
    try:
        conn = get_connection()
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
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        logger.error("Failed to load journeys: %s", exc)
        raise DatabaseError(
            f"Query failed: {exc}",
            "Could not load saved journeys. Please try again later.",
        ) from exc
    finally:
        if conn:
            conn.close()


def get_journey_by_id(journey_id: int) -> dict | None:
    """Load a single journey from the SQLite database by its id."""
    conn = None
    try:
        conn = get_connection()
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
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        logger.error("Failed to load journey %s: %s", journey_id, exc)
        raise DatabaseError(
            f"Query failed: {exc}",
            "Could not load the journey. Please try again.",
        ) from exc
    finally:
        if conn:
            conn.close()
