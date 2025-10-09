FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl dos2unix \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
COPY docker/entrypoint.sh /entrypoint.sh
# Normaliza nome da logo para minúsculo (evita .PNG em produção)
RUN sh -lc 'set -e; d=/app/static/img; if [ -d "$d" ]; then if [ -f "$d/logo.PNG" ] && [ ! -f "$d/logo.png" ]; then mv "$d/logo.PNG" "$d/logo.png"; fi; fi'
# Normaliza fim de linha (CRLF -> LF) para evitar erro no Windows
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
