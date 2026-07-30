"""Generate a local HTML database viewer from tasks.db."""

from __future__ import annotations

import html
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "tasks.db"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "database-viewer.html"


def main() -> None:
    if not DATABASE_PATH.exists():
        import main  # noqa: F401  # Initializes the database.

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
        ).fetchone()[0]

    table_rows = "\n".join(
        "<tr>"
        f"<td>{row['id']}</td>"
        f"<td>{html.escape(row['title'])}</td>"
        f"<td><span class='badge {'done' if row['done'] else 'open'}'>"
        f"{'true' if row['done'] else 'false'}</span></td>"
        "</tr>"
        for row in rows
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SQLite Database Viewer</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #f4f6f8; color: #18212b; font: 16px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  header {{ background: #213547; color: white; padding: 24px 42px; }}
  header h1 {{ margin: 0 0 6px; font-size: 28px; }}
  header p {{ margin: 0; color: #d7e2ec; }}
  main {{ padding: 28px 42px 44px; }}
  .toolbar {{ display: flex; gap: 16px; margin-bottom: 22px; }}
  .pill {{ background: white; border: 1px solid #d8dee5; border-radius: 8px; padding: 11px 15px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }}
  .pill strong {{ display: block; font-size: 12px; color: #617080; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 3px; }}
  .card {{ background: white; border: 1px solid #d8dee5; border-radius: 10px; margin-bottom: 24px; overflow: hidden; box-shadow: 0 3px 12px rgba(0,0,0,.05); }}
  .card h2 {{ margin: 0; padding: 17px 20px; font-size: 19px; border-bottom: 1px solid #e3e7eb; background: #fafbfc; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 14px 18px; text-align: left; border-bottom: 1px solid #e7ebef; }}
  th {{ color: #536273; background: #f8fafb; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }}
  tr:last-child td {{ border-bottom: 0; }}
  .badge {{ display: inline-block; border-radius: 999px; padding: 4px 10px; font-size: 13px; font-weight: 600; }}
  .badge.done {{ background: #dff7e8; color: #17663a; }}
  .badge.open {{ background: #fff1d6; color: #7a4b00; }}
  pre {{ margin: 0; padding: 18px 20px; background: #17212b; color: #e6edf3; overflow: auto; line-height: 1.5; font: 14px ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .status {{ padding: 12px 20px; color: #17663a; background: #ecfbf2; border-top: 1px solid #d7f0e1; font-weight: 600; }}
</style>
</head>
<body>
<header>
  <h1>SQLite Database Viewer</h1>
  <p>FlyRank Task API · persistent local database</p>
</header>
<main>
  <div class="toolbar">
    <div class="pill"><strong>Database</strong>tasks.db</div>
    <div class="pill"><strong>Table</strong>tasks</div>
    <div class="pill"><strong>Rows</strong>{len(rows)}</div>
  </div>
  <section class="card">
    <h2>Browse Data: tasks</h2>
    <table>
      <thead><tr><th>id</th><th>title</th><th>done</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
    <div class="status">Query executed successfully: SELECT * FROM tasks ORDER BY id;</div>
  </section>
  <section class="card">
    <h2>Table Schema</h2>
    <pre>{html.escape(schema)}</pre>
  </section>
</main>
</body>
</html>
"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(document, encoding="utf-8")
    print(f"Generated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
