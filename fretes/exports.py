import html
import re
from decimal import Decimal
from io import BytesIO
from django.db.models import Sum, Count
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .models import Produto

# Helpers de formatação pt-BR
def _fmt_number_br(value) -> str:
    try:
        if value in (None, ""):
            return "0,00"
        n = float(value)
        s = f"{n:,.2f}"
        return s.replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return str(value)


def _fmt_number_br_p(value, places: int = 2) -> str:
    try:
        if value in (None, ""):
            value = 0
        n = float(value)
        s = f"{n:,.{places}f}"
        return s.replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return str(value)


def _fmt_int_br(value) -> str:
    try:
        if value in (None, ""):
            return "0"
        n = int(value)
        s = f"{n:,}"
        return s.replace(",", ".")
    except Exception:
        return str(value)


def _fmt_date_br(dt) -> str:
    try:
        return dt.strftime("%d/%m/%Y") if dt else ""
    except Exception:
        return str(dt)

def _pedido_volume_stats(pedido):
    rows = []
    total_volumes = 0
    total_m3 = Decimal("0")
    for volume in pedido.volumes.all().order_by("id"):
        rows.append((volume.largura_cm, volume.altura_cm, volume.comprimento_cm, volume.quantidade))
        largura_m = volume.largura_cm / Decimal("100")
        altura_m = volume.altura_cm / Decimal("100")
        comprimento_m = volume.comprimento_cm / Decimal("100")
        total_m3 += (largura_m * altura_m * comprimento_m) * Decimal(volume.quantidade)
        total_volumes += volume.quantidade
    return rows, total_volumes, total_m3.quantize(Decimal("0.001"))


def exportar_pedido_excel(pedido):
    rows, total_volumes, total_m3 = _pedido_volume_stats(pedido)
    wb = Workbook()
    ws = wb.active
    ws.title = "Pedido"

    carrier_name = str(pedido.carrier) if pedido.carrier else ""
    ws.append(["Numero do pedido", pedido.numero_pedido])
    ws.append(["Picking", pedido.picking or ""])
    ws.append(["Transportadora", carrier_name])
    ws.append([])

    ws.append(["Largura (cm)", "Altura (cm)", "Comprimento (cm)", "Quantidade"])
    if rows:
        for largura, altura, comprimento, quantidade in rows:
            ws.append([
                _fmt_number_br(largura),
                _fmt_number_br(altura),
                _fmt_number_br(comprimento),
                _fmt_int_br(quantidade),
            ])
    else:
        ws.append(["-", "-", "-", "-"])

    ws.append([])
    ws.append(["Total de volumes", _fmt_int_br(total_volumes)])
    ws.append(["Cubagem total (m3)", _fmt_number_br_p(total_m3, 3)])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="pedido_{pedido.id}.xlsx"'
    return resp

def exportar_pedido_pdf(pedido):
    rows, total_volumes, total_m3 = _pedido_volume_stats(pedido)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)

    styles = getSampleStyleSheet()
    story = [Paragraph("Relatorio de Pedido", styles["Title"]), Spacer(1, 10)]

    carrier_name = str(pedido.carrier) if pedido.carrier else ""
    info_table = Table([
        ["Numero do pedido", pedido.numero_pedido],
        ["Picking", pedido.picking or ""],
        ["Transportadora", carrier_name],
    ], colWidths=[150, 350])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.extend([info_table, Spacer(1, 12)])

    volume_headers = ["Largura (cm)", "Altura (cm)", "Comprimento (cm)", "Quantidade"]
    volume_rows = [volume_headers]
    if rows:
        for largura, altura, comprimento, quantidade in rows:
            volume_rows.append([
                _fmt_number_br(largura),
                _fmt_number_br(altura),
                _fmt_number_br(comprimento),
                _fmt_int_br(quantidade),
            ])
    else:
        volume_rows.append(["-", "-", "-", "-"])

    volumes_table = Table(volume_rows, repeatRows=1)
    volumes_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ALIGN", (0,1), (-2,-1), "RIGHT"),
        ("ALIGN", (-1,1), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
    ]))
    story.extend([volumes_table, Spacer(1, 10)])

    summary_table = Table([
        ["Total de volumes", _fmt_int_br(total_volumes)],
        ["Cubagem total (m3)", _fmt_number_br_p(total_m3, 3)],
    ], colWidths=[200, 150])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="pedido_{pedido.id}.pdf"'
    return resp


