
from decimal import Decimal

def calcular_frete(m3_value: Decimal, carrier, kg_nota: Decimal, valor_nota: Decimal | None):
    tab = carrier.tabela
    m3 = Decimal(m3_value or 0)
    fator = tab.fator_peso_cubico or Decimal("230")
    peso_cubico = (m3 * fator).quantize(Decimal("0.01"))
    peso_usado = max(Decimal(kg_nota or 0), Decimal(peso_cubico or 0))

    # Faixas de preço
    if peso_usado <= 50:
        base = tab.peso_ate_50
    elif peso_usado <= 100:
        base = tab.peso_ate_100
    elif peso_usado <= 150:
        base = tab.peso_ate_150
    elif peso_usado <= 200:
        base = tab.peso_ate_200
    elif peso_usado <= 300:
        base = tab.peso_ate_300
    else:
        base = (peso_usado / Decimal(1000)) * tab.frete_ton

    adicional_valor = Decimal("0")
    if valor_nota and tab.frete_valor_perc:
        adicional_valor = (Decimal(valor_nota) * tab.frete_valor_perc) / Decimal(100)

    # GRIS (% sobre o valor da nota)
    gris_valor = Decimal("0")
    if valor_nota and getattr(tab, "gris_perc", Decimal("0")):
        gris_valor = (Decimal(valor_nota) * Decimal(tab.gris_perc)) / Decimal(100)

    # 💡 Lógica corrigida para o pedágio
    pedagio = Decimal("0")
    if tab.pedagio:
        pedagio = (peso_usado / Decimal(100)) * tab.pedagio

    # Valor de despacho é fixo por nota
    valor_despacho = Decimal(getattr(tab, "valor_despacho", 0) or 0)

    total = max(base, tab.frete_minimo) + pedagio + adicional_valor + gris_valor + valor_despacho
    total = Decimal(total).quantize(Decimal("0.01"))

    return {
        "m3": m3,
        "peso_cubico": peso_cubico,
        "peso_usado": peso_usado,
        "frete_total": total,
    }
