# Bibliotecas locais

Os arquivos são cópias das distribuições oficiais, com versão fixa. No CSS do
Bootstrap, apenas o comentário `sourceMappingURL` foi removido: esse mapa não é
distribuído no app e a reescrita de sua URL pelo manifest alteraria o hash SRI.
Os templates usam SRI calculado sobre os arquivos locais para conferir os bytes
depois da descompressão HTTP.

| Biblioteca | Origem | Licença |
| --- | --- | --- |
| Bootstrap 5.3.8 (CSS) | https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css | MIT, em `bootstrap/LICENSE` |
| HTMX 2.0.11 (JS minificado) | https://cdn.jsdelivr.net/npm/htmx.org@2.0.11/dist/htmx.min.js | Zero-Clause BSD, em `htmx/LICENSE` |

Ao atualizar, substitua o arquivo e a licença, atualize o hash `integrity` no
template correspondente e execute os testes em `browser_tests`.
