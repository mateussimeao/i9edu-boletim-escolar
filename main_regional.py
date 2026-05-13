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

def generate_regional_report(regional, df_prosa, df_ideb_reg, df_mat_reg, df_fluencia_reg, df_taxa_reg, df_distorcao_reg, output_dir, df_prosa_media_reg=None, df_sabe_reg=None, df_metas_reg=None):
    filename = os.path.join(output_dir, f"boletim_regional_{regional}.pdf".replace(" ", "_").replace("/", "_"))

    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(f"SMED - BOLETIM REGIONAL: {regional}")
    c.escola_nome = f"REGIONAL: {regional}"
    c.no_qr = True
    width, height = A4

    capa.render(c, width, height, f"REGIONAL: {regional}", regional)

    # if not df_mat_reg.empty:
    #     cols_sum = [col for col in ['QTD_MATRICULADOS', 'QTD_DEFICIENTES', 'QTD_ALUNOS_REDE', 'QTD_ALUNOS_NOVOS'] if col in df_mat_reg.columns]
    #     df_mat_agg = df_mat_reg.groupby('ANO_ESCOLARIZACAO_LISTAGEM', as_index=False)[cols_sum].sum()
    #     formacao_classe.render(c, width, height, df_mat_agg, df_distorcao_reg)
    if not df_ideb_reg.empty:
        ideb_vista.render(c, width, height, df_ideb_reg)
    if not df_taxa_reg.empty:
        taxa_rendimento_vista.render(c, width, height, df_taxa_reg)
    if not df_distorcao_reg.empty:
        distorcao_vista.render(c, width, height, df_distorcao_reg)
    if not df_prosa.empty:
        prosa.render(c, width, height, df_prosa)
    if df_prosa_media_reg is not None and not df_prosa_media_reg.empty:
        prosa_proficiencia.render(c, width, height, df_prosa_media_reg)
    if df_sabe_reg is not None and not df_sabe_reg.empty:
        sabe.render(c, width, height, df_sabe_reg)
    if not df_fluencia_reg.empty:
        fluencia_leitora_vista.render(c, width, height, df_fluencia_reg)
    if df_metas_reg is not None and not df_metas_reg.empty:
        metas.render(c, width, height, df_metas_reg)

    c.save()

def main():
    print("Iniciando geração de boletins paginados por REGIONAL...")

    output_dir = r'G:\Shared drives\Indicadores do Painel Educação à Vista\BOLETIM DAS ESCOLAS'
    # output_dir = 'relatorios'
    os.makedirs(output_dir, exist_ok=True)

    # 1. Carregar e Padronizar Escolas
    df_escolas = pd.read_parquet('data/prosa_escolas.parquet')
    df_escolas['TRI_NM_REGIONAL'] = df_escolas['TRI_NM_REGIONAL'].replace(['CIDADE BAIXA', 'LIBERDADE'], 'CIDADE BAIXA E LIBERDADE')
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

    # 4. Carregar outros dados
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

    # 5. Adicionar REGIONAL às bases via merge com df_escolas
    df_escolas_ref = df_escolas[['TRI_NM_ESCOLA', 'TRI_NM_REGIONAL']].drop_duplicates()

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

    regionais_unicas = sorted(df_escolas['TRI_NM_REGIONAL'].unique())
    total = len(regionais_unicas)
    count = 1

    for regional in regionais_unicas:
        print(f"Gerando boletim regional: {regional} [{count}/{total}]")

        df_prosa_reg = df_prosa[df_prosa['TRI_NM_REGIONAL'] == regional]

        df_prosa_media_reg = df_prosa_media[df_prosa_media['TRI_NM_REGIONAL'] == regional] if not df_prosa_media.empty else pd.DataFrame()

        df_ideb_reg = df_ideb[df_ideb['REGIONAL'] == regional] if 'REGIONAL' in df_ideb.columns else pd.DataFrame()
        df_mat_reg = df_matriculas[df_matriculas['REGIONAL'] == regional] if 'REGIONAL' in df_matriculas.columns else pd.DataFrame()

        df_fluencia_reg = df_fluencia[df_fluencia['REGIONAL'] == regional] if not df_fluencia.empty and 'REGIONAL' in df_fluencia.columns else pd.DataFrame()
        df_taxa_reg = df_taxa[df_taxa['REGIONAL'] == regional] if not df_taxa.empty else pd.DataFrame()
        df_distorcao_reg = df_distorcao[df_distorcao['REGIONAL'] == regional] if not df_distorcao.empty and 'REGIONAL' in df_distorcao.columns else pd.DataFrame()
        df_sabe_reg = df_sabe[df_sabe['REGIONAL'] == regional] if not df_sabe.empty and 'REGIONAL' in df_sabe.columns else pd.DataFrame()

        df_metas_reg = pd.DataFrame()
        if not df_metas.empty and 'REGIONAL' in df_metas.columns:
            df_metas_reg = df_metas[df_metas['REGIONAL'] == regional].copy()
            if not df_metas_reg.empty:
                for col in ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']:
                    if col in df_metas_reg.columns:
                        df_metas_reg[col] = pd.to_numeric(df_metas_reg[col], errors='coerce')
                df_metas_reg = df_metas_reg.groupby(['ANO_AVALIACAO', 'ANO_ESCOLARIDADE'], as_index=False)[
                    [c for c in ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT'] if c in df_metas_reg.columns]
                ].mean()
                df_metas_reg['ESCOLA'] = f"MÉDIA REGIONAL: {regional}"

        if not df_ideb_reg.empty:
            if 'IDEB_ETAPA' in df_ideb_reg.columns:
                df_ideb_reg = df_ideb_reg[df_ideb_reg['IDEB_ETAPA'].astype(str).str.strip() != '-']
            cols_ideb = ['IDEB', 'NOTA_P', 'FLUXO', 'MATEMATICA', 'PORTUGUES']
            for col in cols_ideb:
                if col in df_ideb_reg.columns:
                    df_ideb_reg[col] = pd.to_numeric(df_ideb_reg[col], errors='coerce')
            df_ideb_reg = df_ideb_reg.groupby(['IDEB_ANO', 'IDEB_ETAPA'], as_index=False)[
                [c for c in cols_ideb if c in df_ideb_reg.columns]
            ].mean()

        regional_dir = os.path.join(output_dir, str(regional))
        os.makedirs(regional_dir, exist_ok=True)
        generate_regional_report(regional, df_prosa_reg, df_ideb_reg, df_mat_reg, df_fluencia_reg, df_taxa_reg, df_distorcao_reg, regional_dir, df_prosa_media_reg, df_sabe_reg, df_metas_reg)

        count += 1
        # if count > 1:
        #     break

    print("Processo concluído.")

if __name__ == "__main__":
    main()