def exportar_produtos_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Produtos"

    headers = [
        "Codigo", "RTG", "Descricao", "Enderecos", "Peso bruto (kg)", "Peso liquido (kg)",
        "Largura (cm)", "Altura (cm)", "Comprimento (cm)"
    ]
    ws.append(headers)

    for produto in queryset:
        ws.append([
            produto.codigo,
            produto.rtg,
            produto.descricao,
            produto.enderecos or "",
            _fmt_number_br(produto.peso_bruto_kg or 0),
            _fmt_number_br(produto.peso_liquido_kg or 0),
            _fmt_number_br(produto.largura_cm or 0),
            _fmt_number_br(produto.altura_cm or 0),
            _fmt_number_br(produto.comprimento_cm or 0),
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="produtos.xlsx"'
    return resp
def _rows_from_queryset(queryset):
    rows = []
    for f in queryset:
        try:
            pedidos_list = list(f.pedidos.all())
        except Exception:
            pedidos_list = []
        pedidos_str = ", ".join(str(p) for p in pedidos_list) if pedidos_list else (f.numero_pedido or "")
        rows.append([
            _fmt_date_br(f.data_calculo),
            pedidos_str,
            f.numero_nota or "",
            getattr(f, 'get_tipo_frete_display', lambda: getattr(f, 'tipo_frete', ''))(),
            _fmt_number_br(f.valor_nota or 0),
            _fmt_number_br(f.kg_nota or 0),
            str(f.carrier),
            _fmt_number_br(f.m3 or 0),
            _fmt_number_br(f.peso_cubico or 0),
            _fmt_number_br(f.peso_usado or 0),
            _fmt_number_br(f.frete_total or 0),
        ])
    return rows

def exportar_fretes_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Fretes"

    headers = ["Data", "Pedidos", "Nota", "Tipo Frete", "Valor Nota", "KG Nota", "Transportadora",
               "m3", "Peso Cubico", "Peso Usado", "Total (R$)"]
    ws.append(headers)

    for row in _rows_from_queryset(queryset):
        ws.append(row)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="fretes.xlsx"'
    return resp

def exportar_fretes_pdf(queryset):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)

    headers = ["Data", "Pedidos", "Nota", "Tipo Frete", "Valor Nota", "KG Nota", "Transportadora",
               "m3", "Peso Cubico", "Peso Usado", "Total (R$)"]
    data = [headers] + _rows_from_queryset(queryset)

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (3,1), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))

    styles = getSampleStyleSheet()
    story = [Paragraph("Relatorio de Fretes", styles["Title"]), Spacer(1, 8), table]
    doc.build(story)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename=\"fretes.pdf\"'
    return resp


def _romaneio_filename(numero_romaneio):
    seguro = re.sub(r"[^A-Za-z0-9_-]+", "_", str(numero_romaneio)).strip("_")
    return seguro or "romaneio"


def _romaneio_rows(queryset, prefixo_real=False):
    rows = []
    for frete in queryset:
        valor_nota = _fmt_number_br(frete.valor_nota or 0)
        valor_frete = _fmt_number_br(frete.frete_total or 0)
        if prefixo_real:
            valor_nota = f"R$ {valor_nota}"
            valor_frete = f"R$ {valor_frete}"
        rows.append([
            _fmt_date_br(frete.data_calculo),
            frete.numero_nota or "",
            str(frete.carrier),
            valor_nota,
            _fmt_number_br(frete.kg_nota or 0),
            _fmt_number_br_p(frete.m3 or 0, 3),
            valor_frete,
        ])
    return rows


def exportar_romaneio_excel(queryset, numero_romaneio):
    wb = Workbook()
    ws = wb.active
    ws.title = "Romaneio"
    ws.append(["Romaneio de entrega", str(numero_romaneio)])
    ws.append([])
    ws.append(["Data", "Nota", "Transportadora", "Valor nota", "KG", "m3", "Frete"])
    for row in _romaneio_rows(queryset):
        ws.append(row)

    buf = BytesIO()
    wb.save(buf)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="romaneio_{_romaneio_filename(numero_romaneio)}.xlsx"'
    return resp


