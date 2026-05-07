import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Configuração de estilo dos padrões de desempenho
# Estes são exemplos de padrões de desempenho, se houver outros reais precisam ser mapeados.
PADRAO_COLORS = {
    '4.Abaixo do Básico': '#e0493e',
    '3.Básico': '#f7b639',
    '2.Adequado': '#3f99de',
    '1.Avançado': '#6aab5b'
}

def clean_data(df_boletim, df_escolas):
    # Fazer merge para obter a regional de cada escola
    df = pd.merge(df_boletim, df_escolas, on='TRI_NM_ESCOLA', how='inner')
    
    # Preencher NaN
    df['PERCENTUAL_PADRAO'] = df['PERCENTUAL_PADRAO'].fillna(0)
    
    # As avaliações esperadas no texto eram '2024-AV3', '2025-AV3', mas o gráfico usa "2024" e "2025" nos títulos
    # Vamos extrair o ano
    df['ANO'] = df['TRI_ANO_AVALIACAO'].str[:4]
    
    return df

def draw_header(c, width, height, is_first_page=False):
    if is_first_page:
        return
        
    # Desenhar logo esquerda (nossa_escola.png)
    logo_esq_path = "assets/nossa_escola.png"
    if os.path.exists(logo_esq_path):
        # Substitui a marcação colorida pela imagem (Aumentando de 4x2 para 5.5x2.5)
        c.drawImage(logo_esq_path, 1*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, preserveAspectRatio=True, mask='auto', anchor='c')
    else:
        # Fallback (placeholders originais)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(1*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica", 10)
        c.drawCentredString(3.75*cm, height - 2.25*cm, "LOGO ESQ")
    
    # Desenhar logo direita (logo_smed.jpeg)
    logo_dir_path = "assets/logo_smed.jpeg"
    if os.path.exists(logo_dir_path):
        c.drawImage(logo_dir_path, width - 6.5*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, preserveAspectRatio=True, mask='auto', anchor='c')
    else:
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(width - 6.5*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(width - 3.75*cm, height - 2.25*cm, "LOGO DIR")

def draw_footer(c, width, height):
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(1*cm, 1*cm, "Fonte: Nossa Escola em Dados")

def create_stacked_bar_chart(df, disciplina, ano, output_filename):
    # Filtra os dados
    df_filter = df[(df['TRI_NM_DISCIPLINA'] == disciplina) & (df['ANO'] == ano)]
    
    # Se não houver dados, retorna None
    if df_filter.empty:
        return None
        
    # Pivotar os dados para plotagem: linhas=ANO_ESCOLARIDADE, colunas=PADRAO_DESEMPENHO
    pivot_df = df_filter.pivot_table(
        index='TRI_ANO_ESCOLARIDADE',
        columns='TRI_PADRAO_DESEMPENHO',
        values='PERCENTUAL_PADRAO',
        aggfunc='sum'
    ).fillna(0)
    
    # Inverter a ordem do eixo Y (Anos de Escolaridade)
    pivot_df = pivot_df.iloc[::-1]
    
    # Tentar aplicar as cores personalizadas, para colunas que não estiverem no dicionário, usa cor neutra
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
    
    # Aumentar tamanho do gráfico e barras (figsize mais largo e alto para dar espaço a barras grossas)
    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    # 'width' controla a espessura da barra horizontal - valores perto de 1 aumentam a espessura
    pivot_df.plot(kind='barh', stacked=True, color=colors_list, ax=ax, width=0.8)
    
    ax.set_title(f"{ano} - Av. de Saída", fontsize=11, fontweight='bold')
    ax.set_ylabel('') # Removendo titulo do eixo Y
    
    # Remover rótulos do eixo X e ticks
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Adicionar porcentagem nas barras (aumentando a fonte de 9 para 10)
    for c in ax.containers:
        # Custom label for each bar (ignorar valores menores que 1%)
        labels = [f'{v.get_width():.0f}%' if v.get_width() >= 1 else '' for v in c]
        ax.bar_label(c, labels=labels, label_type='center', fontsize=10, color='white', weight='bold')
    
    # Aumentar fonte do eixo Y de 10 para 11
    ax.tick_params(axis='y', which='major', labelsize=11)
    
    # Ocultar a legenda individual
    ax.get_legend().remove()
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    return output_filename

def generate_school_report(escola, regional, df_escola, output_dir):
    filename = os.path.join(output_dir, f"{escola}.pdf".replace(" ", "_").replace("/", "_"))
    
    # Configurar Canvas do ReportLab
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # --- PÁGINA 1: CAPA ---
    draw_header(c, width, height, is_first_page=True)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height / 2.0 + 2*cm, "INDICADORES DA NOSSA ESCOLA - 2025")
    
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2.0, height / 2.0 - 1*cm, escola)
    
    c.setFillColorRGB(0, 0, 0)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2.0, height / 2.0 - 3*cm, f"Gerado em: {now_str}")
    
    c.showPage()
    
    # --- PÁGINA 2: INDICADOR PROSA ---
    draw_header(c, width, height)
    
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height - 4.5*cm, "Prosa")
    c.setFillColorRGB(0, 0, 0)
    
    # Parágrafo
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_n.fontName = 'Helvetica'
    style_n.fontSize = 11
    style_n.leading = 14
    style_n.alignment = 4 # JUSTIFY = 4, LEFT = 0
    
    texto_prosa = (
        "<b>PROSA</b> (Programa Salvador Avalia): tem o objetivo de realizar um diagnóstico do aprendizado dos alunos da rede "
        "municipal de ensino e fornecer subsídios para o aprimoramento da qualidade do ensino. A avaliação abrange as disciplinas "
        "de Língua Portuguesa e Matemática, e o resultado é utilizado para identificar pontos de melhoria no processo de ensino-aprendizagem."
    )
    p = Paragraph(texto_prosa, style_n)
    p_w, p_h = p.wrap(width - 4*cm, height)
    p.drawOn(c, 2*cm, height - 5.1*cm - p_h)
    
    # Placeholder da legenda global -> Substituindo pela imagem e descendo a posição original de -7.5 para -9.0
    legenda_path = "assets/legenda.jpg"
    if os.path.exists(legenda_path):
        c.drawImage(legenda_path, width/2 - 4*cm, height - 9.0*cm, 8*cm, 1*cm, preserveAspectRatio=True, anchor='s')
    else:
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(width/2 - 4*cm, height - 9.0*cm, 8*cm, 1*cm, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height - 8.6*cm, "[ LEGENDA PLACEHOLDER ]")
    
    # --- Gráficos ---
    # Coordenadas (largura, altura do bloco) agora um pouco maiores
    chart_w = 8.0 * cm
    chart_h = 6.0 * cm
    
    # Layout Grid: Língua Portuguesa (topo), Matemática (abaixo)
    # Descendo todos os Ys
    # Matemática
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2.0, height - 10.0*cm, "Matemática")
    
    # Gerar imagens dos gráficos (salvos temporariamente)
    img_mat_24 = create_stacked_bar_chart(df_escola, 'Matemática', '2024', "tmp_mat_2024.png")
    img_mat_25 = create_stacked_bar_chart(df_escola, 'Matemática', '2025', "tmp_mat_2025.png")
    
    # Desenhar imagens
    y_mat = height - 16.5*cm
    if img_mat_24:
        c.drawImage(img_mat_24, 2*cm, y_mat, width=chart_w, height=chart_h)
    if img_mat_25:
        c.drawImage(img_mat_25, 2*cm + chart_w + 1*cm, y_mat, width=chart_w, height=chart_h)
        
    # Língua Portuguesa
    c.setFillColor(colors.HexColor('#056cad'))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2.0, height - 17.5*cm, "Língua Portuguesa")
    
    img_lp_24 = create_stacked_bar_chart(df_escola, 'Língua Portuguesa', '2024', "tmp_lp_2024.png")
    img_lp_25 = create_stacked_bar_chart(df_escola, 'Língua Portuguesa', '2025', "tmp_lp_2025.png")
    
    y_lp = height - 24.0*cm
    if img_lp_24:
        c.drawImage(img_lp_24, 2*cm, y_lp, width=chart_w, height=chart_h)
    if img_lp_25:
        c.drawImage(img_lp_25, 2*cm + chart_w + 1*cm, y_lp, width=chart_w, height=chart_h)

    # Limpar imagens temporárias
    for img in [img_mat_24, img_mat_25, img_lp_24, img_lp_25]:
        if img and os.path.exists(img):
            os.remove(img)
            
    draw_footer(c, width, height)
    c.showPage()
    
    c.save()

def main():
    print("Iniciando geração de relatórios...")
    
    # Cria pasta de saída
    output_dir = 'relatorios'
    os.makedirs(output_dir, exist_ok=True)
    
    # Carregar dados
    df_boletim = pd.read_parquet('data/prosa_boletim.parquet')
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    
    # Limpar e juntar dados
    df = clean_data(df_boletim, df_escolas)
    
    escolas = df['TRI_NM_ESCOLA'].unique()
    count=0
    for escola in escolas:
        df_escola = df[df['TRI_NM_ESCOLA'] == escola]
        regional = df_escola['TRI_NM_REGIONAL'].iloc[0]
        
        # Cria pasta pra regional
        regional_dir = os.path.join(output_dir, str(regional))
        os.makedirs(regional_dir, exist_ok=True)
        
        print(f"Gerando relatório: {escola} - Regional {regional}")
        generate_school_report(escola, regional, df_escola, regional_dir)
        count+=1
        if count==30:
            break
    print("Processo concluído.")

if __name__ == "__main__":
    main()
