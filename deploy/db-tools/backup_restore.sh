#!/bin/sh
set -eu

# Restore a PostgreSQL custom-format dump (.dump)
# Usage:
#   backup_restore.sh [PATH_TO_DUMP] [--drop|--no-drop]
# Behavior:
#   - If PATH_TO_DUMP is omitted, picks the most recent /backups/*.dump
#   - By default drops and recreates the target DB before restore (use --no-drop to skip)

DB_NAME=${POSTGRES_DB:-fretes}
DB_USER=${POSTGRES_USER:-fretes}
DB_HOST=${POSTGRES_HOST:-127.0.0.1}
DB_PORT=${POSTGRES_PORT:-5432}

# Ensure non-interactive auth if POSTGRES_PASSWORD is provided
if [ "${POSTGRES_PASSWORD:-}" != "" ]; then
  export PGPASSWORD="${POSTGRES_PASSWORD}"
fi

FILE=""
DROP_FIRST=1

case "${1:-}" in
  ""|--*) ;;
  *) FILE="$1"; shift || true ;;
esac

while [ $# -gt 0 ]; do
  case "$1" in
    --drop) DROP_FIRST=1 ;;
    --no-drop) DROP_FIRST=0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

# Locate latest dump if not provided
if [ -z "$FILE" ]; then
  if ls /backups/*.dump >/dev/null 2>&1; then
    FILE=$(ls -1t /backups/*.dump | head -n1)
  else
    echo "No dump files found in /backups" >&2
    exit 1
  fi
fi

if [ ! -f "$FILE" ]; then
  echo "Dump file not found: $FILE" >&2
  exit 1
fi

echo "Restoring from: $FILE"
psql_conn="-h $DB_HOST -p $DB_PORT -U $DB_USER"

if [ "$DROP_FIRST" = "1" ]; then
  echo "Dropping and recreating database: $DB_NAME"
  dropdb $psql_conn --force --if-exists "$DB_NAME" || true
  createdb $psql_conn "$DB_NAME"
fi

echo "Running pg_restore into $DB_NAME ..."
pg_restore $psql_conn -d "$DB_NAME" --clean --if-exists --no-owner "$FILE"
echo "Restore completed."

