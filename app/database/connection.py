"""Database Connection Manager for SQLite3.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
- Foreign key enforcement enabled on every connection
- Row factory (sqlite3.Row) for accessible column-name lookups
- Flask context-aware connection lifecycle (via flask.g)
- Standalone connection utilities for testing and seeding
- Transaction management context manager ensuring ACID guarantees
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
from flask import current_app, g


def get_db_path() -> str:
    """Retrieve database path from current Flask application configuration.

    Returns:
        str: Absolute or relative file path to the SQLite database.
    """
    if current_app:
        return current_app.config.get("DATABASE_PATH", "instance/restaurant.db")
    return "instance/restaurant.db"


def create_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a new SQLite connection with configured pragmas.

    Args:
        db_path: Path to database file or ':memory:' for tests.

    Returns:
        sqlite3.Connection: Configured connection with Row factory and foreign keys ON.
    """
    path = db_path if db_path is not None else get_db_path()
    is_uri = path.startswith("file:")
    conn = sqlite3.connect(path, timeout=10.0, detect_types=sqlite3.PARSE_DECLTYPES, uri=is_uri)
    conn.row_factory = sqlite3.Row
    # Critical maintainability requirement: explicitly enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    # WAL journal mode is only appropriate for persistent disk databases
    if not is_uri and path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def get_db() -> sqlite3.Connection:
    """Obtain or reuse SQLite connection for the current Flask request context.

    Returns:
        sqlite3.Connection: Thread-safe per-request database connection.
    """
    if "db" not in g:
        g.db = create_connection(get_db_path())
    return g.db


def close_db(e: Optional[BaseException] = None) -> None:
    """Close request-level database connection during Flask teardown.

    Args:
        e: Optional exception raised during request processing.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Cursor, None, None]:
    """Context manager for ACID database transactions.

    Commits on successful block execution, automatically rolls back on any error.

    Args:
        conn: The active sqlite3 connection.

    Yields:
        sqlite3.Cursor: Active cursor for transactional queries.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE;")
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
