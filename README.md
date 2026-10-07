# fretes_web (starter)

## Release para producao

Versao atual: **v2026.10.07-1**, registrada em `VERSION`.
O CI publica app e Nginx no GHCR depois dos testes:

- `ghcr.io/brunorimbanojunior/app_frete_web:v2026.10.07-1`
- `ghcr.io/brunorimbanojunior/app_frete_web-nginx:v2026.10.07-1`

O Compose de producao usa essa versao para as duas imagens. `APP_IMAGE_TAG`
permite selecionar outro release. Para deploy/backup/rollback da stack existente,
siga [DEPLOY.md](DEPLOY.md). As imagens Docker ficam no registry; o Git recebe
codigo, Dockerfiles, lockfile e configuracoes. Backups e credenciais locais sao ignorados.

## Passos rápidos

1. Crie um ambiente e instale dependências:
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --require-hashes -r requirements.txt
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

## Reconstrução Completa
docker compose build --no-cache --pull web
docker compose up -d --remove-orphans db web nginx auto-backup

## Desempenho em dispositivos mobile

- As listagens principais usam paginacao no servidor com 50 registros por pagina.
- As buscas de clientes e produtos em Garantias exigem 2 caracteres e retornam no maximo 20 opcoes.
- O Nginx comprime respostas HTML/CSS/JS e a logo possui uma versao otimizada para exibicao.
- Depois de atualizar, aplique a migracao `0020_performance_indexes` e reconstrua os containers web e nginx.

- A navegação abre por toque e teclado; CONFIG usa um controle nativo acessível.
- As tabelas das listagens viram cartões abaixo de 576 px, com rótulos por campo.
- Pedidos usa o layout compartilhado com viewport, campos de tamanho legível e áreas de toque de 44 px.
- Filtros e buscas ficam em coluna no celular. O autocomplete responde ao evento `input`.
- O cálculo mostra carregamento, bloqueia envio duplicado e permite tentar novamente após erro.
- Bootstrap 5.3.8 e HTMX 2.0.11 são servidos localmente, com hashes de integridade.
- WhiteNoise gera versões gzip e Brotli dos estáticos durante `collectstatic`.

## Dependências e testes

`pyproject.toml` é a fonte das dependências. `uv.lock` fixa também as indiretas.
`requirements.txt` contém somente execução; `requirements-dev.txt` contém pytest
e `requirements-browser.txt` contém Playwright. Os três exports incluem hashes.

Para atualizar uma dependência, altere sua versão no `pyproject.toml`, execute
`uv lock` e regenere os arquivos (uv 0.12.23 usado na atualização):

```bash
uv export --frozen --no-dev --no-emit-project --no-header -o requirements.txt
uv export --frozen --only-group dev --no-emit-project --no-header -o requirements-dev.txt
uv export --frozen --only-group browser --no-emit-project --no-header -o requirements-browser.txt
```

Use PostgreSQL para os testes: a migração histórica `0014` utiliza `BTRIM`.
Defina `DATABASE_URL` apontando para um banco de desenvolvimento isolado,
com permissão de criar o banco temporário de testes. Não use SQLite neste fluxo.

```bash
pip install --require-hashes -r requirements.txt -r requirements-dev.txt -r requirements-browser.txt
python -m playwright install --with-deps chromium
python -m pytest -q fretes/tests
python -m pytest -q browser_tests
```

Os testes de navegador cobrem 320, 375, 768 e 1280 px, menus por toque e teclado,
cadastro de pedidos e garantias, buscas HTMX, cálculos, falhas de requisição,
envio duplicado e paginação preservando filtros. Para capturas locais, defina
`MOBILE_SCREENSHOT_DIR=validation-artifacts/screenshots` antes de executar.
O CI testa antes de publicar a imagem e confere se os exports correspondem ao lockfile.

## Build completo para validação local

O Compose abaixo usa banco e volume próprios e escuta somente em localhost:8083.
As credenciais e opções HTTP deste arquivo são exclusivas dessa validação local.

```bash
docker compose -f docker-compose.validation.yml build --pull web
docker compose -f docker-compose.validation.yml up -d --wait
docker compose -f docker-compose.validation.yml exec -T web python scripts/seed_validation.py
```

Abra `http://127.0.0.1:8083/fretes/`. O script cria dados fictícios e imprime o
usuário `validacao` e uma senha aleatória. Uma nova execução troca essa senha.
Ele recusa execução fora do banco isolado `validation` com `VALIDATION_ONLY=1`.
A imagem gerada tem a tag `app-frete-web:validation-20261007`.

Para parar a validação preservando os dados:

```bash
docker compose -f docker-compose.validation.yml down
```

## Nginx na intranet

O acesso permanece HTTP nas portas 8082 (stack principal) e 8083 (validacao).
Nginx 1.31.3 Alpine esta fixado por versao e digest no Compose e no Dockerfile
de producao. Ao atualizar essa imagem, ajuste os tres locais e valide o proxy.

- O upstream usa o DNS interno do Docker e acompanha mudancas de IP do web,
  sem recarregar o Nginx. Isso nao elimina a indisponibilidade enquanto o unico
  container web esta sendo recriado; alta disponibilidade exige mais instancias.
- As importacoes de produtos e clientes aceitam corpos HTTP de ate 20 MiB,
  incluindo o multipart. As demais rotas mantem 1 MiB. A validacao da planilha
  e as permissoes continuam no Django.
- Os logs de acesso sao JSON, com tempo total e tempo de resposta do upstream.
  Os logs de acesso nao incluem parametros da URL, cookies ou senhas.
- `/nginx-health` verifica o processo HTTP do Nginx; a saude do app e do banco
  deve ser conferida separadamente. Compose e a imagem de producao usam esse healthcheck.
- Os headers de host e protocolo sao definidos pelo proxy, preservando a porta.
  Os redirecionamentos do Nginx sao relativos para manter a porta do Docker.
  Gzip, Brotli e cache dos estaticos continuam ativos.

Para atualizar somente o Nginx principal com a configuracao local:

```bash
docker compose run --rm --no-deps nginx nginx -t
docker compose up -d --no-deps --wait nginx
```

Para repetir a verificacao funcional na instancia isolada, use o arquivo local
de credenciais. O script recusa outros bancos, testa login, telas, filtros,
uploads acima de 1 MiB, bloqueio de uploads excessivos, exportacoes e compressao.
As planilhas de teste nao possuem os cabecalhos obrigatorios e nao alteram cadastros.

```bash
docker compose -f docker-compose.validation.yml cp validation-artifacts/acesso.txt web:/tmp/nginx-access.txt
docker compose -f docker-compose.validation.yml exec -T -e PYTHONPATH=/app -e CHECK_NGINX_HEALTH=1 web python scripts/validate_nginx.py --access-file /tmp/nginx-access.txt
docker compose -f docker-compose.validation.yml exec -T web rm /tmp/nginx-access.txt
```

Com o backup restaurado, use as credenciais de `validation-artifacts/acesso.txt`.
Execute `seed_validation.py` apenas quando quiser adicionar dados ficticios.
O CI tambem constroi e verifica o Nginx em uma instancia descartavel.