def exportar_romaneio_pdf(queryset, numero_romaneio):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20,
        topMargin=20, bottomMargin=20,
    )
    styles = getSampleStyleSheet()
    data = [["Data", "Nota", "Transportadora", "Valor nota", "KG", "m3", "Frete"]]
    data.extend(_romaneio_rows(queryset, prefixo_real=True))
    table = Table(
        data,
        repeatRows=1,
        colWidths=[70, 90, 190, 110, 80, 80, 80],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story = [
        Paragraph("Romaneio de Entrega", styles["Title"]),
        Paragraph(f"Numero: {html.escape(str(numero_romaneio))}", styles["Heading2"]),
        Spacer(1, 8),
        table,
    ]
    doc.build(story)
    resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="romaneio_{_romaneio_filename(numero_romaneio)}.pdf"'
    return resp


# ---------------- Garantias ----------------
def _garantias_rows(queryset):
    rows = []
    for g in queryset:
        rows.append([
            g.id,
            getattr(g.cliente, "nome", ""),
            getattr(g.cliente, "cnpj", ""),
            g.codigo_peca,
            getattr(g, "marca", "Nao Informado") or "Nao Informado",
            g.defeito,
            g.numero_lote or "",
            g.nota_recebida,
            g.valor,
            ("Sim" if getattr(g, "mao_de_obra", False) else "Nao"),
            getattr(g, "valor_mao_de_obra", 0) or 0,
            g.data_recebimento.strftime("%d/%m/%Y") if g.data_recebimento else "",
            g.nota_retorno or "",
            g.data_retorno.strftime("%d/%m/%Y") if g.data_retorno else "",
            ("Garantia" if (getattr(g, "tipo", "garantia") == "garantia") else "Devolucao"),
            "Atendido" if g.nota_retorno else "Em aberto",
        ])
    return rows


def exportar_garantias_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Garantias"

    headers = [
        "ID", "Cliente", "CNPJ", "Cod. Peca", "Marca", "Defeito", "Lote",
        "Nota Recebida", "Valor", "Mao de Obra", "Valor M.O.", "Recebido em", "Nota Retorno", "Retorno em", "Tipo", "Status"
    ]
    ws.append(headers)
    for row in _garantias_rows(queryset):
        row_copy = list(row)
        row_copy[8] = _fmt_number_br(row_copy[8])
        row_copy[10] = _fmt_number_br(row_copy[10])
        ws.append(row_copy)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="garantias.xlsx"'
    return resp


def exportar_garantias_pdf(queryset):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    headers = [
        "ID", "Cliente", "CNPJ", "Cod. Peca", "Marca", "Defeito", "Lote",
        "Nota Recebida", "Valor", "Mao de Obra", "Valor M.O.", "Recebido em", "Nota Retorno", "Retorno em", "Tipo", "Status"
    ]
    rows = _garantias_rows(queryset)

    total_valor = sum((r[8] or 0) for r in rows)
    total_mo = sum((r[10] or 0) for r in rows)

    totals_row = [""] * len(headers)
    totals_row[7] = "Totais"
    totals_row[8] = _fmt_number_br(total_valor)
    totals_row[10] = _fmt_number_br(total_mo)

    data_rows = rows + [totals_row]

    styles = getSampleStyleSheet()
    small_left = styles['BodyText'].clone('SmallLeft')
    small_left.fontSize = 8
    small_left.leading = 9
    small_left.spaceAfter = 0

    small_center = small_left.clone('SmallCenter')
    small_center.alignment = 1

    small_right = small_left.clone('SmallRight')
    small_right.alignment = 2

    table_data = [headers]
    for row in data_rows:
        id_value = Paragraph(html.escape(str(row[0])), small_center)
        cliente = Paragraph(html.escape(str(row[1])), small_left)
        cnpj = Paragraph(html.escape(str(row[2])), small_left)
        codigo = Paragraph(html.escape(str(row[3])), small_left)
        marca = Paragraph(html.escape(str(row[4])), small_left)
        defeito = Paragraph(html.escape(str(row[5])), small_left)
        lote = Paragraph(html.escape(str(row[6] or "")), small_center)
        nota_recebida = Paragraph(html.escape(str(row[7] or "")), small_center)
        valor = row[8] if row[8] not in (None, "") else 0
        valor_fmt = _fmt_number_br(valor)
        valor_cell = Paragraph(html.escape(valor_fmt), small_right)
        mao = Paragraph(html.escape(str(row[9])), small_center)
        valor_mo = row[10] if row[10] not in (None, "") else 0
        valor_mo_fmt = _fmt_number_br(valor_mo)
        valor_mo_cell = Paragraph(html.escape(valor_mo_fmt), small_right)
        recebido_em = Paragraph(html.escape(_fmt_date_br(row[11]) or ""), small_center)
        nota_retorno = Paragraph(html.escape(str(row[12] or "")), small_left)
        retorno_em = Paragraph(html.escape(_fmt_date_br(row[13]) or ""), small_center)
        tipo = Paragraph(html.escape(str(row[14])), small_center)
        status = Paragraph(html.escape(str(row[15])), small_center)

        table_data.append([
            id_value,
            cliente,
            cnpj,
            codigo,
            marca,
            defeito,
            lote,
            nota_recebida,
            valor_cell,
            mao,
            valor_mo_cell,
            recebido_em,
            nota_retorno,
            retorno_em,
            tipo,
            status,
        ])

    ratios = [0.04, 0.13, 0.09, 0.07, 0.07, 0.11, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.06, 0.06, 0.05, 0.06]
    available_width = doc.width
    col_widths = [available_width * r for r in ratios]

    table = Table(table_data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (8, 1), (8, -2), "RIGHT"),
        ("ALIGN", (10, 1), (10, -2), "RIGHT"),
        ("ALIGN", (8, -1), (10, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor('#eef2f7')),
    ]))

    story = [Paragraph("Relatorio de Garantias", styles["Title"]), Spacer(1, 8), table]
    doc.build(story)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="garantias.pdf"'
    return resp


