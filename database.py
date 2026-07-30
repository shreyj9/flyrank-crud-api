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


def row_to_task(row: sqlite3.Row) -> dict[str, object]:
    """Convert a SQLite row into the API's JSON-friendly task shape."""
    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "done": bool(row["done"]),
    }


def fetch_all_tasks() -> list[dict[str, object]]:
    """Return every task ordered by id."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()
    return [row_to_task(row) for row in rows]


def fetch_task(task_id: int) -> dict[str, object] | None:
    """Return one task, or None when the id is unknown."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return row_to_task(row) if row is not None else None


def insert_task(title: str) -> dict[str, object]:
    """Insert a new incomplete task and return it."""
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, 0)",
            (title,),
        )
        task_id = int(cursor.lastrowid)

    created_task = fetch_task(task_id)
    if created_task is None:  # Defensive: the inserted row should always exist.
        raise RuntimeError("Created task could not be loaded")
    return created_task


def update_task_record(
    task_id: int,
    *,
    title: str | None,
    done: bool | None,
    update_title: bool,
    update_done: bool,
) -> dict[str, object] | None:
    """Update selected task fields and return the updated task."""
    assignments: list[str] = []
    values: list[object] = []

    if update_title:
        assignments.append("title = ?")
        values.append(title)
    if update_done:
        assignments.append("done = ?")
        values.append(int(bool(done)))

    if not assignments:
        return fetch_task(task_id)

    values.append(task_id)
    with get_connection() as connection:
        cursor = connection.execute(
            f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?",
            values,
        )
        if cursor.rowcount == 0:
            return None

    return fetch_task(task_id)


def delete_task_record(task_id: int) -> bool:
    """Delete a task and report whether a row was removed."""
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )
        return cursor.rowcount > 0
