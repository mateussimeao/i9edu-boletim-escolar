import os
import pandas as pd

from pages import (
    formacao_classe,
    ideb_vista,
    prosa, prosa_proficiencia,
    fluencia_leitora, fluencia_leitora_vista,
    taxa_rendimento_vista,
    distorcao_vista,
    sabe, metas,
)
from config import OUTPUT_RELATORIO
from generator._utils import abrev_escola, aggregate_ideb, aggregate_metas, save_indicator_pdf


def gerar_escola(data: dict, regional_filter: str = None, escola_filter: str = None):
    print("Gerando relatórios individuais por ESCOLA...")
    os.makedirs(OUTPUT_RELATORIO, exist_ok=True)

    lista = data['prosa'][['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA']].drop_duplicates()
    lista = lista.sort_values(['TRI_NM_REGIONAL', 'TRI_NM_ESCOLA'])
    if regional_filter:
        lista = lista[lista['TRI_NM_REGIONAL'] == regional_filter.upper()]
    if escola_filter:
        lista = lista[lista['TRI_NM_ESCOLA'] == escola_filter.upper()]

    total = len(lista)
    for count, (_, row) in enumerate(lista.iterrows(), 1):
        escola   = row['TRI_NM_ESCOLA']
        regional = row['TRI_NM_REGIONAL']

        df_prosa_e      = data['prosa'][data['prosa']['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO'])
        df_media_e      = data['prosa_media'][data['prosa_media']['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO']) if not data['prosa_media'].empty else pd.DataFrame()
        df_ideb_e       = data['ideb'][data['ideb']['ESCOLA'] == escola]
        df_mat_e        = data['matriculas'][data['matriculas']['ESCOLA'] == escola] if 'ESCOLA' in data['matriculas'].columns else pd.DataFrame()
        df_fluencia_e   = data['fluencia'][data['fluencia']['ESCOLA'] == escola] if not data['fluencia'].empty and 'ESCOLA' in data['fluencia'].columns else pd.DataFrame()
        df_taxa_e       = data['taxa'][data['taxa']['ESCOLA'] == escola] if not data['taxa'].empty and 'ESCOLA' in data['taxa'].columns else pd.DataFrame()
        df_distorcao_e  = data['distorcao'][data['distorcao']['ESCOLA'] == escola] if not data['distorcao'].empty and 'ESCOLA' in data['distorcao'].columns else pd.DataFrame()
        df_sabe_e       = data['sabe'][data['sabe']['TRI_NM_ESCOLA_CLEAN'] == escola] if not data['sabe'].empty else pd.DataFrame()
        df_metas_e      = data['metas'][data['metas']['ESCOLA'] == escola] if not data['metas'].empty and 'ESCOLA' in data['metas'].columns else pd.DataFrame()

        escola_dir_name = abrev_escola(escola).replace("/", "_")
        school_dir = os.path.join(OUTPUT_RELATORIO, str(regional), escola_dir_name)
        os.makedirs(school_dir, exist_ok=True)

        print(f"  [{count}/{total}] {escola} — {regional}")
        _render_escola(escola, regional, df_prosa_e, df_ideb_e, df_mat_e, df_fluencia_e, df_taxa_e, df_distorcao_e, school_dir, df_media_e, df_sabe_e, df_metas_e)


