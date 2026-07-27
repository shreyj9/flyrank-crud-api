#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://localhost:8000/docs}"
OUTPUT="${2:-docs/swagger-ui.png}"

if command -v chromium >/dev/null 2>&1; then
  BROWSER="$(command -v chromium)"
elif command -v google-chrome >/dev/null 2>&1; then
  BROWSER="$(command -v google-chrome)"
elif [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  BROWSER="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
  echo "Chrome or Chromium was not found. Open $URL and take a screenshot manually."
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"
"$BROWSER" --headless --disable-gpu --hide-scrollbars \
  --window-size=1440,1200 --virtual-time-budget=8000 \
  --screenshot="$OUTPUT" "$URL"

echo "Saved Swagger screenshot to $OUTPUT"
