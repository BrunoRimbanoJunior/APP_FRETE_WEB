# fretes_web (starter)

## Passos rápidos

1. Crie um ambiente e instale dependências:
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Migrações e superusuário:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. Rodar:
   ```bash
   python manage.py runserver
   ```

4. Acesse:
   - `http://127.0.0.1:8000/fretes/calcular/`
   - `http://127.0.0.1:8000/admin/`

5. Backup do banco de dados:
```bash
pg_dump -U $POSTGRES_USER -d $POSTGRES_DB -F c -f /var/lib/postgresql/data/backup_$(date+%F_%H%M).dump
```

No Admin, cadastre **Transportadoras** e a **Tabela de Frete** (inline). Cadastre **Pedidos** e seus **Volumes**.
Depois, use a página **Calcular** para gerar e salvar cálculos. Use **Relatórios** para filtrar e exportar Excel.
**Garantias** para cadastro de nostas recebidas, itens, valores, observações e status de andamento.

## Docker (dev) — Restauração rápida de backup

Backups gerados pelo serviço `auto-backup` ficam em `./backups` (mapeado para `/backups`).

- Subir serviços (inclui auto-backup):

  ```bash
  docker compose up -d db web nginx auto-backup
  ```

- Restaurar o dump mais recente usando o próprio container do DB:

  ```bash
  docker compose exec db sh -lc '/usr/local/bin/backup_restore.sh'
  ```

- Restaurar um arquivo específico:

  ```bash
  docker compose exec db sh -lc '/usr/local/bin/backup_restore.sh /backups/backup_fretes_db_YYYY-MM-DD_HH-MM.dump'
  ```

- Alternativa com cliente efêmero (`dbtools`):

  ```bash
  docker compose run --rm dbtools sh -lc 'apk add --no-cache postgresql$PG_CLIENT_MAJOR-client && backup_restore.sh'
  # ou um arquivo específico
  docker compose run --rm dbtools sh -lc 'apk add --no-cache postgresql$PG_CLIENT_MAJOR-client && backup_restore.sh /backups/backup_fretes_db_YYYY-MM-DD_HH-MM.dump'
  ```

- Depois da restauração, aplique migrações se preciso:

  ```bash
  docker compose exec web python manage.py migrate
  ```

## Padrão de imagens estáticas
- Use sempre extensões minúsculas: `.png`, `.jpg`, `.jpeg`, `.svg`, `.gif`, `.webp`.
- Evite arquivos duplicados que diferem só por maiúsculas/minúsculas.
- O CI (workflow “Lint Static Assets”) falha o PR/push caso encontre extensões em maiúsculas ou duplicatas por case.

## COMANDOS DOCKER
# Backup antes da atualização
docker compose exec -T auto-backup /usr/local/bin/backup.sh

# Atualizar imagens externas
docker compose pull db nginx auto-backup

# Reconstruir a imagem Django usando a base mais recente
docker compose build --pull web

# Recriar e iniciar os serviços
docker compose up -d --remove-orphans db web nginx auto-backup

# Conferir o estado
docker compose ps
docker compose logs --tail 100 web