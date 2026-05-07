import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

PADRAO_COLORS = {
    'Fluente': '#004D40',
    'Não Fluente': '#287B65',
    'Frases': '#62CCB0',
    'Palavras': '#42A5F5',
    'Sílabas': '#90CAF9',
    'Não Leitor': '#808080',
    'Não Avaliado': '#c33d33'
}

def create_individual_chart(df_year_ano, title, output_filename, chart_height=3.0, is_last_row=False):
    """Cria um pequeno gráfico de barras horizontais para um ano de escolaridade e ano civil específico."""
    if df_year_ano.empty:
        return None
        
    # Agrupar por resultado pegando a soma da porcentagem e da quantidade
    res_df = df_year_ano.groupby('RESULTADO').agg({
        'QTD': 'sum'
    })
    
    order = ['Fluente', 'Não Fluente', 'Frases', 'Palavras', 'Sílabas', 'Não Leitor', 'Não Avaliado']
    final_res = pd.DataFrame(0.0, index=order, columns=['PERCENTUAL_PADRAO', 'QTD'])
    for res in order:
        if res in res_df.index:
            final_res.loc[res, 'QTD'] = res_df.loc[res, 'QTD']
            
    # Recalcular porcentagem sobre o total regional/escolar para evitar erros de soma (>100%)
    total_qtd = final_res['QTD'].sum()
    if total_qtd > 0:
        final_res['PERCENTUAL_PADRAO'] = (final_res['QTD'] / total_qtd) * 100
    else:
        final_res['PERCENTUAL_PADRAO'] = 0.0
    
    # Filtrar apenas o que for maior que zero
    final_res = final_res[final_res['QTD'] > 0]
    
    if final_res.empty:
        return None

    final_res = final_res.iloc[::-1]
    
    # FIGSIZE aumentado para dar mais largura
    # Aumentando largura base de 6.0 para 8.0 para esticar conforme pedido
    fig, ax = plt.subplots(figsize=(8.0, chart_height))
    colors_list = [PADRAO_COLORS[c] for c in final_res.index]
    
    # Gap menor: height 0.85
    bars = ax.barh(final_res.index, final_res['PERCENTUAL_PADRAO'], color=colors_list, height=0.85)
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=10, loc='center')
    
    # Range máximo dinâmico
    max_perc = final_res['PERCENTUAL_PADRAO'].max()
    ax.set_xlim(0, max_perc + 20) # 20 para garantir espaço para o texto maior
    
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Adicionar labels no formato "QTD (PERC%)"
    x_limit = max_perc + 20
    for i, bar in enumerate(bars):
        perc = bar.get_width()
        res_label = final_res.index[i]
        qtd = final_res.loc[res_label, 'QTD']
        
        if perc > 0 or qtd > 0:
            label_text = f'{qtd:.0f} ({perc:.1f}%)'
            # Só coloca dentro se for a última fileira E a barra for larga o suficiente (metade do limite x)
            if is_last_row and perc > (x_limit / 2):
                # Label centralizado dentro da barra para evitar o QR code no canto
                x_pos = bar.get_x() + bar.get_width() / 2
                ax.text(x_pos, bar.get_y() + bar.get_height()/2, label_text, 
                        va='center', ha='center', fontsize=12, fontweight='bold', color='white')
            else:
                # Caso contrário, mantém fora (padrão)
                ax.text(perc + 1, bar.get_y() + bar.get_height()/2, label_text, 
                        va='center', fontsize=14, fontweight='bold', color='#1A1A1A')
            
    ax.tick_params(axis='y', labelsize=14)
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return output_filename