# ---------------- Garantias (Relatorio Gerencial) ----------------
def _descricoes_por_codigo(rows):
    codigos = [row["codigo_peca"] for row in rows]
    return dict(
        Produto.objects.filter(codigo__in=codigos).values_list("codigo", "descricao")
    )


def exportar_garantias_gerencial_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Gerencial"

    headers = ["Cod. Peca", "Descricao", "Quantidade", "Valor"]
    ws.append(headers)
    rows = list(
        queryset.values("codigo_peca")
        .annotate(total_q=Sum("quantidade"), total_v=Sum("valor"))
        .order_by("-total_q", "codigo_peca")
    )
    descricoes = _descricoes_por_codigo(rows)
    for row in rows:
        ws.append([
            row["codigo_peca"],
            descricoes.get(row["codigo_peca"], ""),
            _fmt_int_br(row["total_q"] or 0),
            _fmt_number_br(row["total_v"] or 0),
        ])
    ws.column_dimensions["B"].width = 45

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="garantias_gerencial.xlsx"'
    return resp


def exportar_garantias_gerencial_pdf(queryset):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()
    title = Paragraph("Relatorio Gerencial de Garantias", styles["Title"])

    # Resumo por Marca
    marcas = list(
        queryset.values("marca")
        .annotate(total_q=Sum("quantidade"), total_v=Sum("valor"))
        .order_by("-total_q", "marca")
    )
    marcas_table_data = [["Marca", "Quantidade", "Valor"]]
    for m in marcas:
        marcas_table_data.append([
            Paragraph(html.escape(str(m["marca"]) or "Nao Informado"), styles["BodyText"]),
            _fmt_int_br(m["total_q"] or 0),
            _fmt_number_br(m["total_v"] or 0),
        ])
    marcas_table = Table(marcas_table_data, repeatRows=1, colWidths=[240, 100, 120])
    marcas_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    # Top 5 clientes por quantidade
    top_clientes = list(
        queryset.values("cliente__nome", "cliente__cnpj")
        .annotate(total_q=Sum("quantidade"), total_v=Sum("valor"))
        .order_by("-total_q", "cliente__nome")[:5]
    )
    top_table_data = [["Cliente", "NOTA", "Quantidade", "Valor"]]
    for c in top_clientes:
        top_table_data.append([
            Paragraph(html.escape(str(c["cliente__nome"]) or ""), styles["BodyText"]),
            Paragraph(html.escape(str(c["cliente__cnpj"]) or ""), styles["BodyText"]),
            _fmt_int_br(c["total_q"] or 0),
            _fmt_number_br(c["total_v"] or 0),
        ])
    top_table = Table(top_table_data, repeatRows=1, colWidths=[260, 160, 80, 100])
    top_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))

    # Produtos agregados
    prod_rows = list(
        queryset.values("codigo_peca")
        .annotate(total_q=Sum("quantidade"), total_v=Sum("valor"))
        .order_by("-total_q", "codigo_peca")
    )
    descricoes = _descricoes_por_codigo(prod_rows)
    produtos_table_data = [["Cod. Peca", "Descricao", "Quantidade", "Valor"]]
    for r in prod_rows:
        produtos_table_data.append([
            Paragraph(html.escape(str(r["codigo_peca"]) or ""), styles["BodyText"]),
            Paragraph(html.escape(descricoes.get(r["codigo_peca"], "")), styles["BodyText"]),
            _fmt_int_br(r["total_q"] or 0),
            _fmt_number_br(r["total_v"] or 0),
        ])
    produtos_table = Table(produtos_table_data, repeatRows=1, colWidths=[90, 250, 80, 110])
    produtos_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))

    story = [title, Spacer(1, 10),
             Paragraph("Resumo por Marca", styles["Heading2"]), Spacer(1, 4), marcas_table, Spacer(1, 12),
             Paragraph("Top 5 Clientes", styles["Heading2"]), Spacer(1, 4), top_table, Spacer(1, 12),
             Paragraph("Produtos", styles["Heading2"]), Spacer(1, 4), produtos_table]

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="garantias_gerencial.pdf"'
    return resp


