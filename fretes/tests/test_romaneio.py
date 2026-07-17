from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from fretes.models import Carrier, FreteCalculado


@pytest.fixture
def usuario_relatorios(db):
    usuario = User.objects.create_user(username="relatorios", password="senha")
    usuario.user_permissions.add(Permission.objects.get(codename="can_view_reports"))
    return usuario


@pytest.fixture
def frete(db):
    carrier = Carrier.objects.create(nome="Transportadora Teste")
    item = FreteCalculado.objects.create(
        numero_pedido="PED-1", numero_nota="NF-10", valor_nota=100,
        kg_nota=20, frete_total=15, carrier=carrier,
    )
    FreteCalculado.objects.filter(pk=item.pk).update(data_calculo=date(2026, 7, 17))
    item.refresh_from_db()
    return item


def test_romaneio_exige_selecao(client, usuario_relatorios, frete):
    client.force_login(usuario_relatorios)
    resposta = client.post(reverse("fretes:romaneio"), {
        "numero_romaneio": "ROM-1", "carrier": frete.carrier_id, "export": "pdf",
    })
    assert resposta.status_code == 200
    assert "Selecione pelo menos uma nota" in resposta.content.decode()


@pytest.mark.parametrize("formato, content_type", [
    ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("pdf", "application/pdf"),
])
def test_exporta_apenas_notas_selecionadas(client, usuario_relatorios, frete, formato, content_type):
    client.force_login(usuario_relatorios)
    resposta = client.post(reverse("fretes:romaneio"), {
        "numero_romaneio": "ROM-1", "carrier": frete.carrier_id,
        "notas": frete.pk, "export": formato,
    })
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == content_type
    assert f"romaneio_ROM-1.{formato}" in resposta["Content-Disposition"]


def test_filtro_invalido_nao_exibe_nem_exporta_notas(client, usuario_relatorios, frete):
    client.force_login(usuario_relatorios)
    resposta = client.post(reverse("fretes:romaneio"), {
        "numero_romaneio": "ROM-1", "start_date": "data-invalida",
        "notas": frete.pk, "export": "pdf",
    })
    assert resposta.status_code == 200
    assert resposta["Content-Type"].startswith("text/html")
    assert "revise os filtros informados" in resposta.content.decode().lower()


def test_nao_exporta_nota_fora_da_transportadora_filtrada(client, usuario_relatorios, frete):
    outra = Carrier.objects.create(nome="Outra Transportadora")
    client.force_login(usuario_relatorios)
    resposta = client.post(reverse("fretes:romaneio"), {
        "numero_romaneio": "ROM-1", "carrier": outra.pk,
        "notas": frete.pk, "export": "xlsx",
    })
    assert resposta.status_code == 200
    assert resposta["Content-Type"].startswith("text/html")
    assert "nao pertencem ao filtro" in resposta.content.decode().lower()


def test_romaneio_exige_permissao(client, frete):
    usuario = User.objects.create_user(username="sem-permissao", password="senha")
    client.force_login(usuario)
    resposta = client.get(reverse("fretes:romaneio"))
    assert resposta.status_code == 403
