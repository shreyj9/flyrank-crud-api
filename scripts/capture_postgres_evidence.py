"""Capture real Docker/Postgres output as text and a PNG for the README."""

from __future__ import annotations

import subprocess
from pathlib import Path

from dotenv import dotenv_values
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
TEXT_PATH = PROJECT_ROOT / "docs" / "postgres-database.txt"
IMAGE_PATH = PROJECT_ROOT / "docs" / "postgres-database.png"


def run(*arguments: str) -> str:
    return subprocess.run(
        list(arguments),
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.rstrip()


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def main() -> None:
    if not ENV_PATH.exists():
        raise SystemExit("Missing .env. Run: cp .env.example .env")

    values = dotenv_values(ENV_PATH)
    user = values.get("POSTGRES_USER") or "taskuser"
    database = values.get("POSTGRES_DB") or "tasks"

    compose_status = run("docker", "compose", "ps")
    database_output = run(
        "docker",
        "compose",
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        user,
        "-d",
        database,
        "-c",
        "\\dt",
        "-c",
        "SELECT id, title, done FROM tasks ORDER BY id;",
    )

    evidence = "\n".join(
        [
            "$ docker compose ps",
            compose_status,
            "",
            "$ docker compose exec -T db psql -U <user> -d <database> -c '\\dt' -c 'SELECT id, title, done FROM tasks ORDER BY id;'",
            database_output,
            "",
        ]
    )
    TEXT_PATH.write_text(evidence, encoding="utf-8")

    lines = evidence.splitlines() or [""]
    font = load_font(18)
    padding = 28
    line_spacing = 8

    probe = Image.new("RGB", (10, 10))
    probe_draw = ImageDraw.Draw(probe)
    measurements = [probe_draw.textbbox((0, 0), line, font=font) for line in lines]
    max_width = max((box[2] - box[0] for box in measurements), default=800)
    line_height = max((box[3] - box[1] for box in measurements), default=20)

    width = max(1100, max_width + padding * 2)
    height = padding * 2 + len(lines) * (line_height + line_spacing)
    image = Image.new("RGB", (width, height), "#111827")
    draw = ImageDraw.Draw(image)

    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill="#E5E7EB")
        y += line_height + line_spacing

    image.save(IMAGE_PATH)
    print(f"Saved {TEXT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Saved {IMAGE_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
