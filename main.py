import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pages import capa, introducao, formacao_classe, ideb, prosa, fluencia_leitora, taxa_rendimento, distorcao, prosa_proficiencia, sabe, sabe_proficiencia
import shutil

def clean_data(df_boletim, df_escolas):
    df = pd.merge(df_escolas, df_boletim, on='TRI_NM_ESCOLA', how='left')
    df['PERCENTUAL_PADRAO'] = df['PERCENTUAL_PADRAO'].fillna(0)
    df['ANO'] = df['TRI_ANO_AVALIACAO'].str[:4]
    return df

def generate_school_report(escola, regional, df_prosa, df_ideb_escola, df_mat_escola, df_fluencia_escola, df_taxa_escola, df_distorcao_escola, output_dir, df_prosa_media_escola=None, df_sabe_escola=None):
    escola_arq = escola.replace("ESCOLA MUNICIPAL", "EM").replace("CENTRO MUNICIPAL DE EDUCACAO INFANTIL", "CMEI")
    filename = os.path.join(output_dir, f"boletim_escolar_{regional}_{escola_arq}.pdf".replace(" ", "_").replace("/", "_"))
    
    # Configurar Canvas
    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle("SMED")
    c.escola_nome = escola
    width, height = A4
    
    # Renderizar as páginas de forma modularizada
    capa.render(c, width, height, escola, regional)
    introducao.render(c, width, height)
    if not df_mat_escola.empty:
        formacao_classe.render(c, width, height, df_mat_escola, df_distorcao_escola)
    if not df_ideb_escola.empty:
        ideb.render(c, width, height, df_ideb_escola, df_taxa_escola)
    if not df_taxa_escola.empty:
        taxa_rendimento.render(c, width, height, df_taxa_escola)
    if not df_distorcao_escola.empty:
        distorcao.render(c, width, height, df_distorcao_escola)
    if not df_prosa.empty:
        prosa.render(c, width, height, df_prosa)
    
    if df_prosa_media_escola is not None and not df_prosa_media_escola.empty:
        prosa_proficiencia.render(c, width, height, df_prosa_media_escola)
        
    if df_sabe_escola is not None and not df_sabe_escola.empty:
        sabe.render(c, width, height, df_sabe_escola)
        # sabe_proficiencia.render(c, width, height, df_sabe_escola)
        
    if not df_fluencia_escola.empty:
        fluencia_leitora.render(c, width, height, df_fluencia_escola)
    
    c.save()

