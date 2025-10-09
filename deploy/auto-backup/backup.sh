#!/bin/sh
set -e

echo "[ $(date) ] - Iniciando o backup..."

# Falha cedo se variáveis não estiverem definidas
: "${POSTGRES_HOST:?POSTGRES_HOST não definido}"
: "${POSTGRES_USER:?POSTGRES_USER não definido}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD não definido}"
: "${POSTGRES_DB:?POSTGRES_DB não definido}"

DUMP_FILE=/backups/backup_fretes_db_$(date +"%Y-%m-%d_%H-%M").dump
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --format=c --compress=9 > "$DUMP_FILE"

echo "[ $(date) ] - Backup concluido: $DUMP_FILE"

# Remove backups com mais de 7 dias
find /backups -name '*.dump' -mtime +7 -delete