def _render_escola(escola, regional, df_prosa, df_ideb, df_mat, df_fluencia, df_taxa, df_distorcao, school_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    escola_arq  = abrev_escola(escola)
    escola_nome = escola

    def _path(indicator):
        return os.path.join(school_dir, f"{indicator}_{escola_arq}.pdf".replace("/", "_"))

    # Formação de Classe — limpa versões anteriores antes de gerar
    for f in os.listdir(school_dir):
        if f.startswith("Formacao_Classe") and f.endswith(".pdf"):
            _try_remove(os.path.join(school_dir, f))
    if not df_mat.empty:
        save_indicator_pdf(_path("Formacao_Classe"), escola_nome, "Formacao_Classe", formacao_classe.render, df_mat, df_distorcao, qr_code_name="Formacao_Classe")

    if not df_ideb.empty:
        save_indicator_pdf(_path("IDEB"), escola_nome, "IDEB", ideb_vista.render, df_ideb, qr_code_name="IDEB")

    if not df_taxa.empty:
        save_indicator_pdf(_path("Taxa_Rendimento"), escola_nome, "Taxa_Rendimento", taxa_rendimento_vista.render, df_taxa, qr_code_name="Taxa_Rendimento")

    if not df_distorcao.empty:
        save_indicator_pdf(_path("Taxa_Distorcao"), escola_nome, "Taxa_Distorcao", distorcao_vista.render, df_distorcao, qr_code_name="Taxa_Distorcao")

    if not df_prosa.empty:
        save_indicator_pdf(_path("Prosa_Padrao_Desempenho"), escola_nome, "Prosa_Padrao_Desempenho", prosa.render, df_prosa, qr_code_name="Prosa_Padrao_Desempenho")

    df_p_media = df_prosa_media if df_prosa_media is not None else pd.DataFrame()
    if not df_p_media.empty:
        save_indicator_pdf(_path("Prosa"), escola_nome, "Prosa", prosa_proficiencia.render, df_p_media, qr_code_name="Prosa")

    if not df_fluencia.empty:
        save_indicator_pdf(_path("Fluencia Leitora"), escola_nome, "Fluencia Leitora", fluencia_leitora.render, df_fluencia, qr_code_name="Fluencia Leitora")

    # SABE — limpa versões anteriores antes de gerar
    if df_sabe is not None and not df_sabe.empty:
        for f in os.listdir(school_dir):
            if f.startswith("SABE") and f.endswith(".pdf"):
                _try_remove(os.path.join(school_dir, f))
        save_indicator_pdf(_path("SABE_Padrao_Desempenho"), escola_nome, "SABE_Padrao_Desempenho", sabe.render, df_sabe, qr_code_name="SABE")

    if df_metas is not None and not df_metas.empty:
        save_indicator_pdf(_path("Metas"), escola_nome, "Metas", metas.render, df_metas, qr_code_name="Metas")


def gerar_regional(data: dict, regional_filter: str = None):
    print("Gerando relatórios individuais por REGIONAL...")
    os.makedirs(OUTPUT_RELATORIO, exist_ok=True)

    regionais = sorted(data['escolas']['TRI_NM_REGIONAL'].unique())
    if regional_filter:
        regionais = [r for r in regionais if r == regional_filter.upper()]

    total = len(regionais)
    for count, regional in enumerate(regionais, 1):
        print(f"  [{count}/{total}] {regional}")

        df_prosa_r      = data['prosa'][data['prosa']['TRI_NM_REGIONAL'] == regional]
        df_media_r      = data['prosa_media'][data['prosa_media']['TRI_NM_REGIONAL'] == regional] if not data['prosa_media'].empty else pd.DataFrame()
        df_ideb_r       = aggregate_ideb(data['ideb'][data['ideb']['REGIONAL'] == regional] if 'REGIONAL' in data['ideb'].columns else pd.DataFrame())
        df_fluencia_r   = data['fluencia'][data['fluencia']['REGIONAL'] == regional] if not data['fluencia'].empty and 'REGIONAL' in data['fluencia'].columns else pd.DataFrame()
        df_taxa_r       = data['taxa'][data['taxa']['REGIONAL'] == regional] if not data['taxa'].empty and 'REGIONAL' in data['taxa'].columns else pd.DataFrame()
        df_distorcao_r  = data['distorcao'][data['distorcao']['REGIONAL'] == regional] if not data['distorcao'].empty and 'REGIONAL' in data['distorcao'].columns else pd.DataFrame()
        df_sabe_r       = data['sabe'][data['sabe']['REGIONAL'] == regional] if not data['sabe'].empty and 'REGIONAL' in data['sabe'].columns else pd.DataFrame()
        df_metas_r      = aggregate_metas(
            data['metas'][data['metas']['REGIONAL'] == regional] if not data['metas'].empty and 'REGIONAL' in data['metas'].columns else pd.DataFrame(),
            f"MÉDIA REGIONAL: {regional}",
        )

        regional_dir = os.path.join(OUTPUT_RELATORIO, str(regional), "MEDIA_REGIONAL")
        os.makedirs(regional_dir, exist_ok=True)
        _render_regional(regional, df_prosa_r, df_ideb_r, df_fluencia_r, df_taxa_r, df_distorcao_r, regional_dir, df_media_r, df_sabe_r, df_metas_r)


def _render_regional(regional, df_prosa, df_ideb, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    escola_nome = f"MÉDIA REGIONAL: {regional}"

    def _path(indicator):
        return os.path.join(output_dir, f"{indicator}_{regional}.pdf".replace("/", "_"))

    if not df_ideb.empty:
        save_indicator_pdf(_path("IDEB"), escola_nome, "IDEB", ideb_vista.render, df_ideb, qr_code_name="IDEB")

    if not df_taxa.empty:
        save_indicator_pdf(_path("Taxa_Rendimento"), escola_nome, "Taxa_Rendimento", taxa_rendimento_vista.render, df_taxa, qr_code_name="Taxa_Rendimento")

    if not df_distorcao.empty:
        save_indicator_pdf(_path("Taxa_Distorcao"), escola_nome, "Taxa_Distorcao", distorcao_vista.render, df_distorcao, qr_code_name="Taxa_Distorcao")

    if not df_prosa.empty:
        save_indicator_pdf(_path("Prosa_Padrao_Desempenho"), escola_nome, "Prosa_Padrao_Desempenho", prosa.render, df_prosa, qr_code_name="Prosa_Padrao_Desempenho")

    df_p_media = df_prosa_media if df_prosa_media is not None else pd.DataFrame()
    if not df_p_media.empty:
        save_indicator_pdf(_path("Prosa"), escola_nome, "Prosa", prosa_proficiencia.render, df_p_media, qr_code_name="Prosa")

    if not df_fluencia.empty:
        save_indicator_pdf(_path("Fluencia Leitora"), escola_nome, "Fluencia Leitora", fluencia_leitora_vista.render, df_fluencia, qr_code_name="Fluencia Leitora")

    if df_sabe is not None and not df_sabe.empty:
        for f in os.listdir(output_dir):
            if f.startswith("SABE") and f.endswith(".pdf"):
                _try_remove(os.path.join(output_dir, f))
        save_indicator_pdf(_path("SABE"), escola_nome, "SABE", sabe.render, df_sabe, qr_code_name="SABE")

    if df_metas is not None and not df_metas.empty:
        save_indicator_pdf(_path("Metas"), escola_nome, "Metas", metas.render, df_metas, qr_code_name="Metas")


def gerar_rede(data: dict):
    print("Gerando relatórios individuais da REDE...")
    output_dir = os.path.join(OUTPUT_RELATORIO, 'REDE')
    os.makedirs(output_dir, exist_ok=True)

    df_metas_rede = aggregate_metas(data['metas'], 'MÉDIA REDE')
    _render_rede(data['prosa'], data['ideb_rede'], data['fluencia'], data['taxa'], data['distorcao'], output_dir, data['prosa_media'], data['sabe'], df_metas_rede)


def _render_rede(df_prosa, df_ideb, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    escola_nome = "MÉDIA REDE"

    def _path(indicator):
        return os.path.join(output_dir, f"{indicator}_REDE.pdf".replace("/", "_"))

    if not df_ideb.empty:
        save_indicator_pdf(_path("IDEB"), escola_nome, "IDEB", ideb_vista.render, df_ideb, qr_code_name="IDEB")

    if not df_taxa.empty:
        save_indicator_pdf(_path("Taxa_Rendimento"), escola_nome, "Taxa_Rendimento", taxa_rendimento_vista.render, df_taxa, qr_code_name="Taxa_Rendimento")

    if not df_distorcao.empty:
        save_indicator_pdf(_path("Taxa_Distorcao"), escola_nome, "Taxa_Distorcao", distorcao_vista.render, df_distorcao, qr_code_name="Taxa_Distorcao")

    if not df_prosa.empty:
        save_indicator_pdf(_path("Prosa_Padrao_Desempenho"), escola_nome, "Prosa_Padrao_Desempenho", prosa.render, df_prosa, qr_code_name="Prosa_Padrao_Desempenho")

    if df_prosa_media is not None and not df_prosa_media.empty:
        save_indicator_pdf(_path("Prosa"), escola_nome, "Prosa", prosa_proficiencia.render, df_prosa_media, qr_code_name="Prosa")

    if not df_fluencia.empty:
        save_indicator_pdf(_path("Fluencia Leitora"), escola_nome, "Fluencia Leitora", fluencia_leitora_vista.render, df_fluencia, qr_code_name="Fluencia Leitora")

    if df_sabe is not None and not df_sabe.empty:
        for f in os.listdir(output_dir):
            if f.startswith("SABE") and f.endswith(".pdf"):
                _try_remove(os.path.join(output_dir, f))
        save_indicator_pdf(_path("SABE"), escola_nome, "SABE", sabe.render, df_sabe, qr_code_name="SABE")

    if df_metas is not None and not df_metas.empty:
        save_indicator_pdf(_path("Metas"), escola_nome, "Metas", metas.render, df_metas, qr_code_name="Metas")


def _try_remove(path: str):
    try:
        os.remove(path)
    except Exception as e:
        print(f"  Aviso: não foi possível remover {path} — {e}")
