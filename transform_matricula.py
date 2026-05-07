import pandas as pd

def main():
    file_name = './data/MATRICULAS_2026.xlsx'
    df = pd.read_excel(file_name)
    for col in df.columns:
        if col.startswith('QTD'):
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    if 'ESCOLA' in df.columns:
        # Garantir que a coluna seja string
        df['ESCOLA'] = df['ESCOLA'].astype(str)
        
        # Remover os 7 primeiros caracteres
        df['ESCOLA'] = df['ESCOLA'].str[7:]
        
        # Mapeamento de substituições (Dicionário de De -> Para)
        # Nota: A ordem importa se houver termos contidos em outros
        substituicoes = {
            r'\bCMEI\b': 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL',
            r'\bEM\b': 'ESCOLA MUNICIPAL',
            r'\bDEPT\b\.': 'DEPUTADO',
            r'\bPROF\b\.': 'PROFESSOR',
            r'\bPROFª\b\.': 'PROFESSORA',
            r'\bENGENHEIRO\b': 'ENG',
            r'\bVARELA\b': 'VARELLA'
        }
        
        # Aplicar as substituições
        for velho, novo in substituicoes.items():
            # Usamos regex=True para garantir que a palavra esteja isolada (\b)
            df['ESCOLA'] = df['ESCOLA'].str.replace(velho, novo, regex=True)
    
    df.to_excel('./data/MATRICULAS.xlsx', index=False)
    print("Alterações concluídas com sucesso!")    
if __name__ == '__main__':
    main()