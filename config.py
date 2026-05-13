import os

# Diretórios de saída
OUTPUT_BOLETIM = r'G:\Shared drives\Indicadores do Painel Educação à Vista\BOLETIM DAS ESCOLAS'
OUTPUT_RELATORIO = r'G:\Shared drives\Indicadores do Painel Educação à Vista\RELATORIOS SMED'

# Arquivos de dados
DATA_DIR = 'data'
PROSA_BOLETIM     = os.path.join(DATA_DIR, 'prosa_boletim.parquet')
PROSA_ESCOLAS     = os.path.join(DATA_DIR, 'prosa_escolas.parquet')
PROSA_MEDIA       = os.path.join(DATA_DIR, 'prosa_media_alunos.parquet')
IDEB              = os.path.join(DATA_DIR, 'IDEB.xlsx')
IDEB_REDE         = os.path.join(DATA_DIR, 'IDEB_REDE.xlsx')
MATRICULAS        = os.path.join(DATA_DIR, 'MATRICULAS.xlsx')
TAXA_RENDIMENTO   = os.path.join(DATA_DIR, 'TAXA_RENDIMENTO.xlsx')
TAXA_DISTORCAO    = os.path.join(DATA_DIR, 'TAXA_DISTORCAO.xlsx')
SABE              = os.path.join(DATA_DIR, 'sabe.xlsx')
METAS             = os.path.join(DATA_DIR, 'METAS.xlsx')
FLUENCIA_2025     = os.path.join(DATA_DIR, 'leitura_diag_2025.xlsx')
FLUENCIA_2026     = os.path.join(DATA_DIR, 'leitura_diag_2026.xlsx')

# Padronização de nomes de escolas (aplicada em todos os DataFrames)
SCHOOL_RENAME = {
    'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
    'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA':   'ESCOLA MUNICIPAL JARDIM BRASILIA',
    'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA':              'ESCOLA MUNICIPAL ENG CARLOS BATALHA',
}

# Padronização de regionais — boletim usa "CIDADE BAIXA E LIBERDADE"
REGIONAL_RENAME_BOLETIM = {
    'CIDADE BAIXA': 'CIDADE BAIXA E LIBERDADE',
    'LIBERDADE':    'CIDADE BAIXA E LIBERDADE',
}

# Padronização de regionais — relatório usa "CIDADE BAIXA LIBERDADE"
REGIONAL_RENAME_RELATORIO = {
    'CIDADE BAIXA':           'CIDADE BAIXA LIBERDADE',
    'LIBERDADE':              'CIDADE BAIXA LIBERDADE',
    'CIDADE BAIXA E LIBERDADE': 'CIDADE BAIXA LIBERDADE',
}

# Modos executados quando --all é passado.
# Cada item é (nivel, formato). Altere a lista para habilitar/desabilitar combinações.
ALL_MODES = [
    ('rede',      'boletim'),
    ('rede',      'relatorio'),
    ('regional',  'boletim'),
    ('regional',  'relatorio'),
    ('escola',    'boletim'),
    ('escola',    'relatorio'),
]
