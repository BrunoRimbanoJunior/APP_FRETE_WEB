from django.http import HttpResponse
from openpyxl import Workbook
from .models import FreteCalculado
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def exportar_fretes_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Fretes"

    headers = ["Data", "Pedido", "Nota", "Valor Nota", "KG Nota", "Transportadora",
               "m³", "Peso Cúbico", "Peso Usado", "Total (R$)"]
    ws.append(headers)

    for f in queryset:
        ws.append([
            f.data_calculo.isoformat(),
            f.numero_pedido,
            f.numero_nota,
            float(f.valor_nota or 0),
            float(f.kg_nota),
            f.carrier.nome if f.carrier else "",
            float(f.m3),
            float(f.peso_cubico),
            float(f.peso_usado),
            float(f.frete_total),
        ])

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="fretes.xlsx"'
    wb.save(resp)
    return resp




def exportar_fretes_pdf(queryset):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)

    data = [["Data","Pedido","Nota","Valor Nota","KG Nota","Transportadora","m³","Peso Cúbico","Peso Usado","Total (R$)"]]
    for f in queryset:
        data.append([
            f.data_calculo.isoformat(),
            f.numero_pedido,
            f.numero_nota,
            f.valor_nota or 0,
            f.kg_nota,
            f.carrier.nome if f.carrier else "",
            f.m3, f.peso_cubico, f.peso_usado, f.frete_total
        ])

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
    title = Paragraph("Relatório de Fretes", styles["Title"])
    story = [title, table]
    doc.build(story)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="fretes.pdf"'
    return resp
