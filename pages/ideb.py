import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pdf_engine import draw_header, draw_footer
from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO

# ─── Mock Data para Fluxo por Ano (mantido enquanto não há dados reais) ──────

MOCK_FLUXO_POR_ANO = {
    "Anos Iniciais": {
        "1º Ano": 0.99,
        "2º Ano": 0.98,
        "3º Ano": 0.97,
        "4º Ano": 0.96,
        "5º Ano": 0.95,
    },
    "Anos Finais": {
        "6º Ano": 1.00,
        "7º Ano": 1.00,
        "8º Ano": 0.993,
        "9º Ano": 0.991,
    },
}

# ─── Cores ───────────────────────────────────────────────────────────────────

COR_IDEB = "#095fc8"
COR_NOTA_PADRONIZADA = "#24736a"
COR_APROVACAO = "#63a6f8"
COR_MATEMATICA = "#168bde"
COR_LINGUA_PORTUGUESA = "#32a852"
COR_TITULO = "#056cad"

# ─── Helpers: KPI ────────────────────────────────────────────────────────────

def _draw_kpi(c, x, y, w, h, title, value, color_hex):
    """Desenha um KPI com título acima e valor abaixo."""
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_CABECALHO, 10)
    c.drawCentredString(x + w / 2, y + h - 0.4 * cm, title)

    c.setFillColor(colors.HexColor(color_hex))
    c.setFont(FONT_NUMERO, 20)
    c.drawCentredString(x + w / 2, y + h / 2 - 0.6 * cm, str(value))


def _draw_kpi_equation(c, x_start, y, kpis, width_available):
    """Desenha 3 KPIs com operadores visuais: KPI1 = KPI2 × KPI3."""
    kpi_w = 4.2 * cm
    kpi_h = 2.5 * cm

    # Centralizar o bloco de 3 KPIs + operadores
    operator_w = 1.2 * cm
    total_w = 3 * kpi_w + 2 * operator_w
    x = x_start + (width_available - total_w) / 2

    # KPI 1
    _draw_kpi(c, x, y, kpi_w, kpi_h, kpis[0]["title"], kpis[0]["value"], kpis[0]["color"])

    # Operador "="
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_NUMERO, 18)
    c.drawCentredString(x + kpi_w + operator_w / 2, y + kpi_h / 2 - 0.1 * cm, "x")

    # KPI 2
    x2 = x + kpi_w + operator_w
    _draw_kpi(c, x2, y, kpi_w, kpi_h, kpis[1]["title"], kpis[1]["value"], kpis[1]["color"])

    # Operador "×"
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont(FONT_NUMERO, 18)
    c.drawCentredString(x2 + kpi_w + operator_w / 2, y + kpi_h / 2 - 0.1 * cm, "=")

    # KPI 3
    x3 = x2 + kpi_w + operator_w
    _draw_kpi(c, x3, y, kpi_w, kpi_h, kpis[2]["title"], kpis[2]["value"], kpis[2]["color"])


# ─── Helpers: Charts ─────────────────────────────────────────────────────────

def _create_line_chart(anos, valores, color, title, output_filename, ylabel=""):
    """Gera um gráfico de linha simples e salva como imagem."""
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(anos, valores, marker="o", color=color, linewidth=2.5, markersize=7)

    # Tom mais escuro para rótulos dos valores
    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(color)
    label_color = (r * 0.35, g * 0.35, b * 0.35)

    for i, (a, v) in enumerate(zip(anos, valores)):
        ax.annotate(
            f"{v:.2f}" if isinstance(v, float) and v < 1 else f"{v:.1f}" if isinstance(v, float) else f"{v}",
            (a, v),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=label_color,
        )

    ax.set_title(title, fontsize=11, fontweight="bold", pad=22)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)

    ax.set_xticks(anos)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    return output_filename


