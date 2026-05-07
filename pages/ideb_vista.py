import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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

COR_IDEB = "#095fc8"
COR_NOTA_PADRONIZADA = "#24736a"
COR_APROVACAO = "#63a6f8"
COR_TITULO = "#056cad"

def _draw_kpi(c, x, y, w, h, title, value, color_hex):
    """Desenha um KPI com título acima e valor abaixo."""
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_CABECALHO, 9)
    c.drawCentredString(x + w / 2, y + h - 0.3 * cm, title)

    c.setFillColor(colors.HexColor(color_hex))
    c.setFont(FONT_NUMERO, 17)
    c.drawCentredString(x + w / 2, y + h / 2 - 0.4 * cm, str(value))

def _draw_kpi_equation(c, x_start, y, kpis, width_available):
    """Desenha 3 KPIs com operadores visuais: KPI1 = KPI2 × KPI3."""
    kpi_w = 3.8 * cm
    kpi_h = 2.0 * cm
    operator_w = 1.0 * cm
    total_w = 3 * kpi_w + 2 * operator_w
    x = x_start + (width_available - total_w) / 2

    # KPI 1 (Nota Padronizada)
    _draw_kpi(c, x, y, kpi_w, kpi_h, kpis[0]["title"], kpis[0]["value"], kpis[0]["color"])

    # Operador "X"
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_NUMERO, 16)
    c.drawCentredString(x + kpi_w + operator_w / 2, y + kpi_h / 2 - 0.1 * cm, "x")

    # KPI 2 (Aprovação)
    x2 = x + kpi_w + operator_w
    _draw_kpi(c, x2, y, kpi_w, kpi_h, kpis[1]["title"], kpis[1]["value"], kpis[1]["color"])

    # Operador "="
    c.drawCentredString(x2 + kpi_w + operator_w / 2, y + kpi_h / 2 - 0.1 * cm, "=")

    # KPI 3 (IDEB)
    x3 = x2 + kpi_w + operator_w
    _draw_kpi(c, x3, y, kpi_w, kpi_h, kpis[2]["title"], kpis[2]["value"], kpis[2]["color"])

def _create_line_chart(anos, valores, color, title, output_filename, height_chart=3.0):
    """Gera um gráfico de linha simples e salva como imagem."""
    fig, ax = plt.subplots(figsize=(6, height_chart))
    ax.plot(anos, valores, marker="o", color=color, linewidth=2.0, markersize=6)

    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(color)
    label_color = (r * 0.35, g * 0.35, b * 0.35)

    for i, (a, v) in enumerate(zip(anos, valores)):
        ax.annotate(
            f"{v:.1f}" if isinstance(v, (int, float)) and v >= 1 else f"{v:.2f}",
            (a, v),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=label_color,
        )

    ax.set_title(title, fontsize=10, fontweight="bold", pad=15)
    ax.set_xticks(anos)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_color('#cccccc')
    ax.spines["left"].set_color('#cccccc')
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return output_filename

def _extract_etapa_data(df_ideb, etapa):
    """Extrai os dados de uma etapa do DataFrame IDEB."""
    df_etapa = df_ideb[df_ideb['IDEB_ETAPA'] == etapa].sort_values('IDEB_ANO')
    if df_etapa.empty:
        return None
        
    df_etapa = df_etapa.dropna(subset=['IDEB'])
    if df_etapa.empty:
        return None

    return {
        "anos": df_etapa['IDEB_ANO'].tolist(),
        "ideb": df_etapa['IDEB'].tolist(),
        "nota_padronizada": df_etapa['NOTA_P'].tolist(),
        "aprovacao": df_etapa['FLUXO'].tolist(),
    }

