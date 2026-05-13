import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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

def create_grouped_bar_chart(df, tipo, max_year, output_filename, color_palette, title):
    # Filtrar tipo (APV, REP, ABN)
    df_filter = df[df['TXREN_TIPO'] == tipo].copy()
    if df_filter.empty:
        return None
    df_filter = df_filter[df_filter['TXREN_ANO_ESCOLARIZACAO'] != 'Total']
        
    years = [max_year - 2, max_year - 1, max_year]
    df_filter = df_filter[df_filter['TXREN_ANO'].isin(years)]
    if df_filter.empty:
        return None
    
    # Pivot
    pivot_df = df_filter.pivot_table(
        index='TXREN_ANO_ESCOLARIZACAO',
        columns='TXREN_ANO',
        values='TXREN_PORCENTAGEM',
        aggfunc='mean'
    )
    
    if pivot_df.empty:
        return None
    
    # Garantir que todos os anos existam na coluna
    for y in years:
        if y not in pivot_df.columns:
            pivot_df[y] = 0.0
            
    pivot_df = pivot_df[years]
    
    # pivot_df = pivot_df.iloc[::-1]  # REMOVIDO para barras verticais
    
    n_cols = len(pivot_df)
    fig_width = max(6.5, n_cols * 1.0)
    fig_height = 2.5
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    pivot_df.plot(kind='bar', color=color_palette, ax=ax, width=0.8)
    
    # Título do gráfico (Aprovação, Reprovação ou Abandono)
    ax.set_title(title, fontsize=10, fontweight='bold', color='#333333', pad=40)
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    # Configurar eixos
    ax.set_yticks([]) # Sem valores no eixo y
    ax.spines['bottom'].set_color('#cccccc')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Adicionar labels nas barras
    for container in ax.containers:
        labels = [f'{v.get_height():.0f}%' if v.get_height() == 100 else f'{v.get_height():.0f}%' if v.get_height() > 0 else '' for v in container]
        ax.bar_label(container, labels=labels, label_type='edge', padding=1, fontsize=7, color='#555555', fontweight='bold')
        
    ax.tick_params(axis='x', which='major', labelsize=10, colors='#333333', rotation=0)
    # Eixo X rótulos em negrito
    for label in ax.get_xticklabels():
        label.set_fontweight('bold')
    
    # Mover legenda para cima horizontalmente
    ax.legend(title='', bbox_to_anchor=(0.5, 1.15), loc='lower center', ncol=3, fontsize=9, frameon=False)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return output_filename

def _draw_kpi_table(c, x, y, width, height_table, df_etapa, max_year):
    years = [max_year - 2, max_year - 1, max_year]
    
    # Calcular médias por TIPO e ANO usando apenas o valor consolidado 'Total'
    df_total = df_etapa[df_etapa['TXREN_ANO_ESCOLARIZACAO'] == 'Total']
    agg = df_total.groupby(['TXREN_TIPO', 'TXREN_ANO'])['TXREN_PORCENTAGEM'].mean().reset_index()
    
    def get_val(tipo, label, ano):
        v = agg[(agg['TXREN_TIPO'] == tipo) & (agg['TXREN_ANO'] == ano)]
        val_str = "N/D"
        if not v.empty:
            val_str = f"{v.iloc[0]['TXREN_PORCENTAGEM']:.1f}%"
        return f"{label}: {val_str}"
        
    # Remover Evolução das Taxas (%)
    
    table_y = y - 0.2*cm
    col_w = width / 3.0
    row_h = 0.6*cm
    
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.5)
    
    # Cabeçalho da tabela
    c.setFillColorRGB(0, 0, 0)
    c.setFont(FONT_CABECALHO, 10)
    c.drawCentredString(x + col_w/2, table_y - row_h + 0.15*cm, str(years[0]))
    c.drawCentredString(x + col_w + col_w/2, table_y - row_h + 0.15*cm, str(years[1]))
    c.drawCentredString(x + 2*col_w + col_w/2, table_y - row_h + 0.15*cm, str(years[2]))
    
    # Linhas de dados
    rows_data = [
        ("Aprovação", "APV"),
        ("Reprovação", "REP"),
        ("Abandono", "ABN")
    ]
    
    curr_y = table_y - row_h
    c.setFont(FONT_TEXTO, 10)
    for label, tipo in rows_data:
        curr_y -= row_h
        
        c.drawCentredString(x + col_w/2, curr_y + 0.15*cm, get_val(tipo, label, years[0]))
        c.drawCentredString(x + col_w + col_w/2, curr_y + 0.15*cm, get_val(tipo, label, years[1]))
        c.drawCentredString(x + 2*col_w + col_w/2, curr_y + 0.15*cm, get_val(tipo, label, years[2]))
        
    bottom_y = curr_y
    top_y = table_y
    
    # Linhas verticais separando os 3 blocos (anos)
    c.line(x + col_w, bottom_y, x + col_w, top_y)
    c.line(x + 2*col_w, bottom_y, x + 2*col_w, top_y)
    
    return bottom_y - 0.5*cm