def _create_bar_chart(labels, valores, color, title, output_filename):
    """Gera um gráfico de barras verticais e salva como imagem."""
    import numpy as np
    valores_limpos = [v for v in valores if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not valores_limpos:
        return None
        
    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.bar(labels, valores, color=color, width=0.5)

    # Tom mais escuro para rótulos
    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(color)
    label_color = (r * 0.35, g * 0.35, b * 0.35)

    for bar, v in zip(bars, valores):
        pct = f"{v * 100:.1f}%" if v <= 1 else f"{v:.1f}%"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.005,
            pct,
            va="bottom",
            ha="center",
            fontsize=11,
            fontweight="bold",
            color=label_color,
        )

    ax.set_title(title, fontsize=11, fontweight="bold", pad=22)
    ax.set_ylim(0, max(valores_limpos) * 1.15)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.yaxis.set_ticks([])
    ax.tick_params(axis='x', labelsize=11)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    return output_filename


# ─── Extração de dados do DataFrame ──────────────────────────────────────────

def _extract_etapa_data(df_ideb, etapa, df_taxa=None):
    """Extrai os dados de uma etapa do DataFrame IDEB e retorna um dict."""
    df_etapa = df_ideb[df_ideb['IDEB_ETAPA'] == etapa].sort_values('IDEB_ANO')

    if df_etapa.empty:
        return None

    # Remover linhas onde IDEB é NaN
    df_etapa = df_etapa.dropna(subset=['IDEB'])
    if df_etapa.empty:
        return None

    fluxo_por_ano = {}
    if df_taxa is not None and not df_taxa.empty:
        # Filtrar por etapa e tipo APV (Aprovação)
        df_filtered = df_taxa[(df_taxa['TXREN_ETAPA'] == etapa) & (df_taxa['TXREN_TIPO'] == 'APV')]
        if not df_filtered.empty:
            anos_ideb = df_etapa['IDEB_ANO'].dropna().tolist()
            max_ano_ideb = max(anos_ideb) if anos_ideb else df_filtered['TXREN_ANO'].max()
            
            df_ano = df_filtered[df_filtered['TXREN_ANO'] == max_ano_ideb]
            if df_ano.empty:
                max_ano_taxa = df_filtered['TXREN_ANO'].max()
                df_ano = df_filtered[df_filtered['TXREN_ANO'] == max_ano_taxa]
                
            if not df_ano.empty:
                # Agrupar por ano de escolarização para suportar agregações (Médias)
                df_agg = df_ano.groupby('TXREN_ANO_ESCOLARIZACAO')['TXREN_PORCENTAGEM'].mean().reset_index()
                for _, row in df_agg.iterrows():
                    ano_esc = row['TXREN_ANO_ESCOLARIZACAO']
                    if ano_esc != 'Total':
                        fluxo_por_ano[ano_esc] = row['TXREN_PORCENTAGEM'] / 100.0 if row['TXREN_PORCENTAGEM'] > 1.2 else row['TXREN_PORCENTAGEM']

    data = {
        "anos": df_etapa['IDEB_ANO'].tolist(),
        "ideb": df_etapa['IDEB'].tolist(),
        "nota_padronizada": df_etapa['NOTA_P'].tolist(),
        "aprovacao": df_etapa['FLUXO'].tolist(),
        "matematica": df_etapa['MATEMATICA'].tolist() if 'MATEMATICA' in df_etapa.columns else [],
        "lingua_portuguesa": df_etapa['PORTUGUES'].tolist() if 'PORTUGUES' in df_etapa.columns else [],
        "fluxo_por_ano": fluxo_por_ano,
    }

    return data


# ─── Página 1: IDEB (visão geral) ───────────────────────────────────────────

def _render_page_ideb(c, width, height, etapa, data):
    draw_header(c, width, height)

    styles = getSampleStyleSheet()
    style_n = ParagraphStyle(
        "IdebIntro",
        parent=styles["Normal"],
        fontName=FONT_TEXTO,
        fontSize=11,
        leading=14,
        alignment=4,
    )

    # Título principal
    c.setFillColor(colors.HexColor(COR_TITULO))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5 * cm, "IDEB")
    c.setFillColorRGB(0, 0, 0)

    # Parágrafo descritivo
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
    p.drawOn(c, 2 * cm, height - 5.1 * cm - p_h)

    # Subtítulo com etapa
    sub_y = height - 5.5 * cm - p_h - 0.8 * cm
    c.setFillColor(colors.HexColor(COR_TITULO))
    c.setFont(FONT_CABECALHO, 14)
    c.drawCentredString(width / 2.0, sub_y, f"IDEB - {etapa}")

    # Resultados [Ano]
    ano_max = max(data["anos"])
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont(FONT_TEXTO, 11)
    c.drawCentredString(width / 2.0, sub_y - 0.6 * cm, f"Resultados {ano_max}")
    c.setFillColorRGB(0, 0, 0)

    # KPIs em equação (valores do ano mais recente)
    ultimo_ideb = data["ideb"][-1]
    ultimo_np = data["nota_padronizada"][-1]
    ultimo_ap = data["aprovacao"][-1]

    kpis = [
        {"title": "Nota Padronizada", "value": f"{ultimo_np:.2f}", "color": COR_NOTA_PADRONIZADA},
        {"title": "Aprovação (Fluxo)", "value": f"{ultimo_ap:.2f}", "color": COR_APROVACAO},
        {"title": "IDEB", "value": f"{ultimo_ideb:.1f}", "color": COR_IDEB},
    ]

    kpi_y = sub_y - 4 * cm
    _draw_kpi_equation(c, 2 * cm, kpi_y, kpis, width - 4 * cm)

    # Gráfico de linha — Série Histórica IDEB
    chart_filename = f"tmp_ideb_hist_{etapa.replace(' ', '_')}.png"
    _create_line_chart(
        data["anos"],
        data["ideb"],
        COR_IDEB,
        f"Série Histórica do IDEB - {etapa}",
        chart_filename,
    )
    chart_y = kpi_y - 8.5 * cm
    c.drawImage(chart_filename, 2.5 * cm, chart_y, width=width - 5 * cm, height=7.5 * cm, preserveAspectRatio=True)
    os.remove(chart_filename)

    #draw_footer(c, width, height, qr_code_name="IDEB")
    draw_footer(c, width, height)
    c.showPage()


# ─── Página 2: IDEB Nota Padronizada ────────────────────────────────────────

def _render_page_nota_padronizada(c, width, height, etapa, data):
    draw_header(c, width, height)

    # Título
    c.setFillColor(colors.HexColor(COR_TITULO))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5 * cm, f"IDEB - {etapa}: Proficiência")

    # Resultados [Ano]
    ano_max = max(data["anos"])
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont(FONT_TEXTO, 11)
    c.drawCentredString(width / 2.0, height - 5.2 * cm, f"Resultados {ano_max}")
    c.setFillColorRGB(0, 0, 0)

    # 3 KPIs lado a lado
    kpi_w = 4.5 * cm
    kpi_h = 2.5 * cm
    total_kpi_w = 3 * kpi_w
    spacing = (width - 4 * cm - total_kpi_w) / 2
    y_kpi = height - 8.5 * cm

    ultimo_mat = data["matematica"][-1]
    ultimo_lp = data["lingua_portuguesa"][-1]
    ultimo_np = data["nota_padronizada"][-1]

    _draw_kpi(c, 2 * cm, y_kpi, kpi_w, kpi_h, "Língua Portuguesa", f"{ultimo_lp:.0f}", COR_LINGUA_PORTUGUESA)
    _draw_kpi(c, 2 * cm + kpi_w + spacing, y_kpi, kpi_w, kpi_h, "Matemática", f"{ultimo_mat:.0f}", COR_MATEMATICA)
    _draw_kpi(c, 2 * cm + 2 * (kpi_w + spacing), y_kpi, kpi_w, kpi_h, "Nota Padronizada", f"{ultimo_np:.2f}", COR_NOTA_PADRONIZADA)

    # Gráfico 1: Série Histórica Língua Portuguesa
    chart_lp = f"tmp_ideb_lp_{etapa.replace(' ', '_')}.png"
    _create_line_chart(
        data["anos"],
        data["lingua_portuguesa"],
        COR_LINGUA_PORTUGUESA,
        f"Série Histórica - Língua Portuguesa ({etapa})",
        chart_lp,
    )
    chart_h = 6.5 * cm
    y_chart1 = height - 9 * cm - chart_h
    c.drawImage(chart_lp, 2.5 * cm, y_chart1, width=width - 5 * cm, height=chart_h, preserveAspectRatio=True)
    os.remove(chart_lp)

    # Gráfico 2: Série Histórica Matemática
    chart_mat = f"tmp_ideb_mat_{etapa.replace(' ', '_')}.png"
    _create_line_chart(
        data["anos"],
        data["matematica"],
        COR_MATEMATICA,
        f"Série Histórica - Matemática ({etapa})",
        chart_mat,
    )
    y_chart2 = y_chart1 - chart_h - 1 * cm
    c.drawImage(chart_mat, 2.5 * cm, y_chart2, width=width - 5 * cm, height=chart_h, preserveAspectRatio=True)
    os.remove(chart_mat)

    #draw_footer(c, width, height, qr_code_name="IDEB")
    draw_footer(c, width, height)
    c.showPage()


