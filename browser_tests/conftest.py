from decimal import Decimal
from urllib.parse import urlsplit

import pytest
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.urls import reverse
from playwright.sync_api import sync_playwright

from fretes.models import Carrier, Cliente, FreightTable, Garantia, Pedido, PedidoVolume, Produto


@pytest.fixture(autouse=True)
def browser_settings(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture(scope="session")
def browser():
    # A API síncrona do Playwright mantém um event loop na thread do teste.
    # O banco é isolado; este ajuste existe somente durante esta fixture.
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
        with sync_playwright() as playwright:
            instance = playwright.chromium.launch()
            yield instance
            instance.close()


@pytest.fixture
def dados(transactional_db):
    user = User.objects.create_superuser(username="mobile-validation", password="test-only")
    carrier = Carrier.objects.create(nome="Transportadora para validação mobile")
    FreightTable.objects.create(carrier=carrier, peso_ate_50=Decimal("80"), frete_minimo=Decimal("80"))
    pedido = Pedido.objects.create(numero_pedido="MOBILE-001", carrier=carrier)
    PedidoVolume.objects.create(pedido=pedido, largura_cm=10, altura_cm=10, comprimento_cm=10)
    cliente = Cliente.objects.create(nome="Cliente " + "NomeComprido" * 8, cnpj="12345678000190")
    produto = Produto.objects.create(codigo="MOBILE-P001", descricao="Descrição " + "PeçaComprida" * 12)
    garantia = Garantia.objects.create(
        cliente=cliente, codigo_peca=produto.codigo, marca="MARCA", defeito="Defeito de teste",
        nota_recebida="NF-MOBILE", data_recebimento="2026-10-07", valor=10,
    )
    return dict(user=user, carrier=carrier, pedido=pedido, cliente=cliente, produto=produto, garantia=garantia)


@pytest.fixture
def page(browser, client, dados, live_server):
    client.force_login(dados["user"])
    context = browser.new_context(
        viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True,
        service_workers="block",
    )
    origin = urlsplit(live_server.url)
    external_requests = []
    asset_failures = []

    def intranet_only(route):
        url = urlsplit(route.request.url)
        if url.scheme in ("http", "https") and (url.scheme, url.netloc) != (origin.scheme, origin.netloc):
            external_requests.append(route.request.url)
            route.abort(error_code="blockedbyclient")
        else:
            route.continue_()

    context.route("**/*", intranet_only)
    assets = {"stylesheet", "script", "image", "font"}
    context.on("response", lambda response: asset_failures.append(
        (response.url, response.status)
    ) if response.request.resource_type in assets and response.status >= 400 else None)
    context.on("requestfailed", lambda request: asset_failures.append(
        (request.url, request.failure)
    ) if request.resource_type in assets else None)
    context.add_cookies([{
        "name": django_settings.SESSION_COOKIE_NAME,
        "value": client.cookies[django_settings.SESSION_COOKIE_NAME].value,
        "url": live_server.url,
    }])
    tab = context.new_page()
    errors = []
    tab.on("pageerror", lambda error: errors.append(str(error)))
    yield tab
    context.close()
    assert not errors, errors
    assert not external_requests, external_requests
    assert not asset_failures, asset_failures


@pytest.fixture
def visit(page, live_server):
    def navigate(name, *args):
        response = page.goto(live_server.url + reverse("fretes:" + name, args=args))
        assert response.status == 200
        return response
    return navigate