def main():
    print("Iniciando geração de relatórios (Plataforma Modular)...")
    
    output_dir = r'G:\Shared drives\Indicadores do Painel Educação à Vista\BOLETIM DAS ESCOLAS'
    # output_dir = 'relatorios'
    # if os.path.exists(output_dir):
    #     shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Carregar dados PROSA
    df_boletim = pd.read_parquet('data/prosa_boletim.parquet')
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    # Unificando regionais
    df_escolas['TRI_NM_REGIONAL'] = df_escolas['TRI_NM_REGIONAL'].replace(['CIDADE BAIXA', 'LIBERDADE'], 'CIDADE BAIXA E LIBERDADE')
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES', 
        'ESCOLA MUNICIPAL CSU DE PERNAMBUES'
    )
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES', 
        'ESCOLA MUNICIPAL CSU DE PERNAMBUES'
    )
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA', 
        'ESCOLA MUNICIPAL JARDIM BRASILIA'
    )
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA', 
        'ESCOLA MUNICIPAL JARDIM BRASILIA'
    )
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA', 
        'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    )
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace(
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA', 
        'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    )
    df_prosa = clean_data(df_boletim, df_escolas)
    
    # Carregar dados IDEB, MATRÍCULAS, FLUÊNCIA, TAXA DE RENDIMENTO e DISTORÇÃO
    df_ideb = pd.read_excel('data/IDEB.xlsx')
    df_matriculas = pd.read_excel('data/MATRICULAS.xlsx')
    df_fluencia_25 = fluencia_leitora.load_real_data('data/leitura_diag_2025.xlsx')
    df_fluencia_26 = fluencia_leitora.load_real_data('data/leitura_diag_2026.xlsx')
    df_fluencia = pd.concat([df_fluencia_25, df_fluencia_26])
    if not df_fluencia.empty and 'ESCOLA' in df_fluencia.columns:
        df_fluencia['ESCOLA'] = (df_fluencia['ESCOLA'].astype(str)
            .str.replace(r'^EM ', 'ESCOLA MUNICIPAL ', regex=True)
            .str.replace(r'^CMEI ', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL ', regex=True))
    df_taxa = pd.read_excel('data/TAXA_RENDIMENTO.xlsx')
    df_distorcao = pd.read_excel('data/TAXA_DISTORCAO.xlsx')
    
    # Carregar dados SABE
    try:
        df_sabe = pd.read_excel('data/sabe.xlsx')
        df_sabe['TRI_NM_ESCOLA_CLEAN'] = df_sabe['TRI_NM_ESCOLA'].str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        df_sabe['ANO'] = df_sabe['TRI_ANO_AVALIACAO'].str[-4:]
        df_sabe['AVG_PROFICIENCIA'] = pd.to_numeric(df_sabe['AVG_PROFICIENCIA'], errors='coerce').fillna(0)

    except Exception as e:
        print(f"Erro ao carregar SABE: {e}")
        df_sabe = pd.DataFrame()
    
    # Carregar dados PROSA Proficiência (Média Alunos)
    try:
        df_prosa_media_raw = pd.read_parquet('data/prosa_media_alunos.parquet')
        df_prosa_media_raw['TRI_NM_ESCOLA'] = df_prosa_media_raw['TRI_NM_ESCOLA'].replace(
            'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES', 
            'ESCOLA MUNICIPAL CSU DE PERNAMBUES'
        )
        df_prosa_media_raw['TRI_NM_ESCOLA'] = df_prosa_media_raw['TRI_NM_ESCOLA'].replace(
            'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA', 
            'ESCOLA MUNICIPAL JARDIM BRASILIA'
        )
        df_prosa_media_raw['TRI_NM_ESCOLA'] = df_prosa_media_raw['TRI_NM_ESCOLA'].replace(
            'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA', 
            'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
        )
        df_prosa_media = pd.merge(df_prosa_media_raw, df_escolas, on='TRI_NM_ESCOLA', how='inner')
        df_prosa_media['ANO'] = df_prosa_media['TRI_ANO_AVALIACAO'].str[:4]
    except:
        df_prosa_media = pd.DataFrame()
  
    lista_escolas_regionais = df_prosa[['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA']].drop_duplicates()
    # lista_escolas_regionais = lista_escolas_regionais[lista_escolas_regionais['TRI_NM_ESCOLA'].isin(['ESCOLA MUNICIPAL 15 DE OUTUBRO', 'ESCOLA MUNICIPAL XAVIER MARQUES'])]
    # lista_escolas_regionais = lista_escolas_regionais[lista_escolas_regionais['TRI_NM_REGIONAL']!='SAO CAETANO']
    lista_escolas_regionais = lista_escolas_regionais.sort_values(['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA'])
    print(len(lista_escolas_regionais))
    count = 1
    for _, row in lista_escolas_regionais.iterrows():
        escola = row['TRI_NM_ESCOLA']
        regional = row['TRI_NM_REGIONAL']
        
        df_prosa_escola = df_prosa[df_prosa['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO'])
        
        # Filtrar dados por escola
        df_ideb_escola = df_ideb[df_ideb['ESCOLA'] == escola]
        df_mat_escola = df_matriculas[df_matriculas['ESCOLA'] == escola]
        
        if not df_fluencia.empty and 'ESCOLA' in df_fluencia.columns:
            df_fluencia_escola = df_fluencia[df_fluencia['ESCOLA'] == escola]
        else:
            df_fluencia_escola = pd.DataFrame()
            
        if not df_taxa.empty and 'ESCOLA' in df_taxa.columns:
            df_taxa_escola = df_taxa[df_taxa['ESCOLA'] == escola]
        else:
            df_taxa_escola = pd.DataFrame()
            
        if not df_distorcao.empty and 'ESCOLA' in df_distorcao.columns:
            df_distorcao_escola = df_distorcao[df_distorcao['ESCOLA'] == escola]
        else:
            df_distorcao_escola = pd.DataFrame()
            
        if not df_prosa_media.empty:
            df_prosa_media_escola = df_prosa_media[df_prosa_media['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO'])
        else:
            df_prosa_media_escola = pd.DataFrame()
            
        if not df_sabe.empty:
            df_sabe_escola = df_sabe[df_sabe['TRI_NM_ESCOLA_CLEAN'] == escola]
        else:
            df_sabe_escola = pd.DataFrame()
            
        regional_dir = os.path.join(output_dir, str(regional))
        os.makedirs(regional_dir, exist_ok=True)
        
        print(f"Gerando relatório: {escola} - Regional {regional} {count}/{len(lista_escolas_regionais)}")
        generate_school_report(escola, regional, df_prosa_escola, df_ideb_escola, df_mat_escola, df_fluencia_escola, df_taxa_escola, df_distorcao_escola, regional_dir, df_prosa_media_escola, df_sabe_escola)
        
        # count += 1
        # if count > 1:
        #     break
            
    print("Processo concluído.")

if __name__ == "__main__":
    main()

