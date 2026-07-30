"""SQLite database setup for the Task API."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "tasks.db"

SEED_TASKS = (
    ("Learn FastAPI basics", 1),
    ("Build CRUD endpoints", 0),
    ("Document the API", 0),
)


def get_database_path() -> Path:
    """Return the configured database path, defaulting to tasks.db."""
    configured_path = os.getenv("TASKS_DB_PATH")
    return Path(configured_path).expanduser().resolve() if configured_path else DEFAULT_DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection whose rows can be accessed by column name."""
    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create the tasks table and seed it only when it is empty."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
            )
            """
        )

        task_count = connection.execute(
            "SELECT COUNT(*) AS count FROM tasks"
        ).fetchone()["count"]

        if task_count == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                SEED_TASKS,
            )
