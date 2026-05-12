import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pages import capa, formacao_classe, ideb_vista, prosa, fluencia_leitora, taxa_rendimento_vista, distorcao_vista, prosa_proficiencia, fluencia_leitora_vista, metas, sabe

def clean_data(df_boletim, df_escolas):
    df = pd.merge(df_boletim, df_escolas, on='TRI_NM_ESCOLA', how='inner')
    df['PERCENTUAL_PADRAO'] = df['PERCENTUAL_PADRAO'].fillna(0)
    df['ANO'] = df['TRI_ANO_AVALIACAO'].str[:4]
    return df

def generate_rede_report(df_prosa, df_ideb, df_mat, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    filename = os.path.join(output_dir, "boletim_rede.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle("SMED - BOLETIM REDE MUNICIPAL")
    c.escola_nome = "REDE MUNICIPAL"
    c.no_qr = True
    width, height = A4

    capa.render(c, width, height, "REDE MUNICIPAL", "TODAS AS REGIONAIS")

    # if not df_mat.empty:
    #     cols_sum = [col for col in ['QTD_MATRICULADOS', 'QTD_DEFICIENTES', 'QTD_ALUNOS_REDE', 'QTD_ALUNOS_NOVOS'] if col in df_mat.columns]
    #     df_mat_agg = df_mat.groupby('ANO_ESCOLARIZACAO_LISTAGEM', as_index=False)[cols_sum].sum()
    #     formacao_classe.render(c, width, height, df_mat_agg, df_distorcao)
    if not df_ideb.empty:
        ideb_vista.render(c, width, height, df_ideb)
    if not df_taxa.empty:
        taxa_rendimento_vista.render(c, width, height, df_taxa)
    if not df_distorcao.empty:
        distorcao_vista.render(c, width, height, df_distorcao)
    if not df_prosa.empty:
        prosa.render(c, width, height, df_prosa)
    if df_prosa_media is not None and not df_prosa_media.empty:
        prosa_proficiencia.render(c, width, height, df_prosa_media)
    if df_sabe is not None and not df_sabe.empty:
        sabe.render(c, width, height, df_sabe)
    if not df_fluencia.empty:
        fluencia_leitora_vista.render(c, width, height, df_fluencia)
    if df_metas is not None and not df_metas.empty:
        metas.render(c, width, height, df_metas)

    c.save()

def main():
    print("Iniciando geração do boletim paginado da REDE...")

    output_base_dir = r'G:\Shared drives\Indicadores do Painel Educação à Vista\BOLETIM DAS ESCOLAS'
    # output_base_dir = 'relatorios'
    output_dir = os.path.join(output_base_dir, "REDE")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Carregar Escolas
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    df_escolas['TRI_NM_ESCOLA'] = df_escolas['TRI_NM_ESCOLA'].replace({
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA': 'ESCOLA MUNICIPAL JARDIM BRASILIA',
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA': 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    })

    # 2. Carregar dados PROSA
    df_boletim = pd.read_parquet('data/prosa_boletim.parquet')
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace({
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL CSU DE PERNAMBUES': 'ESCOLA MUNICIPAL CSU DE PERNAMBUES',
        'CENTRO MUNICIPAL DE EDUCACAO INFANTIL JARDIM BRASILIA': 'ESCOLA MUNICIPAL JARDIM BRASILIA',
        'ESCOLA MUNICIPAL ENGENHEIRO CARLOS BATALHA': 'ESCOLA MUNICIPAL ENG CARLOS BATALHA'
    })
    df_prosa = clean_data(df_boletim, df_escolas)

    # 3. Carregar dados PROSA Proficiência
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

    # 4. Carregar outros dados (IDEB_REDE.xlsx para nível de rede)
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

    # Carregar dados SABE
    try:
        df_sabe = pd.read_excel('data/sabe.xlsx')
        df_sabe['TRI_NM_ESCOLA_CLEAN'] = df_sabe['TRI_NM_ESCOLA'].astype(str).str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        df_sabe['ANO'] = df_sabe['TRI_ANO_AVALIACAO'].astype(str).str[-4:]
        df_sabe['AVG_PROFICIENCIA'] = pd.to_numeric(df_sabe['AVG_PROFICIENCIA'], errors='coerce').fillna(0)
    except Exception as e:
        print(f"Erro ao carregar SABE: {e}")
        df_sabe = pd.DataFrame()

    # Carregar dados METAS (agregar média da rede)
    try:
        df_metas = pd.read_excel('data/METAS.xlsx')
        df_metas['ESCOLA'] = df_metas['ESCOLA'].astype(str).str.replace(r'\bEM\b', 'ESCOLA MUNICIPAL', regex=True).str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        if not df_metas.empty:
            for col in ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']:
                if col in df_metas.columns:
                    df_metas[col] = pd.to_numeric(df_metas[col], errors='coerce')
            df_metas = df_metas.groupby(['ANO_AVALIACAO', 'ANO_ESCOLARIDADE'], as_index=False)[
                [c for c in ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT'] if c in df_metas.columns]
            ].mean()
            df_metas['ESCOLA'] = 'MÉDIA REDE'
    except Exception as e:
        print(f"Erro ao carregar METAS: {e}")
        df_metas = pd.DataFrame()

    # Validação IDEB
    if not df_ideb.empty and 'IDEB_ETAPA' in df_ideb.columns:
        df_ideb = df_ideb[df_ideb['IDEB_ETAPA'].astype(str).str.strip() != '-']

    print("Gerando boletim da REDE...")
    generate_rede_report(df_prosa, df_ideb, df_matriculas, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media, df_sabe, df_metas)

    print(f"Processo concluído. Arquivo salvo em: {output_dir}")

if __name__ == "__main__":
    main()
