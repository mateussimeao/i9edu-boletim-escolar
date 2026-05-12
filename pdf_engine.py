import os
from reportlab.lib.units import cm

def draw_header(c, width, height, is_first_page=False):
    if is_first_page:
        return
        
    # Desenhar logo esquerda (nossa_escola.png)
    logo_esq_path = "assets/nossa_escola.png"
    if os.path.exists(logo_esq_path):
        c.drawImage(logo_esq_path, 2*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, preserveAspectRatio=True, mask='auto', anchor='sw')
    else:
        # Fallback
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(2*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica", 10)
        c.drawCentredString(4.75*cm, height - 2.25*cm, "LOGO ESQ")
    
    # Desenhar logo direita (logo_smed.jpeg)
    logo_dir_path = "assets/logo_smed.jpeg"
    if os.path.exists(logo_dir_path):
        c.drawImage(logo_dir_path, width - 7.5*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, preserveAspectRatio=True, mask='auto', anchor='se')
    else:
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(width - 7.5*cm, height - 3.5*cm, 5.5*cm, 2.5*cm, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(width - 4.75*cm, height - 2.25*cm, "LOGO DIR")
        
    # Nome da Escola (Centralizado no Topo)
    escola = getattr(c, 'escola_nome', None)
    if escola:
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        import reportlab.lib.colors as reports_colors
        
        try:
            from fonts import FONT_NUMERO
            font_name = FONT_NUMERO
        except ImportError:
            font_name = "Helvetica-Bold"
            
        style = ParagraphStyle(
            name='HeaderEscola',
            fontName=font_name,
            fontSize=9,
            alignment=0, # Left
            leading=10,
            textColor=reports_colors.HexColor('#333333')
        )
        p = Paragraph(escola, style)
        avail_w = 5.5 * cm  # Mesma largura da logo esquerda
        p_w, p_h = p.wrap(avail_w, height)
        
        # Alinhado com a logo esquerda (X = 2*cm)
        text_x = 2 * cm
        
        # Desenhar abaixo da logo (Y da logo esquerda é height - 3.5*cm)
        p.drawOn(c, text_x, height - 3 * cm - p_h)

def draw_footer(c, width, height, qr_code_name=None):
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(1*cm, 1*cm, "Fonte: Nossa Escola em Dados")

    if getattr(c, 'no_qr', False):
        return

    if not qr_code_name:
        qr_code_name = getattr(c, 'qr_code_name', None)
        
    if qr_code_name:
        mapping = {
            'Prosa_Padrao_Desempenho': 'prosa',
            'Prosa': 'prosa',
            'Fluencia Leitora': 'fluencia_leitora',
            'Taxa_Distorcao': 'taxa_distorcao',
            'SABE_Proficiencia': 'SABE',
            'SABE': 'SABE',
            'Metas': 'metas'
        }
        name = mapping.get(qr_code_name, qr_code_name)
        qr_path = os.path.join("assets", "qr_codes", f"{name}.jpeg")
        
        if os.path.exists(qr_path):
            qr_size = 3.0 * cm
            c.drawImage(qr_path, width - qr_size - 1*cm, 0.5*cm, width=qr_size, height=qr_size, preserveAspectRatio=True)
