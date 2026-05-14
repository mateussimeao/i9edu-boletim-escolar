import os
import pandas as pd
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pdf_engine import draw_header, draw_footer

# Reusar componentes do módulo original para evitar duplicação de lógica gráfica
from pages.taxa_rendimento import create_grouped_bar_chart, _draw_kpi_table

try:
    from fonts import FONT_TITULO, FONT_CABECALHO, FONT_TEXTO
except ImportError:
    FONT_TITULO = 'Helvetica-Bold'
    FONT_CABECALHO = 'Helvetica-Bold'
    FONT_TEXTO = 'Helvetica'

def _draw_kpi_table(c, x, y, width, df_etapa, max_year, font_size=10):
    years = [max_year - 2, max_year - 1, max_year]
    df_total = df_etapa[df_etapa['TXREN_ANO_ESCOLARIZACAO'] == 'Total']
    agg = df_total.groupby(['TXREN_TIPO', 'TXREN_ANO'])['TXREN_PORCENTAGEM'].mean().reset_index()
    
    def get_val(tipo, label, ano):
        v = agg[(agg['TXREN_TIPO'] == tipo) & (agg['TXREN_ANO'] == ano)]
        return f"{label}: {v.iloc[0]['TXREN_PORCENTAGEM']:.1f}%" if not v.empty else f"{label}: N/D"
        
    table_y = y - 0.2*cm
    col_w = width / 3.0
    row_h = 0.6*cm if font_size >= 10 else 0.45*cm
    
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.5)
    c.setFillColorRGB(0, 0, 0)
    c.setFont(FONT_CABECALHO, font_size)
    
    c.drawCentredString(x + col_w/2, table_y - row_h + 0.15*cm, str(years[0]))
    c.drawCentredString(x + col_w + col_w/2, table_y - row_h + 0.15*cm, str(years[1]))
    c.drawCentredString(x + 2*col_w + col_w/2, table_y - row_h + 0.15*cm, str(years[2]))
    
    rows_data = [("Aprovação", "APV"), ("Reprovação", "REP"), ("Abandono", "ABN")]
    curr_y = table_y - row_h
    c.setFont(FONT_TEXTO, font_size - 1 if font_size < 10 else font_size)
    
    for label, tipo in rows_data:
        curr_y -= row_h
        c.drawCentredString(x + col_w/2, curr_y + 0.12*cm, get_val(tipo, label, years[0]))
        c.drawCentredString(x + col_w + col_w/2, curr_y + 0.12*cm, get_val(tipo, label, years[1]))
        c.drawCentredString(x + 2*col_w + col_w/2, curr_y + 0.12*cm, get_val(tipo, label, years[2]))
        
    c.line(x + col_w, curr_y, x + col_w, table_y)
    c.line(x + 2*col_w, curr_y, x + 2*col_w, table_y)
    return curr_y - 0.3*cm

