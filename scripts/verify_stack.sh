#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env. Creating it from .env.example for local development."
  cp .env.example .env
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or is not on PATH." >&2
  exit 1
fi

source .venv/bin/activate 2>/dev/null || true

docker compose up -d --build

API_PORT="$(awk -F= '$1 == "API_PORT" {print $2}' .env | tail -n1)"
API_PORT="${API_PORT:-8000}"
BASE_URL="http://localhost:${API_PORT}"

for _ in {1..45}; do
  if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

curl -fsS "$BASE_URL/health" >/dev/null
BASE_URL="$BASE_URL" ./scripts/test_api.sh
python3 scripts/test_persistence.py
python3 scripts/capture_postgres_evidence.py

echo
echo "BE-04 verification passed."
echo "Generated docs/persistence-proof.txt and docs/postgres-database.png."
