"""Run the assignment's SQL queries against a temporary database copy."""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DATABASE = PROJECT_ROOT / "tasks.db"


def print_rows(label: str, rows: list[sqlite3.Row]) -> None:
    print(label)
    for row in rows:
        print(dict(row))
    print()


def main() -> None:
    if not SOURCE_DATABASE.exists():
        import main  # noqa: F401  # Creates tasks.db through app initialization.

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_database = Path(temporary_directory) / "tasks.db"
        shutil.copy2(SOURCE_DATABASE, temporary_database)

        with sqlite3.connect(temporary_database) as connection:
            connection.row_factory = sqlite3.Row

            all_tasks = connection.execute("SELECT * FROM tasks").fetchall()
            print_rows("SELECT * FROM tasks;", all_tasks)

            completed_tasks = connection.execute(
                "SELECT * FROM tasks WHERE done = 1"
            ).fetchall()
            print_rows("SELECT * FROM tasks WHERE done = 1;", completed_tasks)

            count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            print("SELECT COUNT(*) FROM tasks;")
            print(count, "tasks")
            print()

            connection.execute("UPDATE tasks SET done = 1")
            completed_count = connection.execute(
                "SELECT COUNT(*) FROM tasks WHERE done = 1"
            ).fetchone()[0]
            print("UPDATE tasks SET done = 1;")
            print(completed_count, "tasks are now completed")
            print()

            connection.execute("DELETE FROM tasks WHERE done = 1")
            remaining_count = connection.execute(
                "SELECT COUNT(*) FROM tasks"
            ).fetchone()[0]
            print("DELETE FROM tasks WHERE done = 1;")
            print(remaining_count, "tasks remain")

    print("Exploration used a temporary copy; the project database was not changed.")


if __name__ == "__main__":
    main()