def render(c, width, height, df_ideb):
    if df_ideb is None or df_ideb.empty:
        return

    draw_header(c, width, height)

    # Título principal
    c.setFillColor(colors.HexColor(COR_TITULO))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5 * cm, "IDEB")
    c.setFillColorRGB(0, 0, 0)

    # Parágrafo descritivo (apenas uma vez)
    styles = getSampleStyleSheet()
    style_n = ParagraphStyle(
        "IdebIntro",
        parent=styles["Normal"],
        fontName=FONT_TEXTO,
        fontSize=11,
        leading=13,
        alignment=4,
    )

    texto = (
        "<b>IDEB</b> (Índice de Desenvolvimento da Educação Básica) é um indicador que avalia a qualidade da educação "
        "básica no Brasil, combinando a taxa de aprovação (fluxo) dos alunos com o desempenho nas avaliações de "
        "português e matemática do SAEB. Ele é realizado de forma bianual (de 2 em 2 anos) e é utilizado para "
        "monitorar a qualidade do ensino e estabelecer metas de melhoria para as escolas e redes de ensino. Para que "
        "uma escola tenha nota no IDEB, é necessário que ela tenha participado da avaliação do SAEB e que pelo menos "
        "80% dos alunos esperados da etapa avaliada tenham realizado a prova. Caso apenas uma das etapas atinja esse "
        "percentual, somente essa etapa terá a nota divulgada."
    )
    p = Paragraph(texto, style_n)
    p_w, p_h = p.wrap(width - 4 * cm, height)
    curr_y = height - 4.8 * cm - p_h  # Subiu de 5.0 para 4.8
    p.drawOn(c, 2 * cm, curr_y)

    etapas = ["Anos Iniciais", "Anos Finais"]
    etapas_existentes = []
    
    for etapa in etapas:
        data = _extract_etapa_data(df_ideb, etapa)
        if data and data["ideb"] and data["ideb"][-1] > 0:
            etapas_existentes.append((etapa, data))
            
    if not etapas_existentes:
        return

    is_dual = len(etapas_existentes) == 2
    chart_h_render = 4.8 * cm if is_dual else 7.0 * cm  # Reduzido de 5.5/7.5
    chart_h_fig = 2.2 if is_dual else 3.2              # Reduzido de 2.5/3.5

    curr_y -= 0.4 * cm  # Reduzido de 0.6

    for i, (etapa, data) in enumerate(etapas_existentes):
        # Subtítulo Etapa
        c.setFillColor(colors.HexColor('#1565C0'))
        c.setFont(FONT_CABECALHO, 12)  # Reduzido de 13
        c.drawString(2.5 * cm, curr_y, etapa)
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.setLineWidth(0.5)
        c.line(2.5 * cm, curr_y - 0.15 * cm, width - 2.5 * cm, curr_y - 0.15 * cm)

        curr_y -= 0.6 * cm  # Reduzido de 0.8

        # Resultados [Ano Mar]
        ano_max = max(data["anos"])
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont(FONT_TEXTO, 9)  # Reduzido de 10
        c.drawCentredString(width / 2.0, curr_y, f"Resultados {ano_max}")
        c.setFillColorRGB(0, 0, 0)

        curr_y -= 0.3 * cm  # Reduzido de 0.4

        # KPIs
        ultimo_ideb = data["ideb"][-1]
        ultimo_np = data["nota_padronizada"][-1]
        ultimo_ap = data["aprovacao"][-1]

        kpis = [
            {"title": "Nota Padronizada", "value": f"{ultimo_np:.2f}", "color": COR_NOTA_PADRONIZADA},
            {"title": "Aprovação (Fluxo)", "value": f"{ultimo_ap:.2f}", "color": COR_APROVACAO},
            {"title": "IDEB", "value": f"{ultimo_ideb:.1f}", "color": COR_IDEB},
        ]

        kpi_h = 2.0 * cm
        curr_y -= kpi_h
        _draw_kpi_equation(c, 2 * cm, curr_y, kpis, width - 4 * cm)

        curr_y -= 0.4 * cm

        # Gráfico
        chart_filename = f"tmp_ideb_vista_{etapa.replace(' ', '')}.png"
        _create_line_chart(
            data["anos"],
            data["ideb"],
            COR_IDEB,
            f"Série Histórica do IDEB - {etapa}",
            chart_filename,
            height_chart=chart_h_fig
        )

        w_img = width - 6 * cm
        x_img = (width - w_img) / 2

        c.drawImage(chart_filename, x_img, curr_y - chart_h_render, width=w_img, height=chart_h_render, preserveAspectRatio=True)
        os.remove(chart_filename)

        curr_y -= (chart_h_render + 0.8 * cm)

    draw_footer(c, width, height, qr_code_name="IDEB")
    c.showPage()
