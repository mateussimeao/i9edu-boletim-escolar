import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pdf_engine import draw_header, draw_footer

try:
    from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO
except ImportError:
    FONT_TITULO = 'Helvetica-Bold'
    FONT_CABECALHO = 'Helvetica-Bold'
    FONT_NUMERO = 'Helvetica-Bold'
    FONT_TEXTO = 'Helvetica'

def _create_grouped_bar_chart(df_ano_esc, output_filename, chart_height=3.0):
    """
    Gera um gráfico de barras agrupadas: LP vs MAT.
    Dentro de cada disciplina: 2023-2, 2024-3, 2025-2 e Meta 2026.
    """
    labels = ['Língua Portuguesa', 'Matemática']
    x = np.arange(len(labels))
    width = 0.16  # Largura das barras
    
    fig, ax = plt.subplots(figsize=(6.8, chart_height))
    
    def get_val(df_sub, col):
        if df_sub.empty: return 0
        val = df_sub[col].iloc[0]
        try: return float(str(val).replace(',', '.'))
        except: return 0
        
    df_23 = df_ano_esc[df_ano_esc['ANO_AVALIACAO'] == '2023-2']
    df_24 = df_ano_esc[df_ano_esc['ANO_AVALIACAO'] == '2024-3']
    df_25 = df_ano_esc[df_ano_esc['ANO_AVALIACAO'] == '2025-2']
    
    # Lógica de fallback para Meta
    df_meta_row = df_25
    meta_year_suffix = "2026"
    
    if df_meta_row.empty:
        if not df_24.empty:
            df_meta_row = df_24
            meta_year_suffix = str(int(df_24['ANO_AVALIACAO'].iloc[0][:4]) + 1)
        elif not df_23.empty:
            df_meta_row = df_23
            meta_year_suffix = str(int(df_23['ANO_AVALIACAO'].iloc[0][:4]) + 1)

    # LP Values
    lp_23 = get_val(df_23, 'PROF_POR')
    lp_24 = get_val(df_24, 'PROF_POR')
    lp_25 = get_val(df_25, 'PROF_POR')
    lp_meta = get_val(df_meta_row, 'META_POR') 
    
    # MAT Values
    mat_23 = get_val(df_23, 'PROF_MAT')
    mat_24 = get_val(df_24, 'PROF_MAT')
    mat_25 = get_val(df_25, 'PROF_MAT')
    mat_meta = get_val(df_meta_row, 'META_MAT')
    
    v_23 = [lp_23, mat_23]
    v_24 = [lp_24, mat_24]
    v_25 = [lp_25, mat_25]
    v_meta = [lp_meta, mat_meta]
    
    # Paleta de cores para LP (Azul) e MAT (Laranja)
    colors_23 = ['#A9D6E5', '#FFE4B5'] 
    colors_24 = ['#61A5C2', '#FFB703']
    colors_25 = ['#2C7DA0', '#FB8500']
    colors_meta = ['#014F86', '#D00000'] 
    
    rects1 = ax.bar(x - 1.5*width, v_23, width, label='2023-2', color=colors_23)
    rects2 = ax.bar(x - 0.5*width, v_24, width, label='2024-3', color=colors_24)
    rects3 = ax.bar(x + 0.5*width, v_25, width, label='2025-2', color=colors_25)
    rects4 = ax.bar(x + 1.5*width, v_meta, width, label='Meta 2026', color=colors_meta)
    
    def autolabel(rects, prefix=''):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{prefix}:\n{height:.0f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), 
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, 
                            fontweight='bold' if prefix.lower().startswith('meta') else 'normal')

    autolabel(rects1, '2023')
    autolabel(rects2, '2024')
    autolabel(rects3, '2025')
    autolabel(rects4, f'Meta\n{meta_year_suffix}')
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, fontweight='bold')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return output_filename

def render(c, width, height, df_metas=None):
    draw_header(c, width, height)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.2*cm, "Metas")
    c.setFillColorRGB(0, 0, 0)
    
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO
    style_n.fontSize = 11
    style_n.leading = 14
    style_n.alignment = 4
    
    texto = (
        "As <b>metas de proficiência</b> indicam o nível de aprendizagem que os alunos devem alcançar em Língua "
        "Portuguesa e Matemática dentro de um período determinado. "
        "Apresentamos a meta prevista para o ano de 2026, definida com base na avaliação de saída do Prosa 2025."
    )
    p = Paragraph(texto, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    curr_y = height - 4.7*cm - p_h
    p.drawOn(c, 2*cm, curr_y)
    curr_y -= 0.6*cm
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 13)
    c.drawCentredString(width / 2.0, curr_y, "Avaliações de Saída")
    curr_y -= 0.7*cm

    if df_metas is None or df_metas.empty:
        return

    df_filtered = df_metas[df_metas['ANO_AVALIACAO'].astype(str).isin(['2023-2', '2024-3', '2025-2'])]
    if df_filtered.empty:
        return

    anos_escolaridade = sorted(df_filtered['ANO_ESCOLARIDADE'].unique()) if 'ANO_ESCOLARIDADE' in df_filtered.columns else []
    # anos_escolaridade = [a for a in anos_escolaridade if str(a).strip() in ['2', '5', '9', '2º Ano', '5º Ano', '9º Ano'] or a in [2,5,9]]
    num_anos = len(anos_escolaridade)
    if num_anos == 0:
        return

    section_title_h = 0.4 * cm 
    chart_h_render = 5.8 * cm # Aumentado de 5.0
    chart_h_fig = 2.8 # Aumentado de 2.4
    
    for ano_esc in anos_escolaridade:
        c.setFillColor(colors.HexColor('#1565C0'))
        c.setFont(FONT_CABECALHO, 11) 
        c.drawCentredString(width / 2.0, curr_y - 0.2*cm, f"{ano_esc}º Ano" if str(ano_esc).isdigit() else str(ano_esc))
        curr_y -= section_title_h
        
        df_ano = df_filtered[df_filtered['ANO_ESCOLARIDADE'] == ano_esc]
        fname = f"tmp_metas_{str(ano_esc).replace(' ', '_')}.png"
        
        chart_path = _create_grouped_bar_chart(df_ano, fname, chart_height=chart_h_fig if chart_h_fig > 1.5 else 2.5)
        
        w_img = width - 2.6*cm  # Margens menores (1.3cm cada)
        x_img = 1.3*cm
        c.drawImage(chart_path, x_img, curr_y - chart_h_render + 0.1*cm, width=w_img, height=chart_h_render - 0.1*cm, preserveAspectRatio=True)
        os.remove(chart_path)
        
        curr_y -= chart_h_render

    draw_footer(c, width, height, qr_code_name="Metas")
    c.showPage()
