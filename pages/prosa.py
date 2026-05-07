import os
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pdf_engine import draw_header, draw_footer
from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO

PADRAO_COLORS = {
    '4.Abaixo do Básico': '#e0493e',
    '3.Básico': '#f7b639',
    '2.Adequado': '#3f99de',
    '1.Avançado': '#6aab5b'
}

def create_stacked_bar_chart(df, disciplina, ano, output_filename):
    df_filter = df[(df['TRI_NM_DISCIPLINA'] == disciplina) & (df['ANO'] == ano)]
    if df_filter.empty:
        return None
        
    # Agrupar por quantidade de alunos para recalcular a porcentagem corretamente em agregações
    pivot_df = df_filter.pivot_table(
        index='TRI_ANO_ESCOLARIDADE',
        columns='TRI_PADRAO_DESEMPENHO',
        values='QTD_ALUNOS',
        aggfunc='sum'
    ).fillna(0)
    
    if pivot_df.empty or len(pivot_df.columns) == 0:
        return None
    
    # Calcular percentual por linha (para que a soma de cada linha seja 100)
    row_totals = pivot_df.sum(axis=1)
    # Evitar divisão por zero caso haja linhas sem alunos
    pivot_df = pivot_df.div(row_totals, axis=0).replace([np.inf, -np.inf], 0).fillna(0) * 100
    
    # Inverter ordem das colunas para inverter o empilhamento das barras (Abaixo -> Avançado)
    pivot_df = pivot_df[pivot_df.columns[::-1]]
    
    # Inverter a ordem do eixo Y
    pivot_df = pivot_df.iloc[::-1]
    
    default_colors = ['#9b59b6', '#34495e', '#16a085', '#d35400', '#c0392b', '#7f8c8d']
    colors_list = []
    default_idx = 0
    for col in pivot_df.columns:
        col_str = str(col)
        if col_str in PADRAO_COLORS:
            colors_list.append(PADRAO_COLORS[col_str])
        else:
            colors_list.append(default_colors[default_idx % len(default_colors)])
            default_idx += 1
    
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    pivot_df.plot(kind='barh', stacked=True, color=colors_list, ax=ax, width=0.8)
    
    ax.set_title(f"{ano} - Av. de Saída", fontsize=11, fontweight='bold')
    ax.set_ylabel('')
    
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Count non-zero padrões per bar row to decide label strategy
    num_bars = len(pivot_df.index)
    nonzero_per_row = [0] * num_bars
    for container in ax.containers:
        for i, bar in enumerate(container):
            if bar.get_width() > 0:
                nonzero_per_row[i] += 1

    # Adaptive font size based on percentage value
    def _adaptive_fontsize(val):
        if val >= 15:
            return 13
        elif val >= 7:
            return 11
        else:
            return 9

    # Smart label positioning: inside for >= 5%, outside for small values
    for idx, container in enumerate(ax.containers):
        col_name = str(pivot_df.columns[idx]) if idx < len(pivot_df.columns) else ''
        bar_color = PADRAO_COLORS.get(col_name, '#333333')
        
        for i, bar in enumerate(container):
            val = bar.get_width()
            if val >= 5:
                # Label inside bar, adaptive font size
                x_pos = bar.get_x() + bar.get_width() / 2
                y_pos = bar.get_y() + bar.get_height() / 2
                ax.text(x_pos, y_pos, f'{val:.0f}%', va='center', ha='center',
                        fontsize=_adaptive_fontsize(val), fontweight='bold', color='white')
            elif 0 < val < 6 and nonzero_per_row[i] < 3:
                # Label outside bar, smaller font
                x_pos = bar.get_x() + bar.get_width() + 0.3
                y_pos = bar.get_y() + bar.get_height() / 2
                ax.text(x_pos, y_pos, f'{val:.0f}%', va='center', ha='left',
                        fontsize=13, fontweight='bold', color=bar_color)
    
    ax.tick_params(axis='y', which='major', labelsize=11)
    ax.get_legend().remove()
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    return output_filename

def render(c, width, height, df_escola):
    draw_header(c, width, height)
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "Prosa")
    c.setFillColorRGB(0, 0, 0)
    
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO
    style_n.fontSize = 11
    style_n.leading = 14
    style_n.alignment = 4
    
    texto_prosa = (
        "<b>PROSA</b> (Programa Salvador Avalia): tem o objetivo de realizar um diagnóstico do aprendizado dos alunos da rede "
        "municipal de ensino e fornecer subsídios para o aprimoramento da qualidade do ensino. A avaliação abrange as disciplinas "
        "de Língua Portuguesa e Matemática, e o resultado é utilizado para identificar pontos de melhoria no processo de ensino-aprendizagem."
    )
    p = Paragraph(texto_prosa, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    p.drawOn(c, 2*cm, height - 5.1*cm - p_h)
    
    legenda_path = "assets/legenda.jpg"
    if os.path.exists(legenda_path):
        c.drawImage(legenda_path, width/2 - 4*cm, height - 9.0*cm, 8*cm, 1*cm, preserveAspectRatio=True, anchor='s')
    else:
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(width/2 - 4*cm, height - 9.0*cm, 8*cm, 1*cm, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont(FONT_TEXTO, 10)
        c.drawCentredString(width/2, height - 8.6*cm, "[ LEGENDA PLACEHOLDER ]")
    
    chart_w = 8.5 * cm
    chart_h = 6.8 * cm
    
    # Língua Portuguesa
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_CABECALHO, 12)
    c.drawCentredString(width / 2.0, height - 10.0*cm, "Língua Portuguesa")
    
    img_lp_24 = create_stacked_bar_chart(df_escola, 'Língua Portuguesa', '2024', "tmp_lp_2024.png")
    img_lp_25 = create_stacked_bar_chart(df_escola, 'Língua Portuguesa', '2025', "tmp_lp_2025.png")
    
    y_lp = height - 17.3*cm
    if img_lp_24:
        c.drawImage(img_lp_24, 1.5*cm, y_lp, width=chart_w, height=chart_h)
    if img_lp_25:
        c.drawImage(img_lp_25, 1.5*cm + chart_w + 0.5*cm, y_lp, width=chart_w, height=chart_h)
        
    # Matemática
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_CABECALHO, 12)
    c.drawCentredString(width / 2.0, height - 18.3*cm, "Matemática")
    
    img_mat_24 = create_stacked_bar_chart(df_escola, 'Matemática', '2024', "tmp_mat_2024.png")
    img_mat_25 = create_stacked_bar_chart(df_escola, 'Matemática', '2025', "tmp_mat_2025.png")
    
    y_mat = height - 25.6*cm
    if img_mat_24:
        c.drawImage(img_mat_24, 1.5*cm, y_mat, width=chart_w, height=chart_h)
    if img_mat_25:
        c.drawImage(img_mat_25, 1.5*cm + chart_w + 0.5*cm, y_mat, width=chart_w, height=chart_h)

    for img in [img_mat_24, img_mat_25, img_lp_24, img_lp_25]:
        if img and os.path.exists(img):
            os.remove(img)
            
    #draw_footer(c, width, height, qr_code_name="prosa")
    draw_footer(c, width, height)
    c.showPage()
