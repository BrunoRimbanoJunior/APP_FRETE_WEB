from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize("width", [375, 1280])
def test_telas_e_dependencias_sem_acesso_externo(page, visit, dados, live_server, width):
    # A fixture bloqueia todas as origens externas e falha se houver tentativa.
    # Contexto novo, cache vazio, CSS/JS/fontes/imagens reais e sem service worker.
    page.set_viewport_size({"width": width, "height": 900})
    responses = []
    page.on("response", lambda response: responses.append(response.url))
    routes = [
        ("index", ()), ("pedido_list", ()), ("pedido_create", ()),
        ("pedido_update", (dados["pedido"].pk,)), ("calcular", ()),
        ("produto_list", ()), ("produto_create", ()),
        ("produto_update", (dados["produto"].pk,)), ("cliente_list", ()),
        ("cliente_create", ()), ("cliente_update", (dados["cliente"].pk,)),
        ("garantia_list", ()), ("garantia_create", ()),
        ("garantia_update", (dados["garantia"].pk,)), ("relatorios", ()),
        ("romaneio", ()), ("garantias_gerencial", ()),
        ("garantias_gerencial_produto", (dados["produto"].codigo,)),
        ("audit_logs", ()), ("admin_import_produtos", ()), ("admin_import_clientes", ()),
    ]
    for name, args in routes:
        visit(name, *args)
        expect(page.locator("main")).to_be_visible()
        expect(page.locator(".brand-logo")).to_be_visible()
        assert page.locator(".brand-logo").evaluate("image => image.complete && image.naturalWidth > 0")
        assert page.locator("body").evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(248, 249, 250)"
        assert any("/static/vendor/bootstrap/" in href for href in page.locator('link[rel="stylesheet"]').evaluate_all(
            "elements => elements.map(element => element.href)"
        ))
        for resource in page.locator('link[rel="stylesheet"],script[src],img[src]').evaluate_all(
            "elements => elements.map(element => element.href || element.src)"
        ):
            assert urlsplit(resource).netloc == urlsplit(live_server.url).netloc, (name, resource)

    visit("calcular")
    assert page.evaluate("htmx.version") == "2.0.11"
    page.locator("#id_numero_pedido").fill("MOBILE")
    expect(page.locator("#pedidos-datalist option")).to_have_count(1)
    # Bootstrap usa SVG embutido; data: nao e uma conexao com a internet.
    select = page.locator("select.form-select").first
    if select.count():
        assert "data:image/svg+xml" in select.evaluate("element => getComputedStyle(element).backgroundImage")
    response = page.goto(live_server.url + "/admin/")
    assert response.status == 200
    expect(page.locator("#site-name")).to_be_visible()
    assert any("/static/admin/css/" in url for url in responses)
    assert any("/static/vendor/bootstrap/" in url for url in responses)
    assert any("/static/vendor/htmx/" in url for url in responses)
