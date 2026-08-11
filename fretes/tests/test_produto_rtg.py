from io import BytesIO

import pytest
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from fretes.models import Produto


@pytest.fixture(autouse=True)
def staticfiles_sem_manifest(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


def _arquivo_produtos(headers, values):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    sheet.append(values)
    stream = BytesIO()
    workbook.save(stream)
    return SimpleUploadedFile(
        "produtos.xlsx",
        stream.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.mark.django_db
def test_filtro_de_codigo_tambem_busca_rtg(client):
    user = User.objects.create_user(username="consulta", password="senha")
    client.force_login(user)
    Produto.objects.create(codigo="COD-001", rtg="RTG-ABC", descricao="Produto")

    response = client.get(reverse("fretes:produto_list"), {"codigo": "RTG-ABC"})

    assert response.status_code == 200
    assert list(response.context["produtos"].values_list("codigo", flat=True)) == ["COD-001"]


@pytest.mark.django_db
def test_importacao_grava_rtg(client):
    user = User.objects.create_user(username="importador", password="senha")
    user.user_permissions.add(Permission.objects.get(codename="can_import_products"))
    client.force_login(user)

    headers = [
        "CODIGO", "RTG", "DESCRICAO", "APLICACAO", "PESO BRUTO", "PESO LIQUIDO",
        "LARGURA (CM)", "ALTURA (CM)", "COMPRIMENTO (CM)",
    ]
    arquivo = _arquivo_produtos(
        headers,
        ["COD-002", "RTG-XYZ", "Peca", "Aplicacao", 1, 0.8, 10, 20, 30],
    )
    response = client.post(reverse("fretes:admin_import_produtos"), {"arquivo": arquivo})

    assert response.status_code == 200
    produto = Produto.objects.get(codigo="COD-002")
    assert produto.rtg == "RTG-XYZ"
    assert produto.descricao == "Peca Aplicacao"


@pytest.mark.django_db
def test_importacao_sem_coluna_rtg_preserva_valor_existente(client):
    user = User.objects.create_user(username="importador-legado", password="senha")
    user.user_permissions.add(Permission.objects.get(codename="can_import_products"))
    client.force_login(user)
    Produto.objects.create(codigo="COD-003", rtg="RTG-MANTER", descricao="Anterior")

    headers = [
        "CODIGO", "DESCRICAO", "APLICACAO", "PESO BRUTO", "PESO LIQUIDO",
        "LARGURA (CM)", "ALTURA (CM)", "COMPRIMENTO (CM)",
    ]
    arquivo = _arquivo_produtos(
        headers,
        ["COD-003", "Atualizada", "Aplicacao", 1, 0.8, 10, 20, 30],
    )

    response = client.post(reverse("fretes:admin_import_produtos"), {"arquivo": arquivo})

    assert response.status_code == 200
    produto = Produto.objects.get(codigo="COD-003")
    assert produto.rtg == "RTG-MANTER"
    assert produto.descricao == "Atualizada Aplicacao"
