Deploy em Produção (Docker Compose + Portainer)

Este guia descreve o fluxo recomendado para publicar novas versões em produção, incluindo backup do banco, validações e rollback.

1) Visão Geral
- App: Django + Gunicorn
- Banco: Postgres
- Orquestração: deploy/docker-compose.prod.yml
- Imagens: publicadas via GitHub Actions em ghcr.io/<org>/app_frete_web:<tag>

2) Pré‑requisitos
- Acesso ao host/Portainer onde roda o stack de produção
- Variáveis de ambiente definidas (no Portainer/stack ou .env.prod):
  - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
  - DJANGO_SECRET_KEY, DJANGO_DEBUG=0, DJANGO_SETTINGS_MODULE=fretes_web.settings.prod
  - DJANGO_CSRF_TRUSTED_ORIGINS e/ou CSRF_TRUSTED_ORIGINS
- Serviço web do compose de prod usa comando que executa migrate e collectstatic antes do Gunicorn

3) Versionamento da Imagem
Evite latest em produção. Prefira tags versionadas (ex.: vYYYY-MM-DD-n). Altere a linha image: do serviço web no deploy/docker-compose.prod.yml para a tag desejada.

4) Backup do Banco (antes do deploy)
Crie um dump dentro do container do Postgres:

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -f /var/lib/postgresql/data/backup_$(date +%F_%H%M).dump'

Opcional: copie o arquivo do container para o host (troque <db-container> pelo nome real obtido com docker ps/docker compose ps):

docker cp <db-container>:/var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump ./backup_YYYY-MM-DD_HHMM.dump

4.1) Verificar o Backup
- Listar conteúdo do arquivo (sem restaurar):

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_restore -l /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump | head -n 40'

- Teste de integridade (dry‑run de catálogo):

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_restore -l /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump > /dev/null'

- Restauração em um banco temporário e checagem:

createdb -U "$POSTGRES_USER" tmp_restore
pg_restore -U "$POSTGRES_USER" -d tmp_restore -c /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump
psql -U "$POSTGRES_USER" -d tmp_restore -c "\\dt"
psql -U "$POSTGRES_USER" -d tmp_restore -c "select count(*) from django_migrations;"
dropdb -U "$POSTGRES_USER" tmp_restore

5) Validar Migrações (opcional)
Listar migrações reconhecidas pela aplicação:

docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py showmigrations

Ver o plano (Django 5.0+):

docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py migrate --plan

6) Atualizar Imagem e Aplicar Deploy
- Baixar a nova imagem:

docker compose -f deploy/docker-compose.prod.yml pull web

- Subir somente o web (recria com a nova imagem):

docker compose -f deploy/docker-compose.prod.yml up -d web

- Acompanhar logs e aguardar “Starting gunicorn …”:

docker compose -f deploy/docker-compose.prod.yml logs -f web

7) Smoke Test Pós‑Deploy
- /fretes/ – home
- /fretes/pedidos/ – listar e filtrar
- /fretes/garantias/ – filtros e exportações (PDF/Excel)
- (se staff) /fretes/admin/tools/importar-produtos/ e /fretes/admin/tools/importar-clientes/

8) Rollback
- Com tag: mude image: para a tag anterior, depois:

docker compose -f deploy/docker-compose.prod.yml pull web && docker compose -f deploy/docker-compose.prod.yml up -d web

- Se precisar restaurar o banco:

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump'

9) Dicas e Solução de Problemas
- 502/Bad Gateway logo após o deploy geralmente é o web subindo; aguarde alguns segundos.
- Verifique db (health=healthy) e logs do web.
- Problemas de sessão/CSRF em HTTPS: alinhe DJANGO_CSRF_TRUSTED_ORIGINS/CSRF_TRUSTED_ORIGINS e flags de cookies.
- Em caso de erro em migração, rode manualmente para ver a mensagem completa:

docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py migrate --noinput -v 3

10) Pipeline CI/CD
- Cada push na branch configurada dispara o workflow (.github/workflows/ci-cd.yml).
- Verifique no GitHub Actions se a imagem foi construída e publicada.
- Use a tag gerada no deploy/docker-compose.prod.yml (ou mantenha latest se preferir, embora não recomendado).

