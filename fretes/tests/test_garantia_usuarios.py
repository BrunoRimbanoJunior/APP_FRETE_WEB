import json

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User
from django.test import RequestFactory
from django.urls import reverse

from fretes.admin import GarantiaAdmin
from fretes.models import AuditLog, Cliente, Garantia, Produto


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(nome="Cliente Teste", cnpj="00.000.000/0001-00")


@pytest.fixture
def produto(db):
    return Produto.objects.create(codigo="PEC-001", descricao="Peca Teste")


@pytest.mark.django_db
def test_criacao_de_garantia_registra_usuario(client, cliente, produto):
    usuario = User.objects.create_user(username="criador", password="senha")
    usuario.user_permissions.add(Permission.objects.get(codename="add_garantia"))
    client.force_login(usuario)

    response = client.post(
        reverse("fretes:garantia_create"),
        {
            "nota_recebida": "NF-001",
            "cliente": cliente.pk,
            "data_recebimento": "2026-08-14",
            "tipo": Garantia.TIPO_GARANTIA,
            "items_payload": json.dumps(
                [
                    {
                        "codigo_peca": produto.codigo,
                        "marca": "Marca Teste",
                        "defeito": "Defeito Teste",
                        "numero_lote": "LOTE-1",
                        "valor": "10.00",
                        "nota_retorno": "",
                        "data_retorno": "",
                        "mao_de_obra": False,
                        "valor_mao_de_obra": "0",
                    }
                ]
            ),
        },
    )

    assert response.status_code == 302
    garantia = Garantia.objects.get()
    assert garantia.criado_por == usuario
    assert garantia.alterado_por == usuario


@pytest.mark.django_db
def test_alteracao_preserva_criador_e_registra_novo_usuario(client, cliente, produto):
    criador = User.objects.create_user(username="criador", password="senha")
    editor = User.objects.create_user(username="editor", password="senha")
    garantia = Garantia.objects.create(
        cliente=cliente,
        codigo_peca=produto.codigo,
        marca="MARCA TESTE",
        defeito="Defeito anterior",
        nota_recebida="NF-001",
        valor="10.00",
        data_recebimento="2026-08-14",
        criado_por=criador,
        alterado_por=criador,
    )
    client.force_login(editor)

    response = client.post(
        reverse("fretes:garantia_update", args=[garantia.pk]),
        {
            "cliente": cliente.pk,
            "codigo_peca": produto.codigo,
            "marca": "Marca Editada",
            "defeito": "Defeito atualizado",
            "numero_lote": "LOTE-2",
            "nota_recebida": "NF-001",
            "valor": "20.00",
            "data_recebimento": "2026-08-14",
            "tipo": Garantia.TIPO_GARANTIA,
            "nota_retorno": "",
            "data_retorno": "",
            "mao_de_obra": "",
            "valor_mao_de_obra": "0",
        },
    )

    assert response.status_code == 302
    garantia.refresh_from_db()
    assert garantia.criado_por == criador
    assert garantia.alterado_por == editor
    assert garantia.defeito == "Defeito atualizado"
    audit_log = AuditLog.objects.filter(
        object_type="Garantia", object_id=str(garantia.pk), action="update"
    ).latest("id")
    assert audit_log.changes["alterado_por"] == [criador.pk, editor.pk]


@pytest.mark.django_db
def test_admin_registra_criador_e_editor(cliente, produto):
    criador = User.objects.create_user(username="admin-criador", password="senha")
    editor = User.objects.create_user(username="admin-editor", password="senha")
    request = RequestFactory().post("/admin/fretes/garantia/add/")
    request.user = criador
    model_admin = GarantiaAdmin(Garantia, AdminSite())
    garantia = Garantia(
        cliente=cliente,
        codigo_peca=produto.codigo,
        marca="MARCA TESTE",
        defeito="Defeito",
        nota_recebida="NF-ADMIN",
        valor="10.00",
        data_recebimento="2026-08-14",
    )

    model_admin.save_model(request, garantia, form=None, change=False)
    assert garantia.criado_por == criador
    assert garantia.alterado_por == criador

    request.user = editor
    garantia.defeito = "Defeito editado"
    model_admin.save_model(request, garantia, form=None, change=True)
    garantia.refresh_from_db()
    assert garantia.criado_por == criador
    assert garantia.alterado_por == editor
