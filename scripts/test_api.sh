#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
RESPONSE_FILE="$(mktemp)"
trap 'rm -f "$RESPONSE_FILE"' EXIT

check() {
  local expected="$1"
  shift
  local actual
  actual=$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' "$@")
  printf '%-62s expected=%s actual=%s\n' "$*" "$expected" "$actual"
  if [[ "$actual" != "$expected" ]]; then
    cat "$RESPONSE_FILE"
    exit 1
  fi
}

check 200 "$BASE_URL/"
check 200 "$BASE_URL/health"
check 200 "$BASE_URL/tasks"
check 200 "$BASE_URL/tasks/1"
check 404 "$BASE_URL/tasks/999999"

check 201 -X POST "$BASE_URL/tasks" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Buy milk"}'
CREATED_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' < "$RESPONSE_FILE")

check 400 -X POST "$BASE_URL/tasks" \
  -H 'Content-Type: application/json' \
  -d '{}'

check 200 -X PUT "$BASE_URL/tasks/$CREATED_ID" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Buy oat milk","done":true}'

check 400 -X PUT "$BASE_URL/tasks/$CREATED_ID" \
  -H 'Content-Type: application/json' \
  -d '{}'

check 204 -X DELETE "$BASE_URL/tasks/$CREATED_ID"
check 404 "$BASE_URL/tasks/$CREATED_ID"

echo "All CRUD checks passed."
