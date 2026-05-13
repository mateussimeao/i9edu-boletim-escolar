import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pages import formacao_classe, ideb_vista, prosa, fluencia_leitora, taxa_rendimento_vista, distorcao_vista, prosa_proficiencia, fluencia_leitora_vista, metas, sabe
import shutil

def clean_data(df_boletim, df_escolas):
    df = pd.merge(df_boletim, df_escolas, on='TRI_NM_ESCOLA', how='inner')
    df['PERCENTUAL_PADRAO'] = df['PERCENTUAL_PADRAO'].fillna(0)
    df['ANO'] = df['TRI_ANO_AVALIACAO'].str[:4]
    return df

def save_indicator_pdf(regional, school_dir, indicator_name, render_func, *args):
    """Gera um PDF separado para um indicador específico (Médial Regional)."""
    filename = os.path.join(school_dir, f"{indicator_name}_{regional}.pdf".replace("/", "_"))
    
    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(f"SMED - {indicator_name} - {regional}")
    c.escola_nome = f"MÉDIA REGIONAL: {regional}"
    width, height = A4
    
    # Chama a função de renderização do módulo
    # Note: Usamos 'MÉDIA REGIONAL' no lugar de 'escola' se a função aceitar o nome
    # Algumas funções de render podem precisar de adaptação se usarem o nome da escola no canvas
    # No caso da Vista, a maioria usa apenas o regional_df.
    render_func(c, width, height, *args)
    
    try:
        c.save()
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)

def generate_regional_reports(regional, df_prosa, df_ideb_reg, df_mat_reg, df_fluencia_reg, df_taxa_reg, df_distorcao_reg, school_dir, df_prosa_media_reg=None, df_sabe_reg=None, df_metas_reg=None):
    """Gera os PDFs individuais agregados por regional."""
    
    # # 1. Formação de Classe
    # if not df_mat_reg.empty:
    #     save_indicator_pdf(regional, school_dir, "Formacao_Classe", formacao_classe.render, df_mat_reg, df_distorcao_reg)
    
    # 2. IDEB
    if not df_ideb_reg.empty:
        save_indicator_pdf(regional, school_dir, "IDEB", ideb_vista.render, df_ideb_reg)
    
    # 3. Taxa de Rendimento
    if not df_taxa_reg.empty:
        save_indicator_pdf(regional, school_dir, "Taxa_Rendimento", taxa_rendimento_vista.render, df_taxa_reg)
    
    # 4. Distorção
    if not df_distorcao_reg.empty:
        save_indicator_pdf(regional, school_dir, "Taxa_Distorcao", distorcao_vista.render, df_distorcao_reg)
    
    # 5. Prosa Padrão
    if not df_prosa.empty:
        save_indicator_pdf(regional, school_dir, "Prosa_Padrao_Desempenho", prosa.render, df_prosa)
    
    # 5.1 Prosa Proficiência
    df_p_media = df_prosa_media_reg if df_prosa_media_reg is not None else pd.DataFrame()
    if not df_p_media.empty:
        save_indicator_pdf(regional, school_dir, "Prosa", prosa_proficiencia.render, df_p_media)
    
    # 6. Fluência Leitora
    if not df_fluencia_reg.empty:
        save_indicator_pdf(regional, school_dir, "Fluencia Leitora", fluencia_leitora_vista.render, df_fluencia_reg)
        
    # 7. SABE
    if df_sabe_reg is not None and not df_sabe_reg.empty:
        # Excluir PDFs antigos do SABE para evitar acúmulos de nomes anteriores
        for f in os.listdir(school_dir):
            if f.startswith("SABE") and f.endswith(".pdf"):
                try:
                    os.remove(os.path.join(school_dir, f))
                except Exception as e:
                    print(f"Erro ao excluir {f}: {e}")
        # Nota: Caso sabe.py precise de ajustes para regional, será impresso.
        save_indicator_pdf(regional, school_dir, "SABE", sabe.render, df_sabe_reg)
        
    # 8. Metas
    if df_metas_reg is not None and not df_metas_reg.empty:
        save_indicator_pdf(regional, school_dir, "Metas", metas.render, df_metas_reg)

