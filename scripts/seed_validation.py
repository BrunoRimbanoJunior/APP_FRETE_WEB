"""Dados fictícios para a instância do docker-compose.validation.yml."""
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fretes_web.settings.prod")

import django
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from fretes.models import Carrier, Cliente, FreightTable, Garantia, Pedido, PedidoVolume, Produto

if os.getenv("VALIDATION_ONLY") != "1" or settings.DATABASES["default"]["NAME"] != "validation":
    raise SystemExit("Este script só pode ser usado no banco isolado de validação.")

user, _ = User.objects.get_or_create(username="validacao", defaults={"is_staff": True, "is_superuser": True})
password = secrets.token_urlsafe(14)
user.set_password(password)
user.save()
carrier, _ = Carrier.objects.get_or_create(nome="Transportadora Demonstração")
FreightTable.objects.get_or_create(carrier=carrier, defaults={"peso_ate_50": 80, "frete_minimo": 80})
cliente, _ = Cliente.objects.get_or_create(cnpj="00000000000000", defaults={"nome": "Cliente fictício para validação", "cidade": "São Paulo", "estado": "SP"})
for index in range(55):
    Produto.objects.get_or_create(codigo=f"DEMO-{index:03}", defaults={"descricao": f"Produto de demonstração {index}", "rtg": f"RTG-{index:03}"})
pedido, _ = Pedido.objects.get_or_create(numero_pedido="DEMO-001", defaults={"carrier": carrier})
PedidoVolume.objects.get_or_create(pedido=pedido, largura_cm=10, altura_cm=10, comprimento_cm=10, defaults={"quantidade": 2})
Garantia.objects.get_or_create(cliente=cliente, codigo_peca="DEMO-001", nota_recebida="NF-DEMO", defaults={"marca": "DEMONSTRAÇÃO", "defeito": "Item fictício", "data_recebimento": "2026-10-07", "valor": 10})
print(f"Usuário de validação: validacao\nSenha: {password}")
