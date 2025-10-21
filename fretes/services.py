
from decimal import Decimal

def _tipo1_impl(m3_value: Decimal, carrier, kg_nota: Decimal, valor_nota: Decimal | None):
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


def _tipo2_impl(m3_value: Decimal, carrier, kg_nota: Decimal, valor_nota: Decimal | None):
    """
    Tipo 2:
    - peso_cubico = m3 * fator_peso_cubico
    - Se peso_cubico > 100kg:
        • valor_100kg = tab.peso_ate_100 (valor fixo para os primeiros 100kg)
        • excedente = peso_cubico - 100
        • valor_excedente = excedente * (tab.frete_ton / 1000)
        • frete_peso = valor_100kg + valor_excedente
      Senao (<= 100kg): frete_peso = tab.peso_ate_100 se houver peso > 0, senao 0
    - frete_valor = valor_nota * frete_valor_perc/100 (se informado)
    - gris = valor_nota * gris_perc/100 (se informado)
    - pedagio = (peso_cubico/100) * tab.pedagio (se informado)
    - total = max(frete_peso, frete_minimo) + frete_valor + gris + pedagio + valor_despacho
    """
    tab = carrier.tabela
    m3 = Decimal(m3_value or 0)
    fator = tab.fator_peso_cubico or Decimal("230")
    peso_cubico = (m3 * fator).quantize(Decimal("0.01"))

    if peso_cubico <= 0:
        frete_peso = Decimal("0")
    elif peso_cubico <= 100:
        frete_peso = Decimal(tab.peso_ate_100 or 0)
    else:
        excedente = (peso_cubico - Decimal("100")).quantize(Decimal("0.01"))
        valor_kg_ton = (Decimal(tab.frete_ton or 0) / Decimal("1000")).quantize(Decimal("0.01"))
        valor_excedente = (excedente * valor_kg_ton).quantize(Decimal("0.01"))
        frete_peso = Decimal(tab.peso_ate_100 or 0) + valor_excedente

    frete_valor = Decimal("0")
    if valor_nota and getattr(tab, "frete_valor_perc", None):
        frete_valor = (Decimal(valor_nota) * Decimal(tab.frete_valor_perc)).quantize(Decimal("0.0001")) / Decimal("100")
        frete_valor = frete_valor.quantize(Decimal("0.01"))

    gris_valor = Decimal("0")
    if valor_nota and getattr(tab, "gris_perc", None):
        gris_valor = (Decimal(valor_nota) * Decimal(tab.gris_perc)).quantize(Decimal("0.0001")) / Decimal("100")
        gris_valor = gris_valor.quantize(Decimal("0.01"))

    pedagio = Decimal("0")
    if getattr(tab, "pedagio", None):
        # quantidade de blocos de 100kg, arredondado para cima
        from decimal import ROUND_CEILING
        blocos = (peso_cubico / Decimal("100")).to_integral_value(rounding=ROUND_CEILING)
        pedagio = (blocos * Decimal(tab.pedagio)).quantize(Decimal("0.01"))

    valor_despacho = Decimal(getattr(tab, "valor_despacho", 0) or 0)

    total = max(Decimal(frete_peso), Decimal(tab.frete_minimo or 0)) + frete_valor + gris_valor + pedagio + valor_despacho
    total = total.quantize(Decimal("0.01"))

    return {
        "m3": m3,
        "peso_cubico": peso_cubico,
        "peso_usado": peso_cubico,
        "frete_total": total,
    }


def calcular_frete(m3_value: Decimal, carrier, kg_nota: Decimal, valor_nota: Decimal | None):
    """
    Dispatch para o tipo de calculo configurado na tabela da transportadora.
    tipo 1 = logica atual; tipo 2 = nova (placeholder ate definicao).
    """
    tab = carrier.tabela
    tipo = getattr(tab, "tipo_calculo", 1) or 1
    if tipo == 1:
        return _tipo1_impl(m3_value, carrier, kg_nota, valor_nota)
    if tipo == 2:
        return _tipo2_impl(m3_value, carrier, kg_nota, valor_nota)
    # fallback padrao
    return _tipo1_impl(m3_value, carrier, kg_nota, valor_nota)
