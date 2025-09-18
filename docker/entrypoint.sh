#!/usr/bin/env bash
set -e

# garanta que estamos usando a venv
export VIRTUAL_ENV="/app/.venv"
export PATH="/app/.venv/bin:$PATH"

echo "Aguardando banco de dados (TCP 5432 em 'db')..."
for i in {1..60}; do
  (echo > /dev/tcp/db/5432) >/dev/null 2>&1 && break
  sleep 2
done

python -c "import sys; print('PYTHON:', sys.executable)"
python -c "import django; print('DJANGO:', django.get_version())" || { echo 'Django não instalado?'; exit 1; }

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn fretes_web.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout ${GUNICORN_TIMEOUT:-60}
