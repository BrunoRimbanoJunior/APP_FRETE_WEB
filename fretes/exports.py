
from io import BytesIO
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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
