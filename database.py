"""Postgres repository for the Task API.

The public functions in this module intentionally match the SQLite repository
used in BE-02. The FastAPI routes can keep calling the same interface while the
storage engine changes underneath them.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

SCHEMA_PATH = Path(__file__).resolve().parent / "sql" / "postgres_schema.sql"
SEED_TASKS = (
    ("Learn FastAPI basics", True),
    ("Build CRUD endpoints", False),
    ("Document the API", False),
)


def get_database_url() -> str:
    """Return DATABASE_URL or fail with a useful configuration error."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env before starting the app."
        )
    return database_url


def get_connection() -> psycopg.Connection[dict[str, Any]]:
    """Open a Postgres connection whose rows are returned as dictionaries."""
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
        connect_timeout=3,
    )


def initialize_database(max_attempts: int = 30, delay_seconds: float = 1.0) -> None:
    """Wait for Postgres, create the table, and seed it only when empty."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(schema_sql)
                    cursor.execute("SELECT COUNT(*) AS count FROM tasks")
                    task_count = int(cursor.fetchone()["count"])
                    if task_count == 0:
                        cursor.executemany(
                            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                            SEED_TASKS,
                        )
            return
        except psycopg.OperationalError as error:
            last_error = error
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Could not connect to Postgres after {max_attempts} attempts"
    ) from last_error


def row_to_task(row: dict[str, Any]) -> dict[str, object]:
    """Convert a Postgres row into the API's JSON task shape."""
    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "done": bool(row["done"]),
    }


# CRUD methods preserve the interface used by the FastAPI routes.
def fetch_all_tasks() -> list[dict[str, object]]:
    """Return every task ordered by id."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
            rows = cursor.fetchall()
    return [row_to_task(row) for row in rows]


def fetch_task(task_id: int) -> dict[str, object] | None:
    """Return one task using a parameterized query, or None if missing."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s",
                (task_id,),
            )
            row = cursor.fetchone()
    return row_to_task(row) if row is not None else None


def insert_task(title: str) -> dict[str, object]:
    """Insert a new incomplete task and return the created row."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done
                """,
                (title, False),
            )
            row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Postgres did not return the created task")
    return row_to_task(row)


def update_task_record(
    task_id: int,
    *,
    title: str | None,
    done: bool | None,
    update_title: bool,
    update_done: bool,
) -> dict[str, object] | None:
    """Update selected fields with parameters and return the changed task."""
    assignments: list[str] = []
    values: list[object] = []

    if update_title:
        assignments.append("title = %s")
        values.append(title)
    if update_done:
        assignments.append("done = %s")
        values.append(bool(done))

    if not assignments:
        return fetch_task(task_id)

    values.append(task_id)
    query = f"""
        UPDATE tasks
        SET {', '.join(assignments)}
        WHERE id = %s
        RETURNING id, title, done
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
            row = cursor.fetchone()
    return row_to_task(row) if row is not None else None


def delete_task_record(task_id: int) -> bool:
    """Delete a task with a parameterized query and report success."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s RETURNING id",
                (task_id,),
            )
            deleted_row = cursor.fetchone()
    return deleted_row is not None
