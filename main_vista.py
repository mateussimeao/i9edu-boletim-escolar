import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pages import formacao_classe, ideb, prosa, fluencia_leitora, taxa_rendimento, distorcao_vista, prosa_proficiencia, fluencia_leitora_vista, ideb_vista, sabe, sabe_proficiencia, taxa_rendimento_vista, metas
import shutil

def clean_data(df_boletim, df_escolas):
    df = pd.merge(df_escolas, df_boletim, on='TRI_NM_ESCOLA', how='left')
    df['PERCENTUAL_PADRAO'] = df['PERCENTUAL_PADRAO'].fillna(0)
    df['ANO'] = df['TRI_ANO_AVALIACAO'].str[:4]
    return df

def save_indicator_pdf(escola, regional, school_dir, indicator_name, render_func, *args):
    """Gera um PDF separado para um indicador específico."""
    escola_arq = escola.replace("ESCOLA MUNICIPAL", "EM").replace("CENTRO MUNICIPAL DE EDUCACAO INFANTIL", "CMEI")
    filename = os.path.join(school_dir, f"{indicator_name}_{escola_arq}.pdf".replace("/", "_"))
    
    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(f"SMED - {indicator_name}")
    c.escola_nome = escola
    c.qr_code_name = indicator_name
    if indicator_name == "SABE_Padrao_Desempenho":
        c.qr_code_name = "SABE"
    width, height = A4
    
    # Chama a função de renderização do módulo
    render_func(c, width, height, *args)
    
    # Verifica se a página foi gerada (algumas funções podem não gerar nada se não houver dados)
    # No caso do ReportLab, o canvas.save() falha se não houver c.showPage(). 
    # Porém, nossas funções de render já chamam c.showPage() ao final.
    # Mas precisamos garantir que algo foi desenhado.
    try:
        c.save()
    except Exception as e:
        # Se falhar porque não houve páginas (por exemplo, ideb sem dados), deleta o arquivo vazio se existir
        if os.path.exists(filename):
            os.remove(filename)

def generate_individual_reports(escola, regional, df_prosa, df_ideb_escola, df_mat_escola, df_fluencia_escola, df_taxa_escola, df_distorcao_escola, school_dir, df_prosa_media_escola=None, df_sabe_escola=None, df_metas_escola=None):
    """Gera os PDFs individuais para cada indicador dentro da pasta da escola."""
    
    # 1. Formação de Classe
    for f in os.listdir(school_dir):
        if f.startswith("Formacao_Classe") and f.endswith(".pdf"):
            try:
                os.remove(os.path.join(school_dir, f))
            except Exception as e:
                print(f"Erro ao excluir {f}: {e}")
    if not df_mat_escola.empty:
        save_indicator_pdf(escola, regional, school_dir, "Formacao_Classe", formacao_classe.render, df_mat_escola, df_distorcao_escola)
    
    # 2. IDEB
    if not df_ideb_escola.empty:
        save_indicator_pdf(escola, regional, school_dir, "IDEB", ideb_vista.render, df_ideb_escola)
    
    # 3. Taxa de Rendimento
    if not df_taxa_escola.empty:
        save_indicator_pdf(escola, regional, school_dir, "Taxa_Rendimento", taxa_rendimento_vista.render, df_taxa_escola)
    
    # 4. Distorção
    if not df_distorcao_escola.empty:
        save_indicator_pdf(escola, regional, school_dir, "Taxa_Distorcao", distorcao_vista.render, df_distorcao_escola)
    
    # 5. Prosa Padrão
    if not df_prosa.empty:
        save_indicator_pdf(escola, regional, school_dir, "Prosa_Padrao_Desempenho", prosa.render, df_prosa)
    
    # 5.1 Prosa Proficiência
    df_p_media = df_prosa_media_escola if df_prosa_media_escola is not None else pd.DataFrame()
    if not df_p_media.empty:
        save_indicator_pdf(escola, regional, school_dir, "Prosa", prosa_proficiencia.render, df_p_media)
    
    # 6. Fluência Leitora
    if not df_fluencia_escola.empty:
        save_indicator_pdf(escola, regional, school_dir, "Fluencia Leitora", fluencia_leitora.render, df_fluencia_escola)
        
    # 7. SABE
    if df_sabe_escola is not None and not df_sabe_escola.empty:
        # Excluir PDFs antigos do SABE para evitar acúmulos de nomes anteriores
        for f in os.listdir(school_dir):
            if f.startswith("SABE") and f.endswith(".pdf"):
                try:
                    os.remove(os.path.join(school_dir, f))
                except Exception as e:
                    print(f"Erro ao excluir {f}: {e}")
                    
        save_indicator_pdf(escola, regional, school_dir, "SABE_Padrao_Desempenho", sabe.render, df_sabe_escola)
        # save_indicator_pdf(escola, regional, school_dir, "SABE", sabe_proficiencia.render, df_sabe_escola)
        
    # 8. Metas
    if df_metas_escola is not None and not df_metas_escola.empty:
        save_indicator_pdf(escola, regional, school_dir, "Metas", metas.render, df_metas_escola)

