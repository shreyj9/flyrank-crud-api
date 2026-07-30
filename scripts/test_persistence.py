"""Verify that SQLite data survives application reloads."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_import(database_path: Path) -> None:
    environment = os.environ.copy()
    environment["TASKS_DB_PATH"] = str(database_path)
    subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "tasks.db"

        run_import(database_path)
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                ("Persist after restart", 0),
            )

        run_import(database_path)
        with sqlite3.connect(database_path) as connection:
            rows = connection.execute(
                "SELECT title FROM tasks ORDER BY id"
            ).fetchall()

        titles = [row[0] for row in rows]
        assert len(titles) == 4, f"Expected 4 tasks after restart, got {len(titles)}"
        assert "Persist after restart" in titles
        print("Persistence check passed: tasks survived an application restart.")


if __name__ == "__main__":
    main()
