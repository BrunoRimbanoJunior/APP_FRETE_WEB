import os
import re
from pathlib import Path

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from fretes.models import FreteCalculado, Garantia, Pedido, Produto


@pytest.mark.parametrize("width", [320, 375, 768, 1280])
def test_layout_sem_rolagem_horizontal(page, visit, dados, width):
    page.set_viewport_size({"width": width, "height": 900})
    routes = [
        ("index", ()), ("pedido_list", ()), ("pedido_create", ()),
        ("pedido_update", (dados["pedido"].pk,)), ("calcular", ()),
        ("produto_list", ()), ("produto_create", ()), ("cliente_list", ()),
        ("cliente_create", ()), ("garantia_list", ()), ("garantia_create", ()),
        ("garantia_update", (dados["garantia"].pk,)), ("relatorios", ()),
        ("romaneio", ()), ("garantias_gerencial", ()),
        ("garantias_gerencial_produto", (dados["produto"].codigo,)), ("audit_logs", ()),
    ]
    for name, args in routes:
        visit(name, *args)
        assert page.locator('meta[name="viewport"]').count() == 1, name
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), (name, width)
        if width < 576 and page.locator("table.mobile-table tbody tr").count():
            assert page.locator("table.mobile-table thead").evaluate(
                "element => getComputedStyle(element).position === 'absolute'"
            ), name
        directory = os.getenv("MOBILE_SCREENSHOT_DIR")
        if directory and width in (375, 1280):
            Path(directory).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(directory) / f"{name}-{width}.png"), full_page=True)


def test_menu_por_toque_e_teclado(page, visit):
    visit("index")
    navigation = page.locator("#main-navigation")
    expect(navigation).not_to_be_visible()
    page.get_by_role("button", name="Menu", exact=True).tap()
    expect(navigation).to_be_visible()
    page.get_by_text("CONFIG", exact=True).tap()
    expect(page.get_by_role("link", name="Admin", exact=True)).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("link", name="Admin", exact=True)).not_to_be_visible()
    page.get_by_text("CONFIG", exact=True).focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("link", name="Admin", exact=True)).to_be_visible()


def test_busca_por_input_e_calculo_htmx(page, visit, dados):
    visit("calcular")
    # fill() dispara input, sem depender de keyup de teclado físico.
    page.locator("#id_numero_pedido").fill("MOBILE")
    expect(page.locator("#pedidos-datalist option")).to_have_count(1)
    page.locator("#id_numero_pedido").fill(dados["pedido"].numero_pedido)
    page.locator("#id_valor_nota").fill("5000")
    page.locator("#id_kg_nota").fill("10")
    page.get_by_role("button", name="Calcular", exact=True).tap()
    expect(page.locator("#resultado")).to_contain_text("Total:")
    expect(page.get_by_role("button", name="Calcular", exact=True)).to_be_enabled()
    assert FreteCalculado.objects.filter(numero_pedido=dados["pedido"].numero_pedido).count() == 1


def test_calculo_bloqueia_envio_duplicado_e_recupera_erro(page, visit, dados):
    visit("calcular")
    page.locator("#id_numero_pedido").fill(dados["pedido"].numero_pedido)
    page.locator("#id_valor_nota").fill("1000.50")
    expect(page.locator("#frete-alerta")).to_be_visible()
    page.locator("#id_tipo_frete").select_option("a_pagar")
    page.locator("#id_kg_nota").fill("10")
    pending = []
    def hold_post(route):
        if route.request.method == "POST":
            pending.append(route)
        else:
            route.continue_()
    page.route("**/calcular/", hold_post)
    button = page.get_by_role("button", name="Calcular", exact=True)
    button.tap()
    expect(button).to_be_disabled()
    expect(page.locator("#calculo-status")).to_be_visible()
    button.evaluate("element => element.click()")
    assert len(pending) == 1
    pending.pop().fulfill(status=503, body="Unavailable")
    expect(page.locator("#resultado")).to_contain_text("Confira a conexão")
    expect(button).to_be_enabled()
    expect(page.locator("#calculo-status")).not_to_be_visible()
    page.unroute("**/calcular/", hold_post)
    button.tap()
    expect(page.locator("#resultado")).to_contain_text("Total:")
    assert FreteCalculado.objects.filter(numero_pedido=dados["pedido"].numero_pedido).count() == 1


