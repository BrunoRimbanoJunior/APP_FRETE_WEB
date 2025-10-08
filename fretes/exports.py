import html
from decimal import Decimal
from io import BytesIO
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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
            ws.append([float(largura), float(altura), float(comprimento), quantidade])
    else:
        ws.append(["-", "-", "-", "-"])

    ws.append([])
    ws.append(["Total de volumes", total_volumes])
    ws.append(["Cubagem total (m3)", float(total_m3)])

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
                f"{largura:.2f}",
                f"{altura:.2f}",
                f"{comprimento:.2f}",
                str(quantidade),
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
        ["Total de volumes", str(total_volumes)],
        ["Cubagem total (m3)", f"{total_m3:.3f}"],
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
        "Codigo", "Descricao", "Enderecos", "Peso bruto (kg)", "Peso liquido (kg)",
        "Largura (cm)", "Altura (cm)", "Comprimento (cm)"
    ]
    ws.append(headers)

    for produto in queryset:
        ws.append([
            produto.codigo,
            produto.descricao,
            produto.enderecos or "",
            float(produto.peso_bruto_kg or 0),
            float(produto.peso_liquido_kg or 0),
            float(produto.largura_cm or 0),
            float(produto.altura_cm or 0),
            float(produto.comprimento_cm or 0),
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
        rows.append([
            f.data_calculo.strftime("%d/%m/%Y") if f.data_calculo else "",
            f.numero_pedido,
            f.numero_nota or "",
            f.valor_nota or 0,
            f.kg_nota,
            str(f.carrier),
            f.m3,
            f.peso_cubico,
            f.peso_usado,
            f.frete_total,
        ])
    return rows

def exportar_fretes_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Fretes"

    headers = ["Data", "Pedido", "Nota", "Valor Nota", "KG Nota", "Transportadora",
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

    headers = ["Data", "Pedido", "Nota", "Valor Nota", "KG Nota", "Transportadora",
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
            "Atendido" if g.nota_retorno else "Em aberto",
        ])
    return rows


def exportar_garantias_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Garantias"

    headers = [
        "ID", "Cliente", "CNPJ", "Cod. Peca", "Marca", "Defeito", "Lote",
        "Nota Recebida", "Valor", "Mao de Obra", "Valor M.O.", "Recebido em", "Nota Retorno", "Retorno em", "Status"
    ]
    ws.append(headers)
    for row in _garantias_rows(queryset):
        ws.append(row)

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
        "Nota Recebida", "Valor", "Mao de Obra", "Valor M.O.", "Recebido em", "Nota Retorno", "Retorno em", "Status"
    ]
    rows = _garantias_rows(queryset)

    total_valor = sum((r[8] or 0) for r in rows)
    total_mo = sum((r[10] or 0) for r in rows)

    totals_row = [""] * len(headers)
    totals_row[7] = "Totais"
    totals_row[8] = total_valor
    totals_row[10] = total_mo

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
        valor_fmt = f"{float(valor):.2f}" if isinstance(valor, (int, float, Decimal)) else str(valor)
        valor_cell = Paragraph(html.escape(valor_fmt), small_right)
        mao = Paragraph(html.escape(str(row[9])), small_center)
        valor_mo = row[10] if row[10] not in (None, "") else 0
        valor_mo_fmt = f"{float(valor_mo):.2f}" if isinstance(valor_mo, (int, float, Decimal)) else str(valor_mo)
        valor_mo_cell = Paragraph(html.escape(valor_mo_fmt), small_right)
        recebido_em = Paragraph(html.escape(str(row[11] or "")), small_center)
        nota_retorno = Paragraph(html.escape(str(row[12] or "")), small_left)
        retorno_em = Paragraph(html.escape(str(row[13] or "")), small_center)
        status = Paragraph(html.escape(str(row[14])), small_center)

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
            status,
        ])

    ratios = [0.04, 0.13, 0.09, 0.06, 0.07, 0.11, 0.05, 0.06, 0.05, 0.05, 0.05, 0.06, 0.06, 0.06, 0.06]
    available_width = doc.width
    col_widths = [available_width * r for r in ratios]

    table = Table(table_data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
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
