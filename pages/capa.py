import os
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
from pdf_engine import draw_header
from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

def render(c, width, height, escola, regional):
    # --- PÁGINA 1: CAPA ---
    draw_header(c, width, height, is_first_page=True)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 24)
    c.drawCentredString(width / 2.0, height / 2.0 + 2*cm, "INDICADORES DA NOSSA ESCOLA - 2026")
    
    style_escola = ParagraphStyle(
        name='CapaEscola',
        fontName=FONT_CABECALHO,
        fontSize=20,
        alignment=1, # Centralizado
        leading=24,
        textColor=colors.HexColor('#056cad')
    )
    p_escola = Paragraph(escola, style_escola)
    avail_w = width - 4*cm
    p_w, p_h = p_escola.wrap(avail_w, height)
    
    curr_y = height / 2.0 + 0.5*cm
    p_escola.drawOn(c, 2*cm, curr_y - p_h)
    
    curr_y -= (p_h + 0.8*cm)
    if not (escola.startswith("REGIONAL: ") or escola.startswith("MÉDIA REGIONAL: ")):
        c.setFont(FONT_CABECALHO, 16)
        c.drawCentredString(width / 2.0, curr_y, f"Regional: {regional}")
    
    curr_y -= 0.8*cm
    c.setFillColorRGB(0, 0, 0)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.setFont(FONT_TEXTO, 12)
    c.drawCentredString(width / 2.0, curr_y, f"Gerado em: {now_str}")
    
    c.showPage()
