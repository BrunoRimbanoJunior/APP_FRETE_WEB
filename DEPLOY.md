Deploy em ProduÃ§Ã£o (Docker Compose + Portainer)

Este guia descreve o fluxo recomendado para publicar novas versÃµes em produÃ§Ã£o, incluindo backup do banco, validaÃ§Ãµes e rollback.

1) VisÃ£o Geral
- App: Django + Gunicorn
- Banco: Postgres
- OrquestraÃ§Ã£o: deploy/docker-compose.prod.yml
- Imagens: publicadas via GitHub Actions em ghcr.io/<org>/app_frete_web:<tag>

2) PrÃ©â€‘requisitos
- Acesso ao host/Portainer onde roda o stack de produÃ§Ã£o
- VariÃ¡veis de ambiente definidas (no Portainer/stack ou .env.prod):
  - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
  - DJANGO_SECRET_KEY, DJANGO_DEBUG=0, DJANGO_SETTINGS_MODULE=fretes_web.settings.prod
  - DJANGO_CSRF_TRUSTED_ORIGINS e/ou CSRF_TRUSTED_ORIGINS
  - TZ (ex.: America/Sao_Paulo — usado pelo auto-backup)
- ServiÃ§o web do compose de prod usa comando que executa migrate e collectstatic antes do Gunicorn

3) Versionamento da Imagem
Evite latest em produÃ§Ã£o. Prefira tags versionadas (ex.: vYYYY-MM-DD-n). Altere a linha image: do serviÃ§o web no deploy/docker-compose.prod.yml para a tag desejada.

4) Backup do Banco (antes do deploy)
Crie um dump dentro do container do Postgres:

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -f /var/lib/postgresql/data/backup_$(date +%F_%H%M).dump'

Opcional: copie o arquivo do container para o host (troque <db-container> pelo nome real obtido com docker ps/docker compose ps):

docker cp <db-container>:/var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump ./backup_YYYY-MM-DD_HHMM.dump

4.1) Verificar o Backup
- Listar conteÃºdo do arquivo (sem restaurar):

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_restore -l /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump | head -n 40'

- Teste de integridade (dryâ€‘run de catÃ¡logo):

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_restore -l /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump > /dev/null'

- RestauraÃ§Ã£o em um banco temporÃ¡rio e checagem:

createdb -U "$POSTGRES_USER" tmp_restore
pg_restore -U "$POSTGRES_USER" -d tmp_restore -c /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump
psql -U "$POSTGRES_USER" -d tmp_restore -c "\\dt"
psql -U "$POSTGRES_USER" -d tmp_restore -c "select count(*) from django_migrations;"
dropdb -U "$POSTGRES_USER" tmp_restore

5) Validar MigraÃ§Ãµes (opcional)
Listar migraÃ§Ãµes reconhecidas pela aplicaÃ§Ã£o:

docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py showmigrations

Ver o plano (Django 5.0+):

docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py migrate --plan

6) Atualizar Imagem e Aplicar Deploy (otimizado)
- Baixar a nova imagem:

docker compose -f deploy/docker-compose.prod.yml pull web

- Rodar migrações (one‑off):

docker compose -f deploy/docker-compose.prod.yml run --rm --profile ops migrate

- Coletar estáticos (one‑off):

docker compose -f deploy/docker-compose.prod.yml run --rm --profile ops collectstatic

- Subir somente o web (inicia direto o Gunicorn):

docker compose -f deploy/docker-compose.prod.yml up -d web

- Acompanhar logs e aguardar o Gunicorn subir:

docker compose -f deploy/docker-compose.prod.yml logs -f web

7) Smoke Test PÃ³sâ€‘Deploy
- /fretes/ â€“ home
- /fretes/pedidos/ â€“ listar e filtrar
- /fretes/garantias/ â€“ filtros e exportaÃ§Ãµes (PDF/Excel)
- (se staff) /fretes/admin/tools/importar-produtos/ e /fretes/admin/tools/importar-clientes/

8) Rollback
- Com tag: mude image: para a tag anterior, depois:

docker compose -f deploy/docker-compose.prod.yml pull web && docker compose -f deploy/docker-compose.prod.yml up -d web

- Se precisar restaurar o banco:

