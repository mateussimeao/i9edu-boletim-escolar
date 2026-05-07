import os
import matplotlib.pyplot as plt
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pdf_engine import draw_header, draw_footer
from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO

# Importando a função de cores da distorção
try:
    from pages.distorcao import get_color_for_distorcao as _get_color_for_distorcao
except ImportError:
    def _get_color_for_distorcao(val):
        return "black"

def create_distribution_chart(df_mat, output_filename):
    """Gera gráfico de distribuição de alunos usando dados reais do DataFrame."""
    # Usar todos os anos de escolarização, ordenados alfabeticamente
    df_filtered = df_mat.sort_values('ANO_ESCOLARIZACAO_LISTAGEM').copy()
    
    if df_filtered.empty:
        return None
    
    anos = df_filtered['ANO_ESCOLARIZACAO_LISTAGEM'].tolist()
    total_alunos = df_filtered['QTD_MATRICULADOS'].tolist()
    pcd_alunos = df_filtered['QTD_DEFICIENTES'].tolist()
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    bar_width = 0.42
    y_pos = range(len(anos))
    
    ax.barh([y - bar_width/2 for y in y_pos], total_alunos, bar_width, label='Total de Alunos', color='#f8981d')
    ax.barh([y + bar_width/2 for y in y_pos], pcd_alunos, bar_width, label='Alunos PCD', color='#4477aa')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(anos, fontsize=15)
    ax.invert_yaxis()
    
    ax.set_title("Distribuição de Alunos por Ano de Escolarização", fontsize=15, fontweight='bold')
    
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    for container in ax.containers:
        for bar in container:
            val = bar.get_width()
            if val <= 0:
                continue
            if val <= 5:
                # Valor pequeno: fora da barra, em preto
                ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
                        f'{val:.0f}', va='center', ha='left',
                        fontsize=14, fontweight='bold', color='black')
            else:
                # Valor normal: dentro da barra, em branco
                ax.text(val / 2, bar.get_y() + bar.get_height() / 2,
                        f'{val:.0f}', va='center', ha='center',
                        fontsize=14, fontweight='bold', color='white')
    
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    return output_filename

def draw_kpi_box(c, x, y, width_box, height_box, title, value, color_hex, is_percent=False):
    # Título do KPI (acima)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_CABECALHO, 10)
    c.drawCentredString(x + width_box/2, y + height_box - 0.4*cm, title)
    
    # Valor numérico em destaque (abaixo)
    if color_hex == 'black':
        c.setFillColorRGB(0, 0, 0)
    else:
        c.setFillColor(colors.HexColor(color_hex))
        
    c.setFont(FONT_NUMERO, 20)
    val_str = f"{value}%" if is_percent else str(value)
    c.drawCentredString(x + width_box/2, y + height_box/2 - 0.4*cm, val_str)

def render(c, width, height, df_mat, df_distorcao_escola=None):
    """Renderiza a página de Formação de Classe usando dados reais de MATRICULAS."""
    draw_header(c, width, height)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "Formação de Classe")
    c.setFillColorRGB(0, 0, 0)
    
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = FONT_TEXTO
    style_n.fontSize = 11
    style_n.leading = 14
    style_n.alignment = 4
    
    # Calcular totais a partir dos dados reais
    total_matriculados = int(df_mat['QTD_MATRICULADOS'].sum())
    total_rede = int(df_mat['QTD_ALUNOS_REDE'].sum())
    total_novos = int(df_mat['QTD_ALUNOS_NOVOS'].sum())
    total_pcd = int(df_mat['QTD_DEFICIENTES'].sum())
    
    # Extrair distorções reais do ano mais recente
    dist_iniciais = "-"
    dist_finais = "-"
    cor_iniciais = "black"
    cor_finais = "black"
    dist_ano = ""
    
    # if df_distorcao_escola is not None and not df_distorcao_escola.empty:
    #     max_y = df_distorcao_escola['TXDIS_ANO'].max()
    #     dist_ano = f"Em {max_y}, a"
        
    #     # Filtro Anos Iniciais
    #     df_ini = df_distorcao_escola[(df_distorcao_escola['TXDIS_ETAPA'] == 'Anos Iniciais') & (df_distorcao_escola['TXDIS_ANO'] == max_y)]
    #     if not df_ini.empty:
    #         v_ini = df_ini['AVG_TXDIS_DISTORCAO'].mean()
    #         dist_iniciais = f"{v_ini:.0f}"
    #         cor_iniciais = _get_color_for_distorcao(v_ini)
            
    #     # Filtro Anos Finais
    #     df_fin = df_distorcao_escola[(df_distorcao_escola['TXDIS_ETAPA'] == 'Anos Finais') & (df_distorcao_escola['TXDIS_ANO'] == max_y)]
    #     if not df_fin.empty:
    #         v_fin = df_fin['AVG_TXDIS_DISTORCAO'].mean()
    #         dist_finais = f"{v_fin:.0f}"
    #         cor_finais = _get_color_for_distorcao(v_fin)
    # else:
    #     dist_ano = "A"
    
    texto_intro = f"""
    No momento, em 2026, estão
    matriculados <b><font color="#f8981d">{total_matriculados}</font></b> estudantes, dos quais <b>{total_rede}</b> já faziam parte da rede em anos anteriores, enquanto <b>{total_novos}</b> ingressaram neste ano letivo, reforçando o fluxo de
    renovação escolar. Além disso, a instituição atende <b><font color="#4477aa">{total_pcd}</font></b> estudantes com deficiência (PCD), evidenciando sua atuação inclusiva e o compromisso com a diversidade
    educacional.
    """
    p = Paragraph(texto_intro, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    p.drawOn(c, 2*cm, height - 5.1*cm - p_h)
    
    # KPIs Bloco 1 (4 horizontais)
    y_kpi1 = height - 10.5*cm
    box_w = 3.5*cm
    box_h = 2*cm
    space = (width - 4*cm - 4*box_w) / 3
    
    draw_kpi_box(c, 2*cm, y_kpi1, box_w, box_h, "Matriculados", total_matriculados, '#f8981d')
    draw_kpi_box(c, 2*cm + box_w + space, y_kpi1, box_w, box_h, "Alunos da Rede", total_rede, 'black')
    draw_kpi_box(c, 2*cm + 2*(box_w + space), y_kpi1, box_w, box_h, "Alunos Novos", total_novos, 'black')
    draw_kpi_box(c, 2*cm + 3*(box_w + space), y_kpi1, box_w, box_h, "Alunos PCD", total_pcd, '#4477aa')
    

    
    # Gráfico
    chart_y = height - 25.0*cm
    chart_img = create_distribution_chart(df_mat, "tmp_dist_chart.png")
    
    if chart_img:
        c.drawImage(chart_img, 1*cm, chart_y, width=width-2*cm, height=12*cm, preserveAspectRatio=True)
        os.remove(chart_img)
        
    draw_footer(c, width, height)
    c.showPage()
