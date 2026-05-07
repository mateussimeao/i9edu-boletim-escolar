import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pdf_engine import draw_header, draw_footer
from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO

def create_grouped_bar_chart(df, disciplina, output_filename):
    df_filter = df[df['TRI_NM_DISCIPLINA'] == disciplina].copy()
    if df_filter.empty:
        return None
        
    # Excluir '5. Não Avaliado'
    if 'TRI_PADRAO_DESEMPENHO' in df_filter.columns:
        df_filter = df_filter[df_filter['TRI_PADRAO_DESEMPENHO'] != '5. Não Avaliado']
        
    # Agrupar por Ano de Escolarização
    pivot_df = df_filter.pivot_table(
        index='TRI_ANO_ESCOLARIDADE',
        columns='ANO',
        values='AVG_PROFICIENCIA',
        aggfunc='mean'
    ).fillna(0)
    
    # Garantir que 2023 e 2024 existam
    for year in ['2023', '2024']:
        if year not in pivot_df.columns:
            pivot_df[year] = 0.0
            
    pivot_df = pivot_df[['2023', '2024']]
    
    labels = pivot_df.index.tolist()
    x = np.arange(len(labels))
    width = 0.35  # Largura de cada barra
    spacing = 0.045 # Espaço entre as barras do mesmo grupo
    
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    # Barras de 2023 e 2024
    rects1 = ax.bar(x - width/2 - spacing/2, pivot_df['2023'], width, label='2023', color='#90CAF9')
    rects2 = ax.bar(x + width/2 + spacing/2, pivot_df['2024'], width, label='2024', color='#1565C0')
    
    ax.set_title(disciplina, fontsize=12, fontweight='bold', pad=22)
    ax.set_ylabel('')
    ax.set_yticks([])
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight='bold', fontsize=10)
    
    def autolabel(rects):
        fsize = 12 if len(labels) <= 5 else 9
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.0f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=fsize, fontweight='bold', color='#444444')

    autolabel(rects1)
    autolabel(rects2)
        
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.legend(title='', bbox_to_anchor=(0, 1.03), loc='lower left', ncol=2, frameon=False, fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    return output_filename

def render(c, width, height, df_escola):
    draw_header(c, width, height)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "SABE - Proficiência")
    c.setFillColorRGB(0, 0, 0)
    
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO
    style_n.fontSize = 11
    style_n.leading = 14
    style_n.alignment = 4
    
    texto_sabe = (
        "O <b>SABE</b> (Sistema de Avaliação Baiano de Educação) é um sistema de avaliação externa que visa analisar o "
        "desempenho dos estudantes nas escolas públicas e privadas da Bahia, em diferentes áreas do conhecimento, como "
        "Língua Portuguesa e Matemática."
    )
    p = Paragraph(texto_sabe, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    curr_y = height - 5.1*cm - p_h
    p.drawOn(c, 2*cm, curr_y)
    
    curr_y -= 1.2*cm
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_CABECALHO, 14)
    c.drawCentredString(width / 2.0, curr_y, "Avaliações de Proficiência")
    c.setFillColorRGB(0, 0, 0)
    
    chart_w = width - 4*cm
    chart_h = 7.5*cm 
    curr_y -= 0.5*cm
    
    # Gráfico Língua Portuguesa
    img_lp = create_grouped_bar_chart(df_escola, 'Língua Portuguesa', "tmp_sabe_prof_lp.png")
    if img_lp:
        curr_y -= chart_h
        c.drawImage(img_lp, 2*cm, curr_y, width=chart_w, height=chart_h, preserveAspectRatio=True)
        os.remove(img_lp)
        
    # Gráfico Matemática
    curr_y -= 0.5*cm
    img_mat = create_grouped_bar_chart(df_escola, 'Matemática', "tmp_sabe_prof_mat.png")
    if img_mat:
        curr_y -= chart_h
        c.drawImage(img_mat, 2*cm, curr_y, width=chart_w, height=chart_h, preserveAspectRatio=True)
        os.remove(img_mat)
        
    draw_footer(c, width, height)
    c.showPage()