def render(c, width, height, df_taxa):
    if df_taxa is None or df_taxa.empty:
        return
        
    df_ai = df_taxa[df_taxa['TXREN_ETAPA'] == 'Anos Iniciais']
    df_af = df_taxa[df_taxa['TXREN_ETAPA'] == 'Anos Finais']
    has_ai = not df_ai.empty and not df_ai['TXREN_PORCENTAGEM'].dropna().empty
    has_af = not df_af.empty and not df_af['TXREN_PORCENTAGEM'].dropna().empty

    if not has_ai and not has_af:
        return

    draw_header(c, width, height)
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "Taxa de Rendimento")
    c.setFillColorRGB(0, 0, 0)
    
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO; style_n.fontSize = 11; style_n.leading = 14; style_n.alignment = 4
    
    texto = ("<b>Taxa de Rendimento</b> é um indicador que resume a situação dos alunos ao final do ano letivo, "
             "medindo a porcentagem de aprovações, reprovações e abandonos. É uma métrica fundamental para avaliar "
             "a qualidade e o fluxo dentro do sistema educacional.")
    p = Paragraph(texto, style_n); p_w, p_h = p.wrap(width - 4*cm, height); base_text_y = height - 5.2*cm - p_h; p.drawOn(c, 2*cm, base_text_y)

    max_year = df_taxa['TXREN_ANO'].max()
    colors_apv = ['#A5D6A7', '#66BB6A', '#2E7D32']
    colors_rep = ['#EF9A9A', '#EF5350', '#C62828']
    colors_abn = ['#FFE082', '#FFCA28', '#F57F17']
    
    curr_y = base_text_y - 0.5*cm

    if has_ai and has_af:
        col_w = (width - 4.5*cm) / 2.0
        c.setFillColor(colors.HexColor('#056cad')); c.setFont(FONT_CABECALHO, 11)
        c.drawCentredString(2*cm + col_w/2, curr_y - 0.2*cm, "Anos Iniciais")
        c.setFillColorRGB(0, 0, 0)
        y_ai = _draw_kpi_table(c, 2*cm, curr_y - 0.5*cm, col_w, df_ai, max_year, font_size=8)

        c.setFillColor(colors.HexColor('#056cad')); c.setFont(FONT_CABECALHO, 11) # Redefinir fonte
        c.drawCentredString(width/2.0 + 0.25*cm + col_w/2, curr_y - 0.2*cm, "Anos Finais")
        c.setFillColorRGB(0, 0, 0)
        y_af = _draw_kpi_table(c, width/2.0 + 0.25*cm, curr_y - 0.5*cm, col_w, df_af, max_year, font_size=8)
        
        y_after_kpi = min(y_ai, y_af)
        df_for_chart = df_taxa
    else:
        etapa_ativa = 'Anos Iniciais' if has_ai else 'Anos Finais'; df_ativa = df_ai if has_ai else df_af
        c.setFillColor(colors.HexColor('#056cad')); c.setFont(FONT_CABECALHO, 14)
        c.drawCentredString(width / 2.0, curr_y - 0.5*cm, etapa_ativa); c.setFillColorRGB(0, 0, 0)
        y_after_kpi = _draw_kpi_table(c, 2*cm, curr_y - 1.0*cm, width - 4*cm, df_ativa, max_year, font_size=10)
        df_for_chart = df_ativa

    etapa_str = "Consolidado" if (has_ai and has_af) else ('AnosIniciais' if has_ai else 'AnosFinais')
    n_anos = df_for_chart[df_for_chart['TXREN_ANO_ESCOLARIZACAO'] != 'Total']['TXREN_ANO_ESCOLARIZACAO'].nunique()
    lbl_fs = 6.5 if n_anos > 5 else None
    img_apv = create_grouped_bar_chart(df_for_chart, 'APV', max_year, f'tmp_taxa_apv_{etapa_str}.png', colors_apv, 'Aprovação', label_fontsize=lbl_fs)
    img_rep = create_grouped_bar_chart(df_for_chart, 'REP', max_year, f'tmp_taxa_rep_{etapa_str}.png', colors_rep, 'Reprovação', label_fontsize=lbl_fs)
    img_abn = create_grouped_bar_chart(df_for_chart, 'ABN', max_year, f'tmp_taxa_abn_{etapa_str}.png', colors_abn, 'Abandono', label_fontsize=lbl_fs)

    chart_available_h = y_after_kpi - 3*cm
    chart_h = min(chart_available_h / 3.0, 3.5*cm if n_anos > 5 else 4.8*cm)
    chart_w = width - 1.5*cm if n_anos > 5 else width - 4.5*cm
    chart_x = (width - chart_w) / 2.0; curr_y = y_after_kpi - chart_h
    
    if img_apv: c.drawImage(img_apv, chart_x, curr_y, width=chart_w, height=chart_h); os.remove(img_apv); curr_y -= chart_h
    if img_rep: c.drawImage(img_rep, chart_x, curr_y, width=chart_w, height=chart_h); os.remove(img_rep); curr_y -= chart_h
    if img_abn: c.drawImage(img_abn, chart_x, curr_y, width=chart_w, height=chart_h); os.remove(img_abn)

    draw_footer(c, width, height)
    c.showPage()
