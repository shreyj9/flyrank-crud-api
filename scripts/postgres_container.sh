#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-taskdb}"
VOLUME_NAME="${POSTGRES_VOLUME_NAME:-taskdata}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-tasks}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

usage() {
  cat <<'USAGE'
Usage: ./scripts/postgres_container.sh <start|shell|status|stop|remove>

Before start, set POSTGRES_PASSWORD in your shell. Example:
  POSTGRES_PASSWORD=choose-a-local-password ./scripts/postgres_container.sh start
USAGE
}

command="${1:-}"

case "$command" in
  start)
    : "${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD before starting Postgres}"
    if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
      docker start "$CONTAINER_NAME" >/dev/null
    else
      docker run \
        --name "$CONTAINER_NAME" \
        -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        -e POSTGRES_DB="$POSTGRES_DB" \
        -p "$POSTGRES_PORT:5432" \
        -v "$VOLUME_NAME:/var/lib/postgresql/data" \
        -d postgres:17-alpine >/dev/null
    fi
    docker ps --filter "name=^/${CONTAINER_NAME}$"
    ;;
  shell)
    docker exec -it "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    ;;
  status)
    docker ps -a --filter "name=^/${CONTAINER_NAME}$"
    ;;
  stop)
    docker stop "$CONTAINER_NAME"
    ;;
  remove)
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    echo "Container removed. Named volume '$VOLUME_NAME' was kept."
    ;;
  *)
    usage
    exit 1
    ;;
esac