def test_garantia_buscas_itens_e_salvamento(page, visit, dados):
    visit("garantia_create")
    page.locator("#cliente-search").fill("Cliente")
    page.locator('[hx-target="#id_cliente"]').tap()
    expect(page.locator("#id_cliente option")).to_have_count(2)
    page.locator("#id_cliente").select_option(str(dados["cliente"].pk))
    page.locator("#id_nota_recebida").fill("NF-BROWSER")
    page.locator("#id_data_recebimento").fill("2026-10-07")
    page.locator("#produto-search").fill("MOBILE")
    page.locator('[hx-target="#id_item_codigo_peca"]').tap()
    expect(page.locator("#id_item_codigo_peca option")).to_have_count(2)
    page.locator("#id_item_codigo_peca").select_option(dados["produto"].codigo)
    page.locator("#id_item_marca").fill("Marca Browser")
    page.locator("#id_item_defeito").fill("Defeito Browser")
    page.locator("#id_item_valor").fill("12.50")
    page.locator("#add-item-btn").tap()
    expect(page.locator("#items-table tbody")).to_contain_text("Marca Browser")
    page.locator('[data-action="edit"]').tap()
    page.locator("#id_item_defeito").fill("Defeito atualizado")
    page.locator("#add-item-btn").tap()
    expect(page.locator("#items-table tbody")).to_contain_text("Defeito atualizado")
    page.get_by_role("button", name="Salvar", exact=False).tap()
    expect(page).to_have_url(re.compile(re.escape(reverse("fretes:garantia_list")) + "$"))
    assert Garantia.objects.filter(nota_recebida="NF-BROWSER", defeito="Defeito atualizado").count() == 1


def test_pedido_volumes_e_salvamento(page, visit, dados):
    visit("pedido_create")
    page.locator("#id_numero_pedido").fill("PED-BROWSER")
    page.locator("#id_carrier").select_option(str(dados["carrier"].pk))
    page.locator("#add-volume-btn").tap()
    volumes = page.locator(".volume-container")
    for index in range(volumes.count()):
        volume = volumes.nth(index)
        for field in ("largura_cm", "altura_cm", "comprimento_cm"):
            volume.locator(f'input[name$="-{field}"]').fill("10.5")
        volume.locator('input[name$="-quantidade"]').fill("2")
    expect(page.locator("#total-volumes-display")).to_have_value(str(2 * volumes.count()))
    volumes.last.locator('input[name$="-DELETE"]').check()
    expect(page.locator("#total-volumes-display")).to_have_value(str(2 * (volumes.count() - 1)))
    expected_count = volumes.count() - 1
    page.get_by_role("button", name="Salvar Pedido").tap()
    expect(page).to_have_url(re.compile(re.escape(reverse("fretes:pedido_list")) + "$"))
    assert Pedido.objects.get(numero_pedido="PED-BROWSER").volumes.count() == expected_count


def test_paginacao_preserva_filtro(page, visit):
    Produto.objects.bulk_create([Produto(codigo=f"PAGE-{i:03}", descricao="Página") for i in range(55)])
    visit("produto_list")
    page.locator("#id_codigo").fill("PAGE")
    page.get_by_role("button", name="Filtrar", exact=True).tap()
    expect(page.locator("table tbody tr")).to_have_count(50)
    page.get_by_role("link", name="Proxima", exact=True).tap()
    expect(page.locator("table tbody tr")).to_have_count(5)
    assert "codigo=PAGE" in page.url and "page=2" in page.url
