"""Create a PNG snapshot of the SQLite database viewer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "tasks.db"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "database-viewer.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{filename}", size)


def rounded_box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: str, outline: str) -> None:
    draw.rounded_rectangle(xy, radius=12, fill=fill, outline=outline, width=2)


def main() -> None:
    if not DATABASE_PATH.exists():
        import main  # noqa: F401

    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
        ).fetchone()[0]

    image = Image.new("RGB", (1440, 1000), "#f4f6f8")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 1440, 116), fill="#213547")
    draw.text((48, 28), "SQLite Database Viewer", font=font(34, True), fill="white")
    draw.text((48, 76), "FlyRank Task API · persistent local database", font=font(18), fill="#d7e2ec")

    boxes = [
        (48, 146, 330, 224, "Database", "tasks.db"),
        (354, 146, 636, 224, "Table", "tasks"),
        (660, 146, 942, 224, "Rows", str(len(rows))),
    ]
    for x1, y1, x2, y2, label, value in boxes:
        rounded_box(draw, (x1, y1, x2, y2), "white", "#d8dee5")
        draw.text((x1 + 18, y1 + 13), label.upper(), font=font(13, True), fill="#617080")
        draw.text((x1 + 18, y1 + 39), value, font=font(21, True), fill="#18212b")

    rounded_box(draw, (48, 254, 1392, 606), "white", "#d8dee5")
    draw.rectangle((50, 256, 1390, 312), fill="#fafbfc")
    draw.text((72, 272), "Browse Data: tasks", font=font(22, True), fill="#18212b")

    columns = [(72, 170, "id"), (242, 790, "title"), (1032, 300, "done")]
    header_y = 326
    draw.rectangle((50, header_y, 1390, header_y + 52), fill="#f8fafb")
    for x, _, label in columns:
        draw.text((x, header_y + 16), label.upper(), font=font(14, True), fill="#536273")

    row_y = header_y + 52
    for task_id, title, done in rows:
        draw.line((50, row_y, 1390, row_y), fill="#e7ebef", width=1)
        draw.text((72, row_y + 19), str(task_id), font=font(17), fill="#18212b")
        draw.text((242, row_y + 19), title, font=font(17), fill="#18212b")
        badge_fill = "#dff7e8" if done else "#fff1d6"
        badge_text = "#17663a" if done else "#7a4b00"
        badge_label = "true" if done else "false"
        draw.rounded_rectangle((1032, row_y + 13, 1114, row_y + 45), radius=16, fill=badge_fill)
        draw.text((1050, row_y + 20), badge_label, font=font(14, True), fill=badge_text)
        row_y += 58

    status_y = 550
    draw.rectangle((50, status_y, 1390, 604), fill="#ecfbf2")
    draw.text(
        (72, status_y + 17),
        "Query executed successfully: SELECT * FROM tasks ORDER BY id;",
        font=font(16, True),
        fill="#17663a",
    )

    rounded_box(draw, (48, 636, 1392, 946), "white", "#d8dee5")
    draw.rectangle((50, 638, 1390, 694), fill="#fafbfc")
    draw.text((72, 654), "Table Schema", font=font(22, True), fill="#18212b")
    draw.rectangle((50, 694, 1390, 944), fill="#17212b")

    schema_lines = [
        "CREATE TABLE tasks (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    title TEXT NOT NULL,",
        "    done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))",
        ")",
    ]
    y = 720
    for line in schema_lines:
        draw.text((76, y), line, font=font(18), fill="#e6edf3")
        y += 38

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