def exportar_garantias_gerencial_produto_excel(queryset, codigo_peca: str):
    wb = Workbook()
    ws = wb.active
    ws.title = f"Produto {codigo_peca}"[:31]

    ws.append(["Produto", codigo_peca])
    ws.append([])

    headers = ["Cliente", "Nota", "Marca", "Defeito", "Tipo", "Valor", "Recebido em"]
    ws.append(headers)
    total = 0.0
    for g in queryset:
        valor = float(g.valor or 0)
        total += valor
        ws.append([
            getattr(g.cliente, "nome", ""),
            getattr(g, "nota_recebida", ""),
            getattr(g, "marca", "Nao Informado") or "Nao Informado",
            g.defeito,
            ("Garantia" if (getattr(g, "tipo", "garantia") == "garantia") else "Devolucao"),
            _fmt_number_br(valor),
            _fmt_date_br(g.data_recebimento),
        ])

    ws.append([])
    ws.append(["Total", "", "", "", "", _fmt_number_br(total), ""]) 

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="garantias_produto_{codigo_peca}.xlsx"'
    return resp


def exportar_garantias_gerencial_produto_pdf(queryset, codigo_peca: str):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    styles = getSampleStyleSheet()

    title = Paragraph(f"Garantias do Produto: {html.escape(str(codigo_peca))}", styles["Title"])

    headers = ["Cliente", "Nota", "Marca", "Defeito", "Tipo", "Valor", "Recebido em"]
    rows = []
    total = 0.0
    for g in queryset:
        valor = float(g.valor or 0)
        total += valor
        rows.append([
            Paragraph(html.escape(getattr(g.cliente, "nome", "")), styles["BodyText"]),
            Paragraph(html.escape(getattr(g, "nota_recebida", "")), styles["BodyText"]),
            Paragraph(html.escape(getattr(g, "marca", "Nao Informado") or "Nao Informado"), styles["BodyText"]),
            Paragraph(html.escape(g.defeito or ""), styles["BodyText"]),
            Paragraph(html.escape("Garantia" if (getattr(g, "tipo", "garantia") == "garantia") else "Devolucao"), styles["BodyText"]),
            _fmt_number_br(valor),
            _fmt_date_br(g.data_recebimento),
        ])

    # Ajusta a largura das colunas para caber nas margens
    # Usa proporções para as 5 primeiras e calcula a última como sobra
    # Adiciona uma margem interna horizontal para não colar nas bordas da página
    inner_margin = 16  # px a cada lado dentro da área útil
    available_width = max(100, doc.width - (inner_margin * 2))
    base_ratios = [0.27, 0.14, 0.12, 0.24, 0.08, 0.09]  # Cliente, Nota, Marca, Defeito, Tipo, Valor
    first_widths = [available_width * r for r in base_ratios]
    last_width = max(90, available_width - sum(first_widths))  # Recebido em
    col_widths = first_widths + [last_width]

    data = [headers] + rows + [["", "", "", "", "Total", _fmt_number_br(total), ""]]
    table = Table(data, repeatRows=1, colWidths=col_widths, hAlign='CENTER')
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (5, 1), (5, -1), "RIGHT"),
        ("ALIGN", (6, 1), (6, -1), "CENTER"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor('#eef2f7')),
    ]))

    story = [title, Spacer(1, 10), table]
    doc.build(story)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="garantias_produto_{codigo_peca}.pdf"'
    return resp
