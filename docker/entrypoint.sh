#!/usr/bin/env sh
set -e

# -------- Espera pelo Postgres (sem depender de bash/nc/pg_isready) --------
: "${POSTGRES_HOST:=db}"
: "${POSTGRES_PORT:=5432}"

echo "Aguardando banco de dados (TCP ${POSTGRES_PORT} em '${POSTGRES_HOST}')..."
TRIES=60
i=1
while [ $i -le $TRIES ]; do
  python - <<PY 2>/dev/null
import socket, os, sys
host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
try:
    with socket.create_connection((host, port), timeout=2):
        pass
except Exception:
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    break
  fi
  sleep 2
  i=$((i+1))
done

# -------- Prints de diagnóstico (como no seu script) --------
python - <<'PY'
import sys
print("PYTHON:", sys.executable)
try:
    import django
    print("DJANGO:", django.get_version())
except Exception as e:
    print("DJANGO: NÃO ENCONTRADO:", e)
    raise
PY

# -------- Django: migrate e collectstatic (podem ser desativados por env) --------
: "${RUN_MIGRATIONS:=1}"
: "${RUN_COLLECTSTATIC:=1}"
if [ "$RUN_MIGRATIONS" = "1" ]; then
  python manage.py migrate --noinput
else
  echo "[entrypoint] RUN_MIGRATIONS=0 — pulando migrate"
fi
if [ "$RUN_COLLECTSTATIC" = "1" ]; then
  python manage.py collectstatic --noinput
else
  echo "[entrypoint] RUN_COLLECTSTATIC=0 — pulando collectstatic"
fi

# -------- Sobe o Gunicorn --------
exec gunicorn fretes_web.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}"