def main():
    print("Iniciando geração de relatórios individuais por indicador (Estrutura Vista)...")
    
    output_dir = r'G:\Shared drives\Indicadores do Painel Educação à Vista\RELATORIOS SMED'
    # output_dir = 'relatorios_vista'
    os.makedirs(output_dir, exist_ok=True)
    
    # Carregar dados PROSA
    df_boletim = pd.read_parquet('data/prosa_boletim.parquet')
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    # Unificando regionais
    df_escolas['TRI_NM_REGIONAL'] = df_escolas['TRI_NM_REGIONAL'].replace(['CIDADE BAIXA', 'LIBERDADE', 'CIDADE BAIXA E LIBERDADE'], 'CIDADE BAIXA LIBERDADE')
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES', 
        'ESCOLA MUNICIPAL CSU DE PERNAMBUES'
    )
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA', 
        'ESCOLA MUNICIPAL JARDIM BRASILIA'
    )
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA', 
        'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    )
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES', 
        'ESCOLA MUNICIPAL CSU DE PERNAMBUES'
    )
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace(
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA', 
        'ESCOLA MUNICIPAL JARDIM BRASILIA'
    )
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace(
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA', 
        'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    )
    df_prosa = clean_data(df_boletim, df_escolas)

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
        
    # Carregar dados METAS
    try:
        df_metas = pd.read_excel('data/METAS.xlsx')
        df_metas['ESCOLA'] = df_metas['ESCOLA'].astype(str)
        df_metas['ESCOLA'] = df_metas['ESCOLA'].str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        df_metas['ESCOLA'] = df_metas['ESCOLA'].replace(
            'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES', 'ESCOLA MUNICIPAL CSU DE PERNAMBUES'
        ).replace(
            'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA', 'ESCOLA MUNICIPAL JARDIM BRASILIA'
        ).replace(
            'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA', 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
        )
    except Exception as e:
        print(f"Erro ao carregar METAS: {e}")
        df_metas = pd.DataFrame()  
    # Obter lista de escolas e regionais ordenadas
    dados_lista = [
        # ("CAJAZEIRAS", "ESCOLA MUNICIPAL BATISTA DE VALERIA"),
        # ("CAJAZEIRAS", "ESCOLA MUNICIPAL PROFESSOR AFONSO TEMPORAL"),
        # ("CAJAZEIRAS", "ESCOLA MUNICIPAL RECANTO DO SOL"),
        # ("CENTRO", "ESCOLA MUNICIPAL CLEMILDA ANDRADE"),
        # ("CENTRO", "ESCOLA MUNICIPAL SATURNINO CABRAL"),
        # ("CENTRO", "ESCOLA MUNICIPAL VISCONDE DE CAIRU DE BROTAS"),
        # ("CIDADE BAIXA E LIBERDADE", "ESCOLA MUNICIPAL CARMELITANA 25 DE AGOSTO"),
        # ("CIDADE BAIXA E LIBERDADE", "ESCOLA MUNICIPAL SOCIEDADE TOME DE SOUZA"),
        # ("ITAPUA", "ESCOLA MUNICIPAL JORGE AMADO"),
        # ("ITAPUA", "ESCOLA MUNICIPAL RAYMUNDO LEMOS DE SANTANA"),
        # ("CIDADE BAIXA E LIBERDADE", "ESCOLA MUNICIPAL ADALGISA SOUZA PINTO"),
        # ("CIDADE BAIXA E LIBERDADE", "ESCOLA MUNICIPAL BARAO DO RIO BRANCO"),
        # ("PIRAJA", "ESCOLA MUNICIPAL CECILIA MEIRELES"),
        # ("PIRAJA", "ESCOLA MUNICIPAL DE PAU DA LIMA"),
        # ("PIRAJA", "ESCOLA MUNICIPAL DE SAO MARCOS"),
        # ("PIRAJA", "ESCOLA MUNICIPAL MANOEL CLEMENTE FERREIRA"),
        # ("SAO CAETANO", "ESCOLA MUNICIPAL ASSISTENCIAL NOSSA SENHORA DE GUADALUPE"),
        # ("SAO CAETANO", "ESCOLA MUNICIPAL COMUNITARIA DO BOM JUA"),
        # ("SAO CAETANO", "ESCOLA MUNICIPAL CONEGO EMILIO LOBO"),
        # ("SAO CAETANO", "ESCOLA MUNICIPAL ENGENHEIRO GILBERTO PIRES MARINHO"),
        # ("SAO CAETANO", "ESCOLA MUNICIPAL ENG CARLOS BATALHA"),
        # ("SAO CAETANO", "ESCOLA MUNICIPAL PROFESSOR GUEDES"),
        # ("SUBURBIO I", "CENTRO MUNICIPAL DE EDUCACAO INFANTIL DONA MARIA EMILIA GADELHA VIANNA"),
        # ("SUBURBIO I", "ESCOLA MUNICIPAL DURVAL PINHEIRO"),
        # ("SUBURBIO I", "ESCOLA MUNICIPAL PAULO MENDES DE AGUIAR"),
        # ("SUBURBIO I", "ESCOLA MUNICIPAL RADIALISTA RAIMUNDO VARELLA FREIRE JUNIOR"),
        # ("SUBURBIO II", "ESCOLA MUNICIPAL CLAUDEMIRA SANTOS LIMA"),
        # ("SUBURBIO II", "ESCOLA MUNICIPAL DE BOTELHO"),
        # ("SUBURBIO II", "ESCOLA MUNICIPAL NOSSA SENHORA DE FATIMA"),
        # ("SUBURBIO II", "ESCOLA MUNICIPAL OITO DE MAIO")
    ]

    # Transformando em DataFrame
    # df_teste = pd.DataFrame(dados_lista, columns=['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA'])
    
    lista_escolas_regionais = df_prosa[['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA']].drop_duplicates()
    # lista_escolas_regionais = df_teste[['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA']].drop_duplicates()
    # lista_escolas_regionais = lista_escolas_regionais[lista_escolas_regionais['TRI_NM_REGIONAL'] != 'SAO CAETANO']
    # lista_escolas_regionais = lista_escolas_regionais[lista_escolas_regionais['TRI_NM_REGIONAL'].isin(['CENTRO'])]
    lista_escolas_regionais = lista_escolas_regionais.sort_values(['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA'])
    count = 1
    total = len(lista_escolas_regionais)
    print(total)
    for _, row in lista_escolas_regionais.iterrows():
        escola = row['TRI_NM_ESCOLA']
        regional = row['TRI_NM_REGIONAL']
        
        # Filtros
        df_prosa_escola = df_prosa[df_prosa['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO'])
        
        if not df_prosa_media.empty:
            df_prosa_media_escola = df_prosa_media[df_prosa_media['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO'])
        else:
            df_prosa_media_escola = pd.DataFrame()
        df_ideb_escola = df_ideb[df_ideb['ESCOLA'] == escola]
        df_ideb_escola = df_ideb_escola[df_ideb_escola['IDEB_ETAPA'].astype(str).str.strip() != '-']
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
            
        if not df_sabe.empty:
            df_sabe_escola = df_sabe[df_sabe['TRI_NM_ESCOLA_CLEAN'] == escola]
        else:
            df_sabe_escola = pd.DataFrame()
        
        if not df_metas.empty:
            df_metas_escola = df_metas[df_metas['ESCOLA'] == escola]  
        else:
            df_metas_escola = pd.DataFrame()
            
        # Estrutura de pastas: Regional / Escola
        escola_dir_name = escola.replace("ESCOLA MUNICIPAL", "EM").replace("CENTRO MUNICIPAL DE EDUCACAO INFANTIL", "CMEI").replace("/", "_")
        school_dir = os.path.join(output_dir, str(regional), escola_dir_name)
        os.makedirs(school_dir, exist_ok=True)
        
        print(f"Gerando indicadores: {escola} - Regional {regional} [{count}/{total}]")
        generate_individual_reports(escola, regional, df_prosa_escola, df_ideb_escola, df_mat_escola, df_fluencia_escola, df_taxa_escola, df_distorcao_escola, school_dir, df_prosa_media_escola, df_sabe_escola, df_metas_escola)
        
        count += 1
        # Para teste, descomente as linhas abaixo se quiser limitar
        # if count > 2:
        #     break
            
    print("Processo concluído.")

if __name__ == "__main__":
    main()