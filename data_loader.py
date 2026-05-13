import pandas as pd
from pages import fluencia_leitora
from config import (
    PROSA_BOLETIM, PROSA_ESCOLAS, PROSA_MEDIA,
    IDEB, IDEB_REDE, MATRICULAS, TAXA_RENDIMENTO, TAXA_DISTORCAO,
    SABE, METAS, FLUENCIA_2025, FLUENCIA_2026,
    SCHOOL_RENAME, REGIONAL_RENAME_BOLETIM, REGIONAL_RENAME_RELATORIO,
)


def load_data(formato: str) -> dict:
    """Carrega e normaliza todos os dados para o formato informado.

    Args:
        formato: 'boletim' ou 'relatorio'

    Returns:
        Dicionário com todos os DataFrames prontos para uso pelos geradores.
    """
    regional_rename = (
        REGIONAL_RENAME_BOLETIM if formato == 'boletim' else REGIONAL_RENAME_RELATORIO
    )

    # --- Escolas (referência de nomes e regionais) ---
    df_escolas = pd.read_parquet(PROSA_ESCOLAS)
    df_escolas['TRI_NM_ESCOLA']   = df_escolas['TRI_NM_ESCOLA'].replace(SCHOOL_RENAME)
    df_escolas['TRI_NM_REGIONAL'] = df_escolas['TRI_NM_REGIONAL'].replace(regional_rename)
    df_escolas_ref = df_escolas[['TRI_NM_ESCOLA', 'TRI_NM_REGIONAL']].drop_duplicates()

    # --- PROSA Boletim ---
    df_boletim = pd.read_parquet(PROSA_BOLETIM)
    df_boletim['TRI_NM_ESCOLA'] = df_boletim['TRI_NM_ESCOLA'].replace(SCHOOL_RENAME)
    df_prosa = pd.merge(df_boletim, df_escolas, on='TRI_NM_ESCOLA', how='inner')
    df_prosa['PERCENTUAL_PADRAO'] = df_prosa['PERCENTUAL_PADRAO'].fillna(0)
    df_prosa['ANO'] = df_prosa['TRI_ANO_AVALIACAO'].str[:4]

    # --- PROSA Proficiência (Média Alunos) ---
    try:
        df_media_raw = pd.read_parquet(PROSA_MEDIA)
        df_media_raw['TRI_NM_ESCOLA'] = df_media_raw['TRI_NM_ESCOLA'].replace(SCHOOL_RENAME)
        df_prosa_media = pd.merge(df_media_raw, df_escolas, on='TRI_NM_ESCOLA', how='inner')
        df_prosa_media['ANO'] = df_prosa_media['TRI_ANO_AVALIACAO'].str[:4]
    except Exception as e:
        print(f"Aviso: prosa_media_alunos não carregado — {e}")
        df_prosa_media = pd.DataFrame()

    # --- IDEB (escola / regional) ---
    df_ideb = pd.read_excel(IDEB)
    if 'IDEB_ETAPA' in df_ideb.columns:
        df_ideb = df_ideb[df_ideb['IDEB_ETAPA'].astype(str).str.strip() != '-']
    df_ideb = (
        pd.merge(df_ideb, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left')
        .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
    )

    # --- IDEB Rede ---
    df_ideb_rede = pd.read_excel(IDEB_REDE)
    if 'IDEB_ETAPA' in df_ideb_rede.columns:
        df_ideb_rede = df_ideb_rede[df_ideb_rede['IDEB_ETAPA'].astype(str).str.strip() != '-']

    # --- Matrículas ---
    df_matriculas = pd.read_excel(MATRICULAS)
    if 'ESCOLA' in df_matriculas.columns:
        df_matriculas = (
            pd.merge(df_matriculas, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left')
            .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
        )

    # --- Fluência Leitora ---
    df_fl25 = fluencia_leitora.load_real_data(FLUENCIA_2025)
    df_fl26 = fluencia_leitora.load_real_data(FLUENCIA_2026)
    df_fluencia = pd.concat([df_fl25, df_fl26])
    if not df_fluencia.empty and 'ESCOLA' in df_fluencia.columns:
        df_fluencia['ESCOLA'] = (
            df_fluencia['ESCOLA'].astype(str)
            .str.replace(r'^EM ', 'ESCOLA MUNICIPAL ', regex=True)
            .str.replace(r'^CMEI ', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL ', regex=True)
        )
        df_fluencia = (
            pd.merge(df_fluencia, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left')
            .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
        )

    # --- Taxa de Rendimento ---
    df_taxa = pd.read_excel(TAXA_RENDIMENTO)
    if 'ESCOLA' in df_taxa.columns:
        df_taxa = (
            pd.merge(df_taxa, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left')
            .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
        )

    # --- Taxa de Distorção ---
    df_distorcao = pd.read_excel(TAXA_DISTORCAO)
    if 'ESCOLA' in df_distorcao.columns:
        df_distorcao = (
            pd.merge(df_distorcao, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left')
            .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
        )

    # --- SABE ---
    try:
        df_sabe = pd.read_excel(SABE)
        df_sabe['TRI_NM_ESCOLA_CLEAN'] = (
            df_sabe['TRI_NM_ESCOLA'].astype(str)
            .str.replace(r'\bEM\b',   'ESCOLA MUNICIPAL',                    regex=True)
            .str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        )
        df_sabe['ANO']              = df_sabe['TRI_ANO_AVALIACAO'].astype(str).str[-4:]
        df_sabe['AVG_PROFICIENCIA'] = pd.to_numeric(df_sabe['AVG_PROFICIENCIA'], errors='coerce').fillna(0)
        df_sabe = (
            pd.merge(df_sabe, df_escolas_ref, left_on='TRI_NM_ESCOLA_CLEAN', right_on='TRI_NM_ESCOLA', how='left')
            .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
        )
    except Exception as e:
        print(f"Aviso: SABE não carregado — {e}")
        df_sabe = pd.DataFrame()

    # --- Metas ---
    try:
        df_metas = pd.read_excel(METAS)
        df_metas['ESCOLA'] = (
            df_metas['ESCOLA'].astype(str)
            .str.replace(r'\bEM\b',   'ESCOLA MUNICIPAL',                    regex=True)
            .str.replace(r'\bCMEI\b', 'CENTRO MUNICIPAL DE EDUCACAO INFANTIL', regex=True)
        )
        df_metas['ESCOLA'] = df_metas['ESCOLA'].replace(SCHOOL_RENAME)
        df_metas = (
            pd.merge(df_metas, df_escolas_ref, left_on='ESCOLA', right_on='TRI_NM_ESCOLA', how='left')
            .rename(columns={'TRI_NM_REGIONAL': 'REGIONAL'})
        )
    except Exception as e:
        print(f"Aviso: METAS não carregado — {e}")
        df_metas = pd.DataFrame()

    return {
        'escolas':     df_escolas,
        'prosa':       df_prosa,
        'prosa_media': df_prosa_media,
        'ideb':        df_ideb,
        'ideb_rede':   df_ideb_rede,
        'matriculas':  df_matriculas,
        'fluencia':    df_fluencia,
        'taxa':        df_taxa,
        'distorcao':   df_distorcao,
        'sabe':        df_sabe,
        'metas':       df_metas,
    }
