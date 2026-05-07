"""
Módulo de registro de fontes customizadas para o relatório.

Fontes registradas:
  - 'Montserrat-Bold'   → Títulos do relatório
  - 'OpenSans-Bold'     → Cabeçalhos de seção / subtítulos
  - 'GoogleSans'        → Textos descritivos / observações
  - 'GoogleSans-Bold'   → Números (KPIs, valores em negrito)
"""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')

_FONT_MAP = {
    'Montserrat-Bold': 'Montserrat-SemiBold.ttf',
    'OpenSans-Bold': 'OpenSans-Medium.ttf',
    'GoogleSans': 'GoogleSans-Regular.ttf',
    'GoogleSans-Bold': 'GoogleSans-Bold.ttf',
    'GoogleSans-Medium': 'GoogleSans-Medium.ttf',
}

_registered = False

def register_fonts():
    """Registra todas as fontes customizadas (uma única vez)."""
    global _registered
    if _registered:
        return
    for font_name, filename in _FONT_MAP.items():
        font_path = os.path.join(_FONTS_DIR, filename)
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont(font_name, font_path))
    
    # Registrar famílias para que <b> e <i> funcionem em Paragraph
    pdfmetrics.registerFontFamily('GoogleSans',
        normal='GoogleSans',
        bold='GoogleSans-Bold',
        italic='GoogleSans',
        boldItalic='GoogleSans-Bold',
    )
    _registered = True

# Registrar automaticamente ao importar
register_fonts()

# Constantes de nomes de fontes para uso nos módulos
FONT_TITULO = 'Montserrat-Bold'
FONT_CABECALHO = 'OpenSans-Bold'
FONT_NUMERO = 'GoogleSans-Bold'
FONT_TEXTO = 'GoogleSans'
