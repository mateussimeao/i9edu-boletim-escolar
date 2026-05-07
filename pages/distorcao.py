import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pdf_engine import draw_header, draw_footer

try:
    from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO
except ImportError:
    FONT_TITULO = 'Helvetica-Bold'
    FONT_CABECALHO = 'Helvetica-Bold'
    FONT_NUMERO = 'Helvetica-Bold'
    FONT_TEXTO = 'Helvetica'

def get_color_for_distorcao(val):
    if pd.isna(val):
        return "#808080"
    if val <= 5:
        return "#46c646" # verde
    elif val <= 15:
        return "#ffcf02" # amarelo
    elif val <= 30:
        return "#f8981d" # laranja
    else:
        return "#f93f17" # vermelho

def _draw_kpi(c, x, y, w, h, title, value, color_hex):
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_CABECALHO, 10)
    c.drawCentredString(x + w / 2, y + h - 0.4 * cm, title)

    c.setFillColor(colors.HexColor(color_hex))
    c.setFont(FONT_NUMERO, 20)
    c.drawCentredString(x + w / 2, y + h / 2 - 0.6 * cm, str(value))

def create_horizontal_grouped_bar_chart(df, max_year, output_filename):
    years = [max_year - 1, max_year]
    df_filter = df[df['TXDIS_ANO'].isin(years)].copy()
    if df_filter.empty:
        return None
        
    pivot_df = df_filter.pivot_table(
        index='TXDIS_ANO_ESCOLARIDADE',
        columns='TXDIS_ANO',
        values='AVG_TX_DISTORCAO',
        aggfunc='mean'
    )
    
    for y in years:
        if y not in pivot_df.columns:
            pivot_df[y] = 0.0
            
    # Inverter ordem das colunas para que o menor ano (2024) apareça EM CIMA do cluster no gráfico barh
    pivot_df = pivot_df[[max_year, max_year - 1]]
    
    # Inverter ordem para manter menor ano letivo no topo do eixo Y em um barh
    pivot_df = pivot_df.iloc[::-1]
    
    n_rows = len(pivot_df)
    fig_height = max(4.0, n_rows * 0.8)
    
    fig, ax = plt.subplots(figsize=(7.5, fig_height))
    
    # Inverter paleta para bater com as colunas invertidas
    color_palette = ['#1565C0', '#90CAF9'] 
    
    pivot_df.plot(kind='barh', color=color_palette, ax=ax, width=0.7)
    
    ax.set_title("Distorção por Ano de Escolarização", fontsize=10, fontweight='bold', color='#333333', pad=25)
    ax.set_ylabel('')
    ax.set_xlabel('')
    
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    
    for container in ax.containers:
        labels = [f'{v.get_width():.1f}%' if v.get_width() > 0 else '' for v in container]
        ax.bar_label(container, labels=labels, label_type='edge', padding=3, fontsize=9, color='#555555', fontweight='bold')
        
    ax.tick_params(axis='y', which='major', labelsize=10, colors='#333333')
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')
    
    # Legenda superior horizontal MANUAL para manter a ordem tradicional (Menor à esquerda)
    handles = [Rectangle((0,0),1,1, color='#90CAF9'), Rectangle((0,0),1,1, color='#1565C0')]
    labels = [str(max_year - 1), str(max_year)]
    ax.legend(handles, labels, title='', bbox_to_anchor=(0.5, 1.01), loc='lower center', ncol=2, fontsize=9, frameon=False)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return output_filename

def render(c, width, height, df_distorcao):
    if df_distorcao is None or df_distorcao.empty:
        return
    df_distorcao['TXDIS_ETAPA'] = df_distorcao['TXDIS_ETAPA'].replace('Anos Inicias', 'Anos Iniciais')    
    etapas = ['Anos Iniciais', 'Anos Finais']
    for etapa in etapas:
        df_etapa = df_distorcao[df_distorcao['TXDIS_ETAPA'] == etapa]
        if df_etapa.empty:
            continue
            
        draw_header(c, width, height)
        
        # Título principal
        c.setFillColor(colors.HexColor('#056cad'))
        c.setFont(FONT_TITULO, 17)
        c.drawCentredString(width / 2.0, height - 4.5*cm, "Distorção Idade-Série")
        c.setFillColorRGB(0, 0, 0)
        
        # Parágrafo descritivo
        styles = getSampleStyleSheet()
        style_n = styles['Normal']
        style_n.fontName = FONT_TEXTO
        style_n.fontSize = 11
        style_n.leading = 14
        style_n.alignment = 4
        
        texto = (
            "A <b>Distorção Idade-Série</b> refere-se à diferença entre a idade real de um aluno e a idade esperada "
            "para o ano em que ele está matriculado na escola, sendo considerada como defasagem de dois ou mais anos. "
            "Essa diferença pode indicar atraso escolar e pode ter diversas causas, como reprovações, evasão escolar ou "
            "dificuldades de aprendizagem."
        )
        p = Paragraph(texto, style_n)
        p_w, p_h = p.wrap(width - 4*cm, height)
        base_text_y = height - 5.2*cm - p_h
        p.drawOn(c, 2*cm, base_text_y)
        
        # Header Etapa
        c.setFillColor(colors.HexColor('#056cad'))
        c.setFont(FONT_CABECALHO, 14)
        c.drawCentredString(width / 2.0, base_text_y - 1.0*cm, etapa)
        c.setFillColorRGB(0, 0, 0)
        
        max_year = df_etapa['TXDIS_ANO'].max()
        
        # KPIs: Média da etapa, agregando os valores do agrupamento escolar
        agg_ano = df_etapa.groupby('TXDIS_ANO')['AVG_TX_DISTORCAO'].mean()
        
        v_current = agg_ano.get(max_year, None)
        v_prev = agg_ano.get(max_year - 1, None)
        
        str_current = "-"
        color_current = "#808080"
        if pd.notna(v_current):
            str_current = f"{v_current:.0f}%"
            color_current = get_color_for_distorcao(v_current)
            
        str_prev = "-"
        color_prev = "#808080"
        if pd.notna(v_prev):
            str_prev = f"{v_prev:.0f}%"
            color_prev = get_color_for_distorcao(v_prev)
            
        # Posicionar os dois KPIs de forma centralizada
        kpi_w = 4.5 * cm
        kpi_h = 2.5 * cm
        total_w = 2 * kpi_w + 1.5 * cm
        start_x = (width - total_w) / 2
        
        y_kpi = base_text_y - 4.5 * cm
        
        _draw_kpi(c, start_x, y_kpi, kpi_w, kpi_h, f"Distorção {max_year - 1}", str_prev, color_prev)
        _draw_kpi(c, start_x + kpi_w + 1.5*cm, y_kpi, kpi_w, kpi_h, f"Distorção {max_year}", str_current, color_current)
        
        # Gráficos horizontais
        chart_filename = f"tmp_distorcao_{etapa.replace(' ','')}.png"
        img_chart = create_horizontal_grouped_bar_chart(df_etapa, max_year, chart_filename)
        
        if img_chart:
            chart_y = y_kpi - 10 * cm
            chart_h = 9 * cm
            chart_w = width - 4 * cm
            chart_x = (width - chart_w) / 2.0
            c.drawImage(img_chart, chart_x, chart_y, width=chart_w, height=chart_h, preserveAspectRatio=True)
            os.remove(img_chart)
            
        #draw_footer(c, width, height, qr_code_name="taxa_distorcao")
        draw_footer(c, width, height)
        c.showPage()