# ─── Página 3: IDEB Fluxo Aprovação ─────────────────────────────────────────

def _render_page_fluxo(c, width, height, etapa, data):
    draw_header(c, width, height)

    # Título
    c.setFillColor(colors.HexColor(COR_TITULO))
    c.setFont(FONT_TITULO, 17)
    c.drawCentredString(width / 2.0, height - 4.5 * cm, f"IDEB - {etapa}: Aprovação (Fluxo)")

    # Resultados [Ano]
    ano_max = max(data["anos"])
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont(FONT_TEXTO, 11)
    c.drawCentredString(width / 2.0, height - 5.2 * cm, f"Resultados {ano_max}")
    c.setFillColorRGB(0, 0, 0)

    # KPI
    kpi_w = 5 * cm
    kpi_h = 2.5 * cm
    x_kpi = (width - kpi_w) / 2
    y_kpi = height - 8.5 * cm
    ultimo_ap = data["aprovacao"][-1]
    _draw_kpi(c, x_kpi, y_kpi, kpi_w, kpi_h, "Fluxo (Aprovação)", f"{ultimo_ap:.2f}", COR_APROVACAO)

    # Gráfico de linha: Série Histórica do Fluxo
    chart_fluxo = f"tmp_ideb_fluxo_{etapa.replace(' ', '_')}.png"
    _create_line_chart(
        data["anos"],
        data["aprovacao"],
        COR_APROVACAO,
        f"Série Histórica - Fluxo ({etapa})",
        chart_fluxo,
    )
    chart_h = 6.5 * cm
    y_chart1 = height - 9 * cm - chart_h
    c.drawImage(chart_fluxo, 2.5 * cm, y_chart1, width=width - 5 * cm, height=chart_h, preserveAspectRatio=True)
    os.remove(chart_fluxo)

    # Gráfico de barras: Fluxo por ano de escolaridade (mock data)
    fluxo_por_ano = data["fluxo_por_ano"]
    if fluxo_por_ano:
        chart_bar = f"tmp_ideb_fluxo_bar_{etapa.replace(' ', '_')}.png"
        res_bar = _create_bar_chart(
            list(fluxo_por_ano.keys()),
            list(fluxo_por_ano.values()),
            COR_APROVACAO,
            f"Fluxo por Ano de Escolaridade ({etapa}) - {ano_max}",
            chart_bar,
        )
        if res_bar:
            chart_h2 = 6 * cm
            y_chart2 = y_chart1 - chart_h2 - 1 * cm
            c.drawImage(chart_bar, 2.5 * cm, y_chart2, width=width - 5 * cm, height=chart_h2, preserveAspectRatio=True)
            os.remove(chart_bar)

    #draw_footer(c, width, height, qr_code_name="IDEB")
    draw_footer(c, width, height)
    c.showPage()


# ─── Render principal ────────────────────────────────────────────────────────

def render(c, width, height, df_ideb, df_taxa=None):
    """Renderiza as páginas do IDEB para cada etapa que possuir dados."""
    if df_ideb.empty:
        return

    for etapa in ["Anos Iniciais", "Anos Finais"]:
        data = _extract_etapa_data(df_ideb, etapa, df_taxa)
        if data is None:
            continue

        # Verificar se existe IDEB para essa etapa (valor do ano mais recente)
        ultimo_ideb = data["ideb"][-1] if data["ideb"] else 0
        if ultimo_ideb == 0:
            continue

        _render_page_ideb(c, width, height, etapa, data)
        _render_page_nota_padronizada(c, width, height, etapa, data)
        _render_page_fluxo(c, width, height, etapa, data)
