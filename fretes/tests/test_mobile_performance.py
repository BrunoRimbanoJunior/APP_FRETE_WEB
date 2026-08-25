import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from fretes.models import Cliente, Garantia, Produto


@pytest.fixture(autouse=True)
def staticfiles_sem_manifest(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def usuario(db):
    user = User.objects.create_user(username="mobile", password="senha")
    user.user_permissions.add(Permission.objects.get(codename="add_garantia"))
    return user


@pytest.mark.django_db
def test_lista_de_produtos_entrega_cinquenta_registros_por_pagina(client, usuario):
    Produto.objects.bulk_create(
        [
            Produto(codigo=f"P-{indice:03}", descricao=f"Produto {indice}")
            for indice in range(55)
        ]
    )
    client.force_login(usuario)

    primeira = client.get(reverse("fretes:produto_list"))
    segunda = client.get(reverse("fretes:produto_list"), {"page": 2})

    assert primeira.status_code == 200
    assert primeira.context["page_obj"].paginator.count == 55
    assert len(primeira.context["produtos"]) == 50
    assert len(segunda.context["produtos"]) == 5


@pytest.mark.django_db
def test_nova_garantia_nao_renderiza_catalogos_inteiros(client, usuario):
    Produto.objects.bulk_create(
        [Produto(codigo=f"PROD-{i:03}", descricao=f"Produto {i}") for i in range(30)]
    )
    Cliente.objects.bulk_create(
        [Cliente(nome=f"Cliente {i}", cnpj=f"{i:014}") for i in range(30)]
    )
    client.force_login(usuario)

    response = client.get(reverse("fretes:garantia_create"))

    assert response.status_code == 200
    assert response.context["header_form"].fields["cliente"].queryset.count() == 0
    assert response.context["produtos"].count() == 0
    assert b"PROD-000" not in response.content
    assert b"Cliente 0" not in response.content


@pytest.mark.django_db
def test_buscas_sob_demanda_exigem_dois_caracteres_e_limitam_resultados(client, usuario):
    Produto.objects.bulk_create(
        [Produto(codigo=f"ABC-{i:03}", descricao=f"Produto {i}") for i in range(30)]
    )
    Cliente.objects.bulk_create(
        [Cliente(nome=f"Cliente Busca {i}", cnpj=f"{i:014}") for i in range(30)]
    )
    client.force_login(usuario)

    produto_curto = client.get(reverse("fretes:produtos_options"), {"q": "A"})
    produtos = client.get(reverse("fretes:produtos_options"), {"q": "ABC"})
    clientes = client.get(reverse("fretes:clientes_options"), {"q": "Cliente"})

    # Cada fragmento inclui uma opcao vazia e no maximo 20 resultados.
    assert produto_curto.content.count(b"<option") == 1
    assert produtos.content.count(b"<option") == 21
    assert clientes.content.count(b"<option") == 21


@pytest.mark.django_db
def test_edicao_carrega_somente_cliente_e_produto_selecionados(client, usuario):
    cliente = Cliente.objects.create(nome="Cliente Selecionado", cnpj="00.000.000/0001-00")
    outro_cliente = Cliente.objects.create(nome="Cliente Nao Selecionado", cnpj="00.000.000/0002-00")
    produto = Produto.objects.create(codigo="PROD-SELECIONADO", descricao="Produto selecionado")
    outro_produto = Produto.objects.create(codigo="PROD-OUTRO", descricao="Outro produto")
    garantia = Garantia.objects.create(
        cliente=cliente,
        codigo_peca=produto.codigo,
        marca="MARCA",
        defeito="Defeito",
        nota_recebida="NF-1",
        data_recebimento="2026-08-25",
    )
    client.force_login(usuario)

    response = client.get(reverse("fretes:garantia_update", args=[garantia.pk]))

    assert response.status_code == 200
    assert cliente.nome.encode() in response.content
    assert produto.codigo.encode() in response.content
    assert outro_cliente.nome.encode() not in response.content
    assert outro_produto.codigo.encode() not in response.content
