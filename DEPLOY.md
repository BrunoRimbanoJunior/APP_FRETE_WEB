# Deploy em produção — Docker Compose e Portainer

O app é Django/Gunicorn com PostgreSQL 16 e Nginx. O acesso à intranet permanece
HTTP na porta 8082. A stack de backup continua separada.

## Release atual

A versão está em `VERSION`: **v2026.10.07-1**. O Git registra código, lockfile,
Dockerfiles e configuração. As imagens compiladas são publicadas no GHCR:

- `ghcr.io/brunorimbanojunior/app_frete_web:v2026.10.07-1`
- `ghcr.io/brunorimbanojunior/app_frete_web-nginx:v2026.10.07-1`

O CI executa testes de funcionalidade, navegador e proxy antes de publicar as
duas imagens. Também publica tags do SHA do commit, da branch e `latest`.
Produção usa a versão explícita por padrão; `APP_IMAGE_TAG` permite selecionar
outra versão. Mantenha app e Nginx na mesma versão.

As bases Python 3.13.16 e Nginx 1.31.3 estão fixadas por digest. As dependências
Python estão no `uv.lock` e são instaladas com hashes de `requirements.txt`.
Os estáticos são coletados pelo entrypoint antes de iniciar o Gunicorn.

## Antes de atualizar a stack existente

Confira que o workflow CI/CD terminou com sucesso para o commit do release e
que as duas imagens estão disponíveis. Registre as tags/digests atuais para
rollback e gere um backup do banco em produção.

Preserve o nome atual da stack/projeto Compose e os volumes PostgreSQL existentes.
O nome do projeto participa do nome dos volumes; mudar o nome pode iniciar um banco
vazio em um volume novo. O backup restaurado e as credenciais da validação local
não fazem parte do release.

Variáveis existentes a manter: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_HOST=db`, `POSTGRES_PORT=5432`, `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS` e
`DJANGO_CSRF_TRUSTED_ORIGINS`/`CSRF_TRUSTED_ORIGINS`.
Em HTTP, mantenha `CSRF_COOKIE_SECURE=0` e `SESSION_COOKIE_SECURE=0`.
Use `DJANGO_DEBUG=0`. Não versione `.env.prod` ou credenciais.

## Portainer

1. Atualize a stack existente com `deploy/docker-compose.prod.yml` deste release.
2. Nas variáveis da stack, defina `APP_IMAGE_TAG=v2026.10.07-1`, mantendo as demais.
3. Faça pull das duas imagens e atualize a stack preservando banco, rede e volumes.
4. Confira os logs do web, saúde do Nginx e as verificações funcionais abaixo.

O Compose conserva o build local do Nginx como alternativa, mas a publicação no
GHCR permite atualizar o proxy sem compilar no servidor. Para imagens privadas,
a autenticação no GHCR deve existir no servidor/Portainer.

## Servidor com checkout Git e Docker Compose

Execute no diretório do projeto e use o nome real da stack já existente.
O exemplo abaixo usa `.env.prod` como arquivo local de variáveis:

```bash
export COMPOSE_PROJECT_NAME=nome_atual_da_stack
export APP_IMAGE_TAG=v2026.10.07-1

git pull --ff-only origin hotfix/principal
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml config --quiet
```

Gere um dump antes de atualizar. O arquivo vai para `/tmp` do DB porque a montagem
`/backups` dessa stack é somente leitura. Copie-o para uma pasta de backup do servidor:

```bash
mkdir -p backups
backup_file="pre-deploy-$(date +%Y%m%dT%H%M%S).dump"
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/pre-deploy.dump'
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml exec -T db sh -lc 'pg_restore -l /tmp/pre-deploy.dump > /dev/null'
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml cp db:/tmp/pre-deploy.dump "backups/$backup_file"
```

Baixe as duas imagens, confira a configuração do proxy e atualize somente web/Nginx:

```bash
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml pull web nginx
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml run --rm --no-deps nginx nginx -t
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml up -d --no-deps --wait web nginx
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml ps
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml logs --tail 100 web nginx
```

O entrypoint do web aguarda PostgreSQL, aplica migrações, coleta estáticos e inicia
Gunicorn. Não existem serviços `migrate`/`collectstatic` ou perfil `ops` neste Compose.
O release atual não adiciona migrações. A recriação do único web pode causar uma
breve indisponibilidade; o Nginx acompanha automaticamente a mudança de IP.

Para compilar o Nginx diretamente no servidor como alternativa ao pull:

```bash
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml build nginx
```

## Validação depois do deploy

- `/` deve redirecionar para `/fretes/`, preservando a porta 8082.
- Login, pedidos, clientes, produtos, garantias e relatórios devem abrir normalmente.
- Confira buscas HTMX, menus no celular e exportações PDF/Excel autenticadas.
- Importações de clientes/produtos aceitam até 20 MiB de corpo HTTP, incluindo multipart.
  As demais rotas mantêm 1 MiB. Permissões e validações continuam no Django.
- `/nginx-health` deve retornar `ok`. Esse endpoint verifica apenas o Nginx;
  confira o web pelos logs e por uma requisição real ao app.
- Os logs de acesso são JSON com tempos total/do upstream, sem parâmetros de URL ou cookies.

## Rollback

Selecione a versão anterior registrada antes do deploy usando `APP_IMAGE_TAG`,
faça pull e recrie apenas web/Nginx. Se a versão anterior ainda não possui uma
imagem Nginx no GHCR, use a imagem/configuração do proxy que estava em execução.
Não remova volumes para reverter uma atualização do app.

## Backup e restauração

O agendamento está em `deploy/docker-compose.backup.yml`. Essa stack usa os nomes
externos de rede e volume do app; mantenha os nomes reais da implantação.
Os scripts `deploy/db-tools/backup_restore.sh` e `deploy/auto-backup/backup.sh`
continuam disponíveis. Uma restauração de banco é uma operação separada do deploy.

## Validação local

`docker-compose.validation.yml` usa porta 8083 e banco/volume próprios. O script
`scripts/validate_nginx.py` testa o proxy real somente no banco `validation`
com `VALIDATION_ONLY=1`; consulte o README. Credenciais e relatórios locais ficam
em `validation-artifacts/`, que é ignorado pelo Git e pelo build.
