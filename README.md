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
