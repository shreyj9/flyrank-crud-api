#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"

check() {
  local expected="$1"; shift
  local actual
  actual=$(curl -s -o /tmp/flyrank-response -w '%{http_code}' "$@")
  printf '%-45s expected=%s actual=%s\n' "$*" "$expected" "$actual"
  test "$actual" = "$expected"
}

check 200 "$BASE_URL/"
check 200 "$BASE_URL/health"
check 200 "$BASE_URL/tasks"
check 200 "$BASE_URL/tasks/1"
check 404 "$BASE_URL/tasks/99"
check 201 -X POST "$BASE_URL/tasks" -H 'Content-Type: application/json' -d '{"title":"Buy milk"}'
check 400 -X POST "$BASE_URL/tasks" -H 'Content-Type: application/json' -d '{}'
check 200 -X PUT "$BASE_URL/tasks/4" -H 'Content-Type: application/json' -d '{"title":"Buy oat milk","done":true}'
check 400 -X PUT "$BASE_URL/tasks/4" -H 'Content-Type: application/json' -d '{}'
check 204 -X DELETE "$BASE_URL/tasks/4"
check 404 "$BASE_URL/tasks/4"

echo "All CRUD checks passed."
