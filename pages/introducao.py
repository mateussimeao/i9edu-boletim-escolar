import os
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pdf_engine import draw_header
from fonts import FONT_TITULO, FONT_CABECALHO, FONT_NUMERO, FONT_TEXTO

def render(c, width, height):
    # O cabeçalho deve estar presente nas demais páginas (mas sem rodapé nesta específica)
    draw_header(c, width, height)
    
    styles = getSampleStyleSheet()
    
    style_n = ParagraphStyle(
        'IntroStyle',
        parent=styles['Normal'],
        fontName=FONT_TEXTO,
        fontSize=11,
        leading=16,
        alignment=4, # Justified
        textColor=colors.HexColor('#000000')
    )
    
    style_bullet = ParagraphStyle(
        'BulletStyle',
        parent=style_n,
        leftIndent=20,
        spaceBefore=4,
        spaceAfter=4
    )
    
    # Caminhos para as imagens dentro da pasta assets
    gems_img = "assets/gems.jpeg"
    bar_chart_img = "assets/bar_chart.jpeg"
    dedo_img = "assets/dedo.jpeg"
    
    def get_img_tag(path, w, h, alt):
        if os.path.exists(path):
            # O ReportLab suporta a tag <img> com atributo valign para alinhamento vertical com o texto
            return f'<img src="{path}" width="{w}" height="{h}" valign="middle"/>'
        return f'<b>[{alt}]</b>'

    img_gems = get_img_tag(gems_img, 11, 11, "marker")
    img_chart = get_img_tag(bar_chart_img, 14, 14, "chart")
    img_dedo = get_img_tag(dedo_img, 18, 18, "dedo")

    # Estruturação dos parágrafos textuais
    text_blocks = [
        ("Prezado(a) Diretor(a),", style_n),
        ("Este documento reúne os principais resultados educacionais da sua unidade escolar, com base nas informações mais recentes da Rede. "
         "Aqui, você encontrará dados sobre matrícula, rendimento, distorção idade-série, IDEB, resultados de avaliações como PROSA e Fluência Leitora, "
         "entre outros indicadores essenciais para o acompanhamento da aprendizagem.", style_n),
        ("O objetivo deste material é oferecer uma visão geral da sua escola em relação a indicadores-chave, possibilitando:", style_n),
        (f"{img_gems} Analisar os resultados da escola frente à rede e à regional;", style_bullet),
        (f"{img_gems} Observar a evolução ao longo do tempo;", style_bullet),
        (f"{img_gems} Apoiar o planejamento pedagógico e a tomada de decisões baseadas em dados.", style_bullet),
        (f"{img_chart} Para uma análise mais aprofundada, com possibilidade de gerar relatórios customizados por etapa, turma ou estudante, "
         f"orientamos o acesso à plataforma Nossa Escola em Dados, disponível em: {img_dedo} "
         "<font color='#056cad'><u><a href='https://escolaemdados-educacao.salvador.ba.gov.br'>https://escolaemdados-educacao.salvador.ba.gov.br</a></u></font>", style_n),
        ("Ressaltamos que este material não substitui o acesso à plataforma, mas funciona como um panorama inicial para apoiar a leitura dos dados, "
         "estimular reflexões pedagógicas e fortalecer o trabalho de toda a equipe escolar.", style_n)
    ]
    
    # Margem inicial abaixo do header
    current_y = height - 5 * cm
    
    for text, style in text_blocks:
        p = Paragraph(text, style)
        p_w, p_h = p.wrap(width - 4*cm, height)
        current_y -= p_h
        p.drawOn(c, 2*cm, current_y)
        # Espaçamento entre parágrafos
        current_y -= 0.5 * cm
        
    c.showPage()
