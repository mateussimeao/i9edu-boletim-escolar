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

def save_indicator_pdf(output_dir, indicator_name, render_func, *args):
    """Gera um PDF separado para um indicador específico (Médial Rede)."""
    filename = os.path.join(output_dir, f"{indicator_name}_REDE.pdf".replace("/", "_"))
    
    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(f"SMED - {indicator_name} - REDE")
    c.escola_nome = "MÉDIA REDE"
    width, height = A4
    
    # Chama a função de renderização do módulo
    render_func(c, width, height, *args)
    
    try:
        c.save()
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)

def generate_rede_reports(df_prosa, df_ideb, df_mat, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    """Gera os PDFs consolidados por rede."""
    
    # # 1. Formação de Classe
    # if not df_mat.empty:
    #     save_indicator_pdf(output_dir, "Formacao_Classe", formacao_classe.render, df_mat, df_distorcao)
    
    # 2. IDEB
    if not df_ideb.empty:
        save_indicator_pdf(output_dir, "IDEB", ideb_vista.render, df_ideb)
    
    # 3. Taxa de Rendimento
    if not df_taxa.empty:
        save_indicator_pdf(output_dir, "Taxa_Rendimento", taxa_rendimento_vista.render, df_taxa)
    
    # 4. Distorção
    if not df_distorcao.empty:
        save_indicator_pdf(output_dir, "Taxa_Distorcao", distorcao_vista.render, df_distorcao)
    
    # 5. Prosa Padrão
    if not df_prosa.empty:
        save_indicator_pdf(output_dir, "Prosa_Padrao_Desempenho", prosa.render, df_prosa)
    
    # 5.1 Prosa Proficiência
    if df_prosa_media is not None and not df_prosa_media.empty:
        save_indicator_pdf(output_dir, "Prosa", prosa_proficiencia.render, df_prosa_media)
    
    # 6. Fluência Leitora
    if not df_fluencia.empty:
        save_indicator_pdf(output_dir, "Fluencia Leitora", fluencia_leitora_vista.render, df_fluencia)
        
    # 7. SABE
    if df_sabe is not None and not df_sabe.empty:
        # Excluir PDFs antigos do SABE para evitar acúmulos de nomes anteriores
        for f in os.listdir(output_dir):
            if f.startswith("SABE") and f.endswith(".pdf"):
                try:
                    os.remove(os.path.join(output_dir, f))
                except Exception as e:
                    print(f"Erro ao excluir {f}: {e}")
        save_indicator_pdf(output_dir, "SABE", sabe.render, df_sabe)
        
    # 8. Metas
    if df_metas is not None and not df_metas.empty:
        save_indicator_pdf(output_dir, "Metas", metas.render, df_metas)

def main():
    print("Iniciando geração de relatórios de REDE (Estrutura Vista)...")
    # output_base_dir = 'relatorios_vista'
    output_base_dir = r"G:\Shared drives\Indicadores do Painel Educação à Vista\RELATORIOS SMED"
    output_dir = os.path.join(output_base_dir, "REDE")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Carregar Escolas (para obter mapeamento se necessário, embora Rede use tudo)
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace({
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA': 'ESCOLA MUNICIPAL JARDIM BRASILIA',
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA': 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    })
    
    # 2. Carregar e Limpar dados PROSA
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
    
    # 4. Carregar outros dados
    df_ideb = pd.read_excel('data/IDEB_REDE.xlsx')
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
    
    # Carregar dados SABE
    try:
        df_sabe = pd.read_excel('data/sabe.xlsx')
        df_sabe['TRI_NM_ESCOLA_CLEAN'] = df_sabe['TRI_NM_ESCOLA'].astype(str).str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        df_sabe['ANO'] = df_sabe['TRI_ANO_AVALIACAO'].astype(str).str[-4:]
        df_sabe['AVG_PROFICIENCIA'] = pd.to_numeric(df_sabe['AVG_PROFICIENCIA'], errors='coerce').fillna(0)
    except Exception as e:
        print(f"Erro ao carregar SABE: {e}")
        df_sabe = pd.DataFrame()
        
    # Carregar dados METAS
    try:
        df_metas = pd.read_excel('data/METAS.xlsx')
        df_metas['ESCOLA'] = df_metas['ESCOLA'].astype(str).str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        if not df_metas.empty:
            for col in ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']:
                if col in df_metas.columns:
                    df_metas[col] = pd.to_numeric(df_metas[col], errors='coerce')
            df_metas = df_metas.groupby(['ANO_AVALIACAO', 'ANO_ESCOLARIDADE'], as_index=False)[['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']].mean()
            df_metas['ESCOLA'] = 'MÉDIA REDE'
    except Exception as e:
        print(f"Erro ao carregar METAS: {e}")
        df_metas = pd.DataFrame()

    # Validação IDEB
    if not df_ideb.empty:
        if 'IDEB_ETAPA' in df_ideb.columns:
            df_ideb = df_ideb[df_ideb['IDEB_ETAPA'].astype(str).str.strip() != '-']
    
    print("Gerando PDFs de REDE...")
    generate_rede_reports(df_prosa, df_ideb, df_matriculas, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media, df_sabe, df_metas)
    
    print(f"Processo concluído. Arquivos salvos em: {output_dir}")

if __name__ == "__main__":
    main()