def render(c, width, height, df_escola):
    draw_header(c, width, height)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "Fluência Leitora")
    c.setFillColorRGB(0, 0, 0)
    
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO
    style_n.fontSize = 11
    style_n.leading = 14
    style_n.alignment = 4
    
    texto = (
        "<b>Fluência Leitora</b> é a habilidade de decifrar e compreender as palavras com facilidade, permitindo que o leitor se concentre no "
        "significado do texto, em vez de focar no reconhecimento individual das palavras. Uma leitura fluente é caracterizada por uma leitura "
        "natural, sem grandes pausas ou erros, e com a utilização correta dos aspectos rítmicos e tonais do discurso."
    )
    p = Paragraph(texto, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    curr_y = height - 5.1*cm - p_h
    p.drawOn(c, 2*cm, curr_y)
    
    curr_y -= 0.5*cm
    
    if df_escola.empty:
        draw_footer(c, width, height, qr_code_name="fluencia_leitora")
        c.showPage()
        return

    anos_escolaridade = sorted(df_escola['ANO_ESCOLARIDADE'].unique())
    num_anos = len(anos_escolaridade)
    
    # Cálculo dinâmico para caber tudo na mesma página
    # Espaço disponível ~ 21cm (A4 total é ~29cm, Header/Footer tiram uns 8cm)
    available_h = curr_y - 2.0*cm # Margem inferior reduzida
    row_h = available_h / num_anos
    section_title_h = 0.35*cm 
    chart_h_render = row_h - section_title_h 
    
    # chart_h_fig (polegadas) proporcional - Multiplicador aumentado para esticar mais
    chart_h_fig = (chart_h_render / cm) / 2.54 * 1.8 
    
    # Reduzindo margens laterais para 1.5cm e gap para 0.2cm
    chart_w = (width - 3.2*cm) / 2 
    col1_x = 1.5*cm
    col2_x = width - 1.5*cm - chart_w
    
    for ano_esc in anos_escolaridade:
        # Seção estilo Distorção - Centralizada e fonte 11 negrito
        c.setFillColor(colors.HexColor('#1565C0'))
        c.setFont(FONT_CABECALHO, 11) # Aumentado para 11
        c.drawCentredString(width / 2.0, curr_y - 0.2*cm, ano_esc)
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.setLineWidth(0.4)
        c.line(1.5*cm, curr_y - 0.3*cm, width - 1.5*cm, curr_y - 0.3*cm)
        
        curr_y -= section_title_h
        
        # Filtros e Geração
        df_24 = df_escola[(df_escola['ANO_ESCOLARIDADE'] == ano_esc) & (df_escola['ANO'].astype(str).str.startswith('2024'))]
        df_25 = df_escola[(df_escola['ANO_ESCOLARIDADE'] == ano_esc) & (df_escola['ANO'].astype(str).str.startswith('2025'))]
        
        fname_24 = f"tmp_fluencia_{ano_esc.replace(' ','_')}_2024.png"
        fname_25 = f"tmp_fluencia_{ano_esc.replace(' ','_')}_2025.png"
        
        is_last = (ano_esc == anos_escolaridade[-1])
        
        img_24 = create_individual_chart(df_24, "2024 - Av. de Saída", fname_24, chart_height=chart_h_fig, is_last_row=is_last)
        img_25 = create_individual_chart(df_25, "2025 - Av. de Saída", fname_25, chart_height=chart_h_fig, is_last_row=is_last)
        
        if img_24:
            # drawImage com a nova largura/altura máximas
            c.drawImage(img_24, col1_x, curr_y - chart_h_render, width=chart_w, height=chart_h_render, preserveAspectRatio=True)
            os.remove(img_24)
        else:
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.rect(col1_x, curr_y - chart_h_render + 0.2*cm, chart_w, chart_h_render - 0.4*cm, stroke=1, fill=0)
            c.setFont(FONT_TEXTO, 8)
            c.drawCentredString(col1_x + chart_w/2, curr_y - chart_h_render/2, "Sem dados 2024")

        if img_25:
            c.drawImage(img_25, col2_x, curr_y - chart_h_render, width=chart_w, height=chart_h_render, preserveAspectRatio=True)
            os.remove(img_25)
        else:
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.rect(col2_x, curr_y - chart_h_render + 0.2*cm, chart_w, chart_h_render - 0.4*cm, stroke=1, fill=0)
            c.setFont(FONT_TEXTO, 8)
            c.drawCentredString(col2_x + chart_w/2, curr_y - chart_h_render/2, "Sem dados 2025")

        curr_y -= chart_h_render
        
    draw_footer(c, width, height, qr_code_name="fluencia_leitora")
    c.showPage()
