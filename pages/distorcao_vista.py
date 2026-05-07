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
    c.setFont(FONT_CABECALHO, 8) # Fonte menor para caber
    c.drawCentredString(x + w / 2, y + h - 0.3 * cm, title)

    c.setFillColor(colors.HexColor(color_hex))
    c.setFont(FONT_NUMERO, 16) # Fonte menor para caber
    c.drawCentredString(x + w / 2, y + h / 2 - 0.4 * cm, str(value))

def create_horizontal_grouped_bar_chart(df, max_year, output_filename, height_chart=4.0):
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
    pivot_df = pivot_df.iloc[::-1]
    
    n_rows = len(pivot_df)
    # Ajuste de tamanho da figura para ser mais compacta
    fig, ax = plt.subplots(figsize=(7.5, height_chart)) 
    
    # Inverter paleta para bater com as colunas invertidas
    color_palette = ['#1565C0', '#90CAF9'] 
    
    pivot_df.plot(kind='barh', color=color_palette, ax=ax, width=0.7)
    
    ax.set_title("Distorção por Ano de Escolarização", fontsize=9, fontweight='bold', color='#333333', pad=15)
    ax.set_ylabel('')
    ax.set_xlabel('')
    
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    
    for container in ax.containers:
        labels = [f'{v.get_width():.1f}%' if v.get_width() > 0 else '' for v in container]
        ax.bar_label(container, labels=labels, label_type='edge', padding=3, fontsize=8, color='#555555', fontweight='bold')
        
    ax.tick_params(axis='y', which='major', labelsize=9, colors='#333333')
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')
    
    # Legenda superior horizontal MANUAL para manter a ordem tradicional (Menor à esquerda)
    handles = [Rectangle((0,0),1,1, color='#90CAF9'), Rectangle((0,0),1,1, color='#1565C0')]
    labels = [str(max_year - 1), str(max_year)]
    ax.legend(handles, labels, title='', bbox_to_anchor=(0.5, 0.97), loc='lower center', ncol=2, fontsize=8, frameon=False)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return output_filename

def render(c, width, height, df_distorcao):
    if df_distorcao is None or df_distorcao.empty:
        return
        
    df_distorcao = df_distorcao.copy()
    df_distorcao['TXDIS_ETAPA'] = df_distorcao['TXDIS_ETAPA'].replace('Anos Inicias', 'Anos Iniciais')    
    
    draw_header(c, width, height)
    
    # Título principal
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "Distorção Idade-Série")
    c.setFillColorRGB(0,0,0)
    
    # Parágrafo descritivo (apenas uma vez)
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO
    style_n.fontSize = 11
    style_n.leading = 13
    style_n.alignment = 4
    
    texto = (
        "A <b>Distorção Idade-Série</b> refere-se à diferença entre a idade real de um aluno e a idade esperada "
        "para o ano em que ele está matriculado na escola, sendo considerada como defasagem de dois ou mais anos."
    )
    p = Paragraph(texto, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    curr_y = height - 5.0*cm - p_h
    p.drawOn(c, 2*cm, curr_y)
    
    etapas = ['Anos Iniciais', 'Anos Finais']
    # Filtrar apenas etapas que existem
    etapas_existentes = [e for e in etapas if not df_distorcao[df_distorcao['TXDIS_ETAPA'] == e].empty]
    
    if not etapas_existentes:
        c.showPage()
        return

    # Ajuste de espaço dependendo se temos 1 ou 2 etapas
    is_dual = len(etapas_existentes) == 2
    chart_h_render = 7.0*cm if is_dual else 10.0*cm
    chart_h_fig = 3.5 if is_dual else 5.0
    
    curr_y -= 0.8*cm
    
    for etapa in etapas_existentes:
        df_etapa = df_distorcao[df_distorcao['TXDIS_ETAPA'] == etapa]
        
        # Subtítulo Etapa
        c.setFillColor(colors.HexColor('#1565C0'))
        c.setFont(FONT_CABECALHO, 13)
        c.drawString(2.5*cm, curr_y, etapa)
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.setLineWidth(0.5)
        c.line(2.5*cm, curr_y - 0.2*cm, width - 2.5*cm, curr_y - 0.2*cm)
        
        curr_y -= 1.0*cm
        
        max_year = df_etapa['TXDIS_ANO'].max()
        agg_ano = df_etapa.groupby('TXDIS_ANO')['AVG_TX_DISTORCAO'].mean()
        
        # KPIs
        kpis = []
        for year in [max_year - 1, max_year]:
            val = agg_ano.get(year, None)
            kpis.append({
                "label": f"Distorção {year}",
                "value": f"{val:.0f}%" if pd.notna(val) else "-",
                "color": get_color_for_distorcao(val)
            })
            
        kpi_w = 4.0 * cm
        kpi_h = 2.0 * cm
        kpi_x = 2.5 * cm
        
        # Renderizar KPIs
        for kpi in kpis:
            _draw_kpi(c, kpi_x, curr_y - kpi_h, kpi_w, kpi_h, kpi['label'], kpi['value'], kpi['color'])
            kpi_x += kpi_w + 1.0*cm
            
        # Gráfico ao lado ou abaixo? 
        # Com dual, melhor abaixo ou lado? 
        # Vamos manter o padrão de abaixo mas mais compacto.
        
        chart_filename = f"tmp_dist_vista_{etapa.replace(' ','')}.png"
        img_chart = create_horizontal_grouped_bar_chart(df_etapa, max_year, chart_filename, height_chart=chart_h_fig)
        
        if img_chart:
            # chart_y = curr_y - kpi_h - chart_h_render - 0.5*cm
            # Na verdade, se couber ao lado dos KPIs seria bom, mas distorção tem muitos anos (1 ao 5)
            # Então melhor abaixo.
            curr_y -= (kpi_h + 0.3*cm)
            
            w_img = width - 6*cm
            x_img = (width - w_img) / 2
            
            c.drawImage(img_chart, x_img, curr_y - chart_h_render, width=w_img, height=chart_h_render, preserveAspectRatio=True)
            os.remove(img_chart)
            
            curr_y -= (chart_h_render + 0.5*cm)
        else:
            curr_y -= (kpi_h + 1.0*cm)

    draw_footer(c, width, height, qr_code_name="taxa_distorcao")
    c.showPage()