docker compose -f deploy/docker-compose.prod.yml exec db sh -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c /var/lib/postgresql/data/backup_YYYY-MM-DD_HHMM.dump'

9) Dicas e SoluÃ§Ã£o de Problemas
- 502/Bad Gateway logo apÃ³s o deploy geralmente Ã© o web subindo; aguarde alguns segundos.
- Verifique db (health=healthy) e logs do web.
- Problemas de sessÃ£o/CSRF em HTTPS: alinhe DJANGO_CSRF_TRUSTED_ORIGINS/CSRF_TRUSTED_ORIGINS e flags de cookies.
- Em caso de erro em migraÃ§Ã£o, rode manualmente para ver a mensagem completa:

docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py migrate --noinput -v 3

10) Pipeline CI/CD
- Cada push na branch configurada dispara o workflow (.github/workflows/ci-cd.yml).
- Verifique no GitHub Actions se a imagem foi construÃ­da e publicada.
- Use a tag gerada no deploy/docker-compose.prod.yml (ou mantenha latest se preferir, embora nÃ£o recomendado).




11) Auto-backup em Produção
- O serviço `auto-backup` está no compose de prod e:
  - Executa `pg_dump` às 04:00 e 16:00 (fuso `TZ`).
  - Salva em `/backups` no volume nomeado `pgbackups`.
  - Remove dumps com mais de 7 dias.

- Checar logs:

  docker compose -f deploy/docker-compose.prod.yml logs -f auto-backup

- Listar dumps:

  docker compose -f deploy/docker-compose.prod.yml exec auto-backup sh -lc 'ls -lh /backups | tail -n +1'

- Restaurar o último dump (sem prompt de senha):

  docker compose -f deploy/docker-compose.prod.yml exec auto-backup sh -lc 'set -e; export PGPASSWORD="$POSTGRES_PASSWORD"; LATEST=$(ls -1t /backups/*.dump | head -n1); echo "Restaurando: $LATEST"; dropdb -h "$POSTGRES_HOST" -U "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB"; createdb -h "$POSTGRES_HOST" -U "$POSTGRES_USER" "$POSTGRES_DB"; pg_restore -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --clean --if-exists "$LATEST"'

- Para manter cópias no host, mapeie `pgbackups` para um caminho do host via Portainer/bind, conforme sua política de retenção.


12) Restauração rápida pelo container do DB
- O serviço `db` monta:
  - `pgbackups` em `/backups` (somente leitura)
  - script `/usr/local/bin/backup_restore.sh`

- Restaurar o dump mais recente (com drop e recreate):

  docker compose -f deploy/docker-compose.prod.yml exec db sh -lc '/usr/local/bin/backup_restore.sh'

- Restaurar um arquivo específico:

  docker compose -f deploy/docker-compose.prod.yml exec db sh -lc '/usr/local/bin/backup_restore.sh /backups/backup_fretes_db_YYYY-MM-DD_HH-MM.dump'

- Restaurar sem dropar o banco antes:

  docker compose -f deploy/docker-compose.prod.yml exec db sh -lc '/usr/local/bin/backup_restore.sh --no-drop'

12) Restauração rápida pelo container do DB (alternativas)
- Usar o container do DB (exec):

  docker compose -f deploy/docker-compose.prod.yml exec db sh -lc '/usr/local/bin/backup_restore.sh'

- Usar um cliente efêmero (run dbtools):
  (instala client e executa o script contra o serviço `db` pela rede Compose)

  docker compose -f deploy/docker-compose.prod.yml run --rm dbtools sh -lc 'apk add --no-cache postgresql$PG_CLIENT_MAJOR-client && backup_restore.sh'

- Restaurar arquivo específico:

  docker compose -f deploy/docker-compose.prod.yml exec db sh -lc '/usr/local/bin/backup_restore.sh /backups/backup_fretes_db_YYYY-MM-DD_HH-MM.dump'

  # ou com dbtools efêmero
  docker compose -f deploy/docker-compose.prod.yml run --rm dbtools sh -lc 'apk add --no-cache postgresql$PG_CLIENT_MAJOR-client && backup_restore.sh /backups/backup_fretes_db_YYYY-MM-DD_HH-MM.dump'
