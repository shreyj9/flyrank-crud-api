#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
TEST_EMAIL="${TEST_EMAIL:-flyrank-auth-$(date +%s)@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-FlyRankTest123!}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

request() {
  local name="$1"
  local expected="$2"
  shift 2
  local body_file="$TMP_DIR/${name}.json"
  local actual
  actual="$(curl -sS -o "$body_file" -w '%{http_code}' "$@")"
  printf '%-32s expected=%s actual=%s\n' "$name" "$expected" "$actual"
  if [[ "$actual" != "$expected" ]]; then
    cat "$body_file"
    echo
    exit 1
  fi
}

request public-info 200 "$BASE_URL/public/info"
request missing-token 401 "$BASE_URL/protected/profile"
request missing-signup-input 400 \
  -X POST "$BASE_URL/auth/signup" \
  -H 'Content-Type: application/json' \
  -d '{}'
request signup 201 \
  -X POST "$BASE_URL/auth/signup" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}"
request login 200 \
  -X POST "$BASE_URL/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}"

ACCESS_TOKEN="$(python3 - "$TMP_DIR/login.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding='utf-8') as handle:
    print(json.load(handle)['access_token'])
PY
)"

request profile-valid 200 \
  "$BASE_URL/protected/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
request dashboard-valid 200 \
  "$BASE_URL/protected/dashboard" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

TAMPERED_TOKEN="$(python3 - "$ACCESS_TOKEN" <<'PYTOKEN'
import sys

token = sys.argv[1]
parts = token.split(".")
if len(parts) != 3 or not parts[2]:
    raise SystemExit("Unexpected JWT format")

signature = parts[2]
index = len(signature) // 2
replacement = "A" if signature[index] != "A" else "B"
parts[2] = signature[:index] + replacement + signature[index + 1:]

print(".".join(parts))
PYTOKEN
)"
request profile-tampered 401 \
  "$BASE_URL/protected/profile" \
  -H "Authorization: Bearer $TAMPERED_TOKEN"
request logout 204 \
  -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

echo "All Supabase authentication checks passed."
echo "Test account: $TEST_EMAIL"
