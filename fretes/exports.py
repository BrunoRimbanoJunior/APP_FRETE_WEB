
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
               "m³", "Peso Cúbico", "Peso Usado", "Total (R$)"]
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
               "m³", "Peso Cúbico", "Peso Usado", "Total (R$)"]
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
    story = [Paragraph("Relatório de Fretes", styles["Title"]), Spacer(1, 8), table]
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
            g.defeito,
            g.numero_lote or "",
            g.nota_recebida,
            g.valor,
            ("Sim" if getattr(g, "mao_de_obra", False) else "Não"),
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
        "ID", "Cliente", "CNPJ", "Cód. Peça", "Defeito", "Lote",
        "Nota Recebida", "Valor", "Mão de Obra", "Valor M.O.", "Recebido em", "Nota Retorno", "Retorno em", "Status"
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
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)

    headers = [
        "ID", "Cliente", "CNPJ", "Cód. Peça", "Defeito", "Lote",
        "Nota Recebida", "Valor", "Mão de Obra", "Valor M.O.", "Recebido em", "Nota Retorno", "Retorno em", "Status"
    ]
    rows = _garantias_rows(queryset)
    # Totais (colunas índice 7=Valor, 9=Valor M.O.)
    total_valor = sum((r[7] or 0) for r in rows)
    total_mo = sum((r[9] or 0) for r in rows)

    totals_row = [""] * len(headers)
    totals_row[6] = "Totais"
    totals_row[7] = total_valor
    totals_row[9] = total_mo

    data = [headers] + rows + [totals_row]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        # Destaque da linha de totais (última linha)
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor('#eef2f7')),
        ("ALIGN", (7, -1), (7, -1), "RIGHT"),
        ("ALIGN", (9, -1), (9, -1), "RIGHT"),
    ]))

    styles = getSampleStyleSheet()
    story = [Paragraph("Relatório de Garantias", styles["Title"]), Spacer(1, 8), table]
    doc.build(story)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="garantias.pdf"'
    return resp