def main():
    print("Iniciando geração de relatórios de MÉDIA REGIONAL (Estrutura Vista)...")
    
    output_dir = 'G:\Shared drives\Indicadores do Painel Educação à Vista\RELATORIOS SMED'
    # output_dir = 'relatorios_vista'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Carregar e Padronizar Escolas (para unificação de regionais)
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    df_escolas['TRI_NM_REGIONAL'] = df_escolas['TRI_NM_REGIONAL'].replace(['CIDADE BAIXA', 'LIBERDADE', 'CIDADE BAIXA E LIBERDADE'], 'CIDADE BAIXA LIBERDADE')
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace({
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA': 'ESCOLA MUNICIPAL JARDIM BRASILIA',
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA': 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    })
    
    # 2. Carregar dados PROSA e fazer merge com escolas padronizadas
    df_boletim = pd.read_parquet('data/prosa_boletim.parquet')
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace({
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA': 'ESCOLA MUNICIPAL JARDIM BRASILIA',
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA': 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    })
    df_prosa = clean_data(df_boletim, df_escolas)

    # 3. Carregar dados PROSA Proficiência (Média Alunos)
    try:
        df_prosa_media_raw = pd.read_parquet('data/prosa_media_alunos.parquet')
        df_prosa_media_raw['TRI_NM_ESCOLA'] = df_prosa_media_raw['TRI_NM_ESCOLA'].replace({
            'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
            'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA': 'ESCOLA MUNICIPAL JARDIM BRASILIA',
            'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA': 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
        })
        df_prosa_media = pd.merge(df_prosa_media_raw, df_escolas, on='TRI_NM_ESCOLA', how='inner')
        df_prosa_media['ANO'] = df_prosa_media['TRI_ANO_AVALIACAO'].str[:4]
    except:
        df_prosa_media = pd.DataFrame()
    
    # 4. Carregar outros dados e padronizar regionais neles também
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

    df_taxa = pd.read_excel('data/TAXA_RENDIMENTO.xlsx')
    df_distorcao = pd.read_excel('data/TAXA_DISTORCAO.xlsx')
    
    # 5. Adicionar REGIONAL às outras bases via merge com df_escolas
    # Usamos LEFT join para garantir que não percamos dados, e depois filtramos
    df_escolas_ref = df_escolas[['TRI_NM_ESCOLA', 'TRI_NM_REGIONAL']].drop_duplicates()
    
    # Mapeamento: ESCOLA -> TRI_NM_ESCOLA
    df_ideb = pd.merge(df_ideb, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    df_matriculas = pd.merge(df_matriculas, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    df_fluencia = pd.merge(df_fluencia, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    df_taxa = pd.merge(df_taxa, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    df_distorcao = pd.merge(df_distorcao, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    
    # Carregar dados SABE
    try:
        df_sabe = pd.read_excel('data/sabe.xlsx')
        df_sabe['TRI_NM_ESCOLA_CLEAN'] = df_sabe['TRI_NM_ESCOLA'].astype(str).str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        df_sabe['ANO'] = df_sabe['TRI_ANO_AVALIACAO'].astype(str).str[-4:]
        df_sabe['AVG_PROFICIENCIA'] = pd.to_numeric(df_sabe['AVG_PROFICIENCIA'], errors='coerce').fillna(0)
        df_sabe = pd.merge(df_sabe, df_escolas_ref, left_on='TRI_NM_ESCOLA_CLEAN', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    except Exception as e:
        print(f"Erro ao carregar SABE: {e}")
        df_sabe = pd.DataFrame()
        
    # Carregar dados METAS
    try:
        df_metas = pd.read_excel('data/METAS.xlsx')
        df_metas['ESCOLA'] = df_metas['ESCOLA'].astype(str).str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        df_metas = pd.merge(df_metas, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left').rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    except Exception as e:
        print(f"Erro ao carregar METAS: {e}")
        df_metas = pd.DataFrame()
    
    # Obter lista de regionais únicas
    regionais_unicas = sorted(df_escolas['TRI_NM_REGIONAL'].unique())
    total = len(regionais_unicas)
    count = 1
    
    for regional in regionais_unicas:
        print(f"Gerando Médias Regionais: {regional} [{count}/{total}]")
        
        # Filtros por Regional
        df_prosa_reg = df_prosa[df_prosa['TRI_NM_REGIONAL'] == regional]
        
        if not df_prosa_media.empty:
            df_prosa_media_reg = df_prosa_media[df_prosa_media['TRI_NM_REGIONAL'] == regional]
        else:
            df_prosa_media_reg = pd.DataFrame()
            
        df_ideb_reg = df_ideb[df_ideb['REGIONAL'] == regional] if 'REGIONAL' in df_ideb.columns else pd.DataFrame()
        df_mat_reg = df_matriculas[df_matriculas['REGIONAL'] == regional] if 'REGIONAL' in df_matriculas.columns else pd.DataFrame()
        
        if not df_fluencia.empty and 'REGIONAL' in df_fluencia.columns:
            df_fluencia_reg = df_fluencia[df_fluencia['REGIONAL'] == regional]
        else:
            df_fluencia_reg = pd.DataFrame()
            
        if not df_taxa.empty:
            df_taxa_reg = df_taxa[df_taxa['REGIONAL'] == regional]
        else:
            df_taxa_reg = pd.DataFrame()
            
        if not df_distorcao.empty and 'REGIONAL' in df_distorcao.columns:
            df_distorcao_reg = df_distorcao[df_distorcao['REGIONAL'] == regional]
        else:
            df_distorcao_reg = pd.DataFrame()
            
        if not df_sabe.empty and 'REGIONAL' in df_sabe.columns:
            df_sabe_reg = df_sabe[df_sabe['REGIONAL'] == regional]
        else:
            df_sabe_reg = pd.DataFrame()
            
        if not df_metas.empty and 'REGIONAL' in df_metas.columns:
            df_metas_reg = df_metas[df_metas['REGIONAL'] == regional]
            if not df_metas_reg.empty:
                for col in ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']:
                    if col in df_metas_reg.columns:
                        df_metas_reg[col] = pd.to_numeric(df_metas_reg[col], errors='coerce')
                df_metas_reg = df_metas_reg.groupby(['ANO_AVALIACAO', 'ANO_ESCOLARIDADE'], as_index=False)[['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']].mean()
                df_metas_reg['ESCOLA'] = f"MÉDIA REGIONAL: {regional}"
        else:
            df_metas_reg = pd.DataFrame()

        # Validação e Agregação IDEB
        if not df_ideb_reg.empty:
            if 'IDEB_ETAPA' in df_ideb_reg.columns:
                df_ideb_reg = df_ideb_reg[df_ideb_reg['IDEB_ETAPA'].astype(str).str.strip() != '-']
            
            # Converter para numérico para evitar erros na média
            cols_ideb = ['IDEB', 'NOTA_P', 'FLUXO', 'MATEMATICA', 'PORTUGUES']
            for col in cols_ideb:
                if col in df_ideb_reg.columns:
                    df_ideb_reg[col] = pd.to_numeric(df_ideb_reg[col], errors='coerce')
            
            # Agrupar médias por ano e etapa para o Gráfico de Linha
            df_ideb_reg = df_ideb_reg.groupby(['IDEB_ANO', 'IDEB_ETAPA'], as_index=False)[
                [c for c in cols_ideb if c in df_ideb_reg.columns]
            ].mean()
            
        # Estrutura de pastas: [Regional] / MEDIA_REGIONAL
        regional_dir = os.path.join(output_dir, str(regional), "MEDIA_REGIONAL")
        os.makedirs(regional_dir, exist_ok=True)
        
        generate_regional_reports(regional, df_prosa_reg, df_ideb_reg, df_mat_reg, df_fluencia_reg, df_taxa_reg, df_distorcao_reg, regional_dir, df_prosa_media_reg, df_sabe_reg, df_metas_reg)
        
        count += 1
        # if count == 2:
        #     break
            
    print("Processo concluído.")

if __name__ == "__main__":
    main()
