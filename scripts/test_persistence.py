"""Prove that Postgres rows survive a full Docker Compose restart."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
PROOF_PATH = PROJECT_ROOT / "docs" / "persistence-proof.txt"


def compose(*arguments: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *arguments],
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def request_json(method: str, url: str, payload: dict[str, object] | None = None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        content = response.read()
        return response.status, json.loads(content) if content else None


def wait_for_api(base_url: str, timeout_seconds: int = 90) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            status, payload = request_json("GET", f"{base_url}/health")
            if status == 200 and payload == {"status": "ok"}:
                return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(2)
    compose("logs", capture_output=False)
    raise RuntimeError("API did not become healthy before the timeout")


def main() -> None:
    if not ENV_PATH.exists():
        raise SystemExit("Missing .env. Run: cp .env.example .env")

    values = dotenv_values(ENV_PATH)
    api_port = values.get("API_PORT") or "8000"
    base_url = f"http://localhost:{api_port}"
    proof_title = f"Persistence proof {datetime.now(timezone.utc).isoformat()}"

    compose("up", "-d", "--build")
    wait_for_api(base_url)

    create_status, created = request_json(
        "POST",
        f"{base_url}/tasks",
        {"title": proof_title},
    )
    if create_status != 201 or not isinstance(created, dict):
        raise RuntimeError(f"Unexpected create response: {create_status} {created}")
    task_id = int(created["id"])

    compose("down")
    compose("up", "-d")
    wait_for_api(base_url)

    get_status, reloaded = request_json("GET", f"{base_url}/tasks/{task_id}")
    if get_status != 200 or not isinstance(reloaded, dict):
        raise RuntimeError(f"Task {task_id} was missing after restart")
    if reloaded.get("title") != proof_title:
        raise RuntimeError("Reloaded task did not match the created task")

    db_rows = compose(
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        values.get("POSTGRES_USER") or "taskuser",
        "-d",
        values.get("POSTGRES_DB") or "tasks",
        "-c",
        "SELECT id, title, done FROM tasks ORDER BY id;",
        capture_output=True,
    ).stdout

    PROOF_PATH.write_text(
        "\n".join(
            [
                "FlyRank BE-04 Postgres persistence proof",
                f"Verified at: {datetime.now(timezone.utc).isoformat()}",
                f"Created task id: {task_id}",
                f"Created title: {proof_title}",
                "Restart performed with: docker compose down && docker compose up -d",
                "Result: task remained available after the app and DB containers restarted.",
                "",
                "Postgres rows after restart:",
                db_rows.rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("Persistence check passed: the Postgres row survived docker compose down/up.")
    print(f"Proof written to {PROOF_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