def render(c, width, height, df_taxa):
    if df_taxa is None or df_taxa.empty:
        return
        
    etapas = ['Anos Iniciais', 'Anos Finais']
    
    # Cores
    colors_apv = ['#A5D6A7', '#66BB6A', '#2E7D32']
    colors_rep = ['#EF9A9A', '#EF5350', '#C62828']
    colors_abn = ['#FFE082', '#FFCA28', '#F57F17']

    for etapa in etapas:
        df_etapa = df_taxa[df_taxa['TXREN_ETAPA'] == etapa]
        if df_etapa.empty:
            continue
            
        # Pular se não houver dados numéricos (ex: todos NaN)
        if df_etapa['TXREN_PORCENTAGEM'].dropna().empty:
            continue
            
        draw_header(c, width, height)
        
        c.setFillColor(colors.HexColor('#056cad'))
        c.setFont(FONT_TITULO, 17)
        c.drawCentredString(width / 2.0, height - 4.5*cm, "Taxa de Rendimento")
        c.setFillColorRGB(0, 0, 0)
        
        # Texto descritivo
        styles = getSampleStyleSheet()
        style_n = styles['Normal']
        style_n.fontName = FONT_TEXTO
        style_n.fontSize = 11
        style_n.leading = 14
        style_n.alignment = 4
        
        texto = (
            "<b>Taxa de Rendimento</b> é um indicador que resume a situação dos alunos ao final do ano letivo, "
            "medindo a porcentagem de aprovações, reprovações e abandonos. É uma métrica fundamental para avaliar "
            "a qualidade e o fluxo dentro do sistema educacional."
        )
        p = Paragraph(texto, style_n)
        p_w, p_h = p.wrap(width - 4*cm, height)
        base_text_y = height - 5.2*cm - p_h
        p.drawOn(c, 2*cm, base_text_y)
        
        # Header da etapa agora fica abaixo do parágrafo
        c.setFillColor(colors.HexColor('#056cad'))
        c.setFont(FONT_CABECALHO, 14)
        c.drawCentredString(width / 2.0, base_text_y - 1.0*cm, etapa)
        c.setFillColorRGB(0, 0, 0)
        
        text_y = base_text_y - 1.0*cm
        
        max_year = df_etapa['TXREN_ANO'].max()
        
        # Tabela KPI
        y_after_kpi = _draw_kpi_table(c, 2*cm, text_y - 0.5*cm, width - 4*cm, 4*cm, df_etapa, max_year)
        
        # Gráficos de Barras
        img_apv = create_grouped_bar_chart(df_etapa, 'APV', max_year, f'tmp_taxa_apv_{etapa.replace(" ","")}.png', colors_apv, 'Aprovação')
        img_rep = create_grouped_bar_chart(df_etapa, 'REP', max_year, f'tmp_taxa_rep_{etapa.replace(" ","")}.png', colors_rep, 'Reprovação')
        img_abn = create_grouped_bar_chart(df_etapa, 'ABN', max_year, f'tmp_taxa_abn_{etapa.replace(" ","")}.png', colors_abn, 'Abandono')
        
        # Altura disponível para gráficos
        chart_available_h = y_after_kpi - 2*cm
        chart_h = chart_available_h / 3.0
        # Limitar altura pra não distorcer muito (max 6cm)
        chart_h = min(chart_h, 5.5*cm)
        chart_w = width - 6.5*cm
        chart_x = (width - chart_w) / 2.0
        
        curr_y = y_after_kpi - chart_h
        if img_apv:
            c.drawImage(img_apv, chart_x, curr_y, width=chart_w, height=chart_h)
            os.remove(img_apv)
            curr_y -= chart_h
            
        if img_rep:
            c.drawImage(img_rep, chart_x, curr_y, width=chart_w, height=chart_h)
            os.remove(img_rep)
            curr_y -= chart_h
            
        if img_abn:
            c.drawImage(img_abn, chart_x, curr_y, width=chart_w, height=chart_h)
            os.remove(img_abn)
        
        #draw_footer(c, width, height, qr_code_name="taxa_rendimento")
        draw_footer(c, width, height)
        c.showPage()
