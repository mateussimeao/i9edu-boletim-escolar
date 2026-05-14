import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from pages import (
    capa, introducao, formacao_classe,
    ideb, ideb_vista,
    prosa, prosa_proficiencia,
    fluencia_leitora, fluencia_leitora_vista,
    taxa_rendimento, taxa_rendimento_vista,
    distorcao, distorcao_vista,
    sabe, metas,
)
from config import OUTPUT_BOLETIM
from generator._utils import abrev_escola, aggregate_ideb, aggregate_metas


def gerar_escola(data: dict, regional_filter: str = None, escola_filter: str = None):
    print("Gerando boletins por ESCOLA...")
    os.makedirs(OUTPUT_BOLETIM, exist_ok=True)

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
        df_ideb_e       = data['ideb'][data['ideb']['ESCOLA'] == escola]
        df_mat_e        = data['matriculas'][data['matriculas']['ESCOLA'] == escola] if 'ESCOLA' in data['matriculas'].columns else pd.DataFrame()
        df_fluencia_e   = data['fluencia'][data['fluencia']['ESCOLA'] == escola] if not data['fluencia'].empty and 'ESCOLA' in data['fluencia'].columns else pd.DataFrame()
        df_taxa_e       = data['taxa'][data['taxa']['ESCOLA'] == escola] if not data['taxa'].empty and 'ESCOLA' in data['taxa'].columns else pd.DataFrame()
        df_distorcao_e  = data['distorcao'][data['distorcao']['ESCOLA'] == escola] if not data['distorcao'].empty and 'ESCOLA' in data['distorcao'].columns else pd.DataFrame()
        df_media_e      = data['prosa_media'][data['prosa_media']['TRI_NM_ESCOLA'] == escola].dropna(subset=['TRI_ANO_AVALIACAO']) if not data['prosa_media'].empty else pd.DataFrame()
        df_sabe_e       = data['sabe'][data['sabe']['TRI_NM_ESCOLA_CLEAN'] == escola] if not data['sabe'].empty else pd.DataFrame()

        regional_dir = os.path.join(OUTPUT_BOLETIM, str(regional))
        os.makedirs(regional_dir, exist_ok=True)

        print(f"  [{count}/{total}] {escola} — {regional}")
        _render_escola(escola, regional, df_prosa_e, df_ideb_e, df_mat_e, df_fluencia_e, df_taxa_e, df_distorcao_e, regional_dir, df_media_e, df_sabe_e)


def _render_escola(escola, regional, df_prosa, df_ideb, df_mat, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None):
    escola_arq = abrev_escola(escola)
    filename = os.path.join(output_dir, f"boletim_escolar_{regional}_{escola_arq}.pdf".replace(" ", "_").replace("/", "_"))

    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle("SMED")
    c.escola_nome = escola
    width, height = A4

    capa.render(c, width, height, escola, regional)
    introducao.render(c, width, height)

    if not df_mat.empty:
        formacao_classe.render(c, width, height, df_mat, df_distorcao)
    if not df_ideb.empty:
        ideb.render(c, width, height, df_ideb, df_taxa)
    if not df_taxa.empty:
        taxa_rendimento.render(c, width, height, df_taxa)
    if not df_distorcao.empty:
        distorcao.render(c, width, height, df_distorcao)
    if not df_prosa.empty:
        prosa.render(c, width, height, df_prosa)
    if df_prosa_media is not None and not df_prosa_media.empty:
        prosa_proficiencia.render(c, width, height, df_prosa_media)
    if df_sabe is not None and not df_sabe.empty:
        sabe.render(c, width, height, df_sabe)
    if not df_fluencia.empty:
        fluencia_leitora.render(c, width, height, df_fluencia)

    c.save()


def gerar_regional(data: dict, regional_filter: str = None):
    print("Gerando boletins por REGIONAL...")
    os.makedirs(OUTPUT_BOLETIM, exist_ok=True)

    regionais = sorted(data['escolas']['TRI_NM_REGIONAL'].unique())
    if regional_filter:
        regionais = [r for r in regionais if r == regional_filter.upper()]

    total = len(regionais)
    for count, regional in enumerate(regionais, 1):
        print(f"  [{count}/{total}] {regional}")

        df_prosa_r      = data['prosa'][data['prosa']['TRI_NM_REGIONAL'] == regional]
        df_media_r      = data['prosa_media'][data['prosa_media']['TRI_NM_REGIONAL'] == regional] if not data['prosa_media'].empty else pd.DataFrame()
        df_ideb_r       = aggregate_ideb(data['ideb'][data['ideb']['REGIONAL'] == regional] if 'REGIONAL' in data['ideb'].columns else pd.DataFrame())
        df_mat_r        = data['matriculas'][data['matriculas']['REGIONAL'] == regional] if 'REGIONAL' in data['matriculas'].columns else pd.DataFrame()
        df_fluencia_r   = data['fluencia'][data['fluencia']['REGIONAL'] == regional] if not data['fluencia'].empty and 'REGIONAL' in data['fluencia'].columns else pd.DataFrame()
        df_taxa_r       = data['taxa'][data['taxa']['REGIONAL'] == regional] if not data['taxa'].empty and 'REGIONAL' in data['taxa'].columns else pd.DataFrame()
        df_distorcao_r  = data['distorcao'][data['distorcao']['REGIONAL'] == regional] if not data['distorcao'].empty and 'REGIONAL' in data['distorcao'].columns else pd.DataFrame()
        df_sabe_r       = data['sabe'][data['sabe']['REGIONAL'] == regional] if not data['sabe'].empty and 'REGIONAL' in data['sabe'].columns else pd.DataFrame()
        df_metas_r      = aggregate_metas(
            data['metas'][data['metas']['REGIONAL'] == regional] if not data['metas'].empty and 'REGIONAL' in data['metas'].columns else pd.DataFrame(),
            f"MÉDIA REGIONAL: {regional}",
        )

        regional_dir = os.path.join(OUTPUT_BOLETIM, str(regional))
        os.makedirs(regional_dir, exist_ok=True)
        _render_regional(regional, df_prosa_r, df_ideb_r, df_mat_r, df_fluencia_r, df_taxa_r, df_distorcao_r, regional_dir, df_media_r, df_sabe_r, df_metas_r)


def _render_regional(regional, df_prosa, df_ideb, df_mat, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    filename = os.path.join(output_dir, f"boletim_regional_{regional}.pdf".replace(" ", "_").replace("/", "_"))

    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(f"SMED - BOLETIM REGIONAL: {regional}")
    c.escola_nome = f"REGIONAL: {regional}"
    c.no_qr = True
    width, height = A4

    capa.render(c, width, height, f"REGIONAL: {regional}", regional)
    if not df_ideb.empty:
        ideb.render(c, width, height, df_ideb, df_taxa)
    if not df_taxa.empty:
        taxa_rendimento.render(c, width, height, df_taxa)
    if not df_distorcao.empty:
        distorcao.render(c, width, height, df_distorcao)
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


def gerar_rede(data: dict):
    print("Gerando boletim da REDE...")
    output_dir = os.path.join(OUTPUT_BOLETIM, 'REDE')
    os.makedirs(output_dir, exist_ok=True)

    df_metas_rede = aggregate_metas(data['metas'], 'MÉDIA REDE')
    _render_rede(data['prosa'], data['ideb_rede'], data['matriculas'], data['fluencia'], data['taxa'], data['distorcao'], output_dir, data['prosa_media'], data['sabe'], df_metas_rede)


def _render_rede(df_prosa, df_ideb, df_mat, df_fluencia, df_taxa, df_distorcao, output_dir, df_prosa_media=None, df_sabe=None, df_metas=None):
    filename = os.path.join(output_dir, "boletim_rede.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle("SMED - BOLETIM REDE MUNICIPAL")
    c.escola_nome = "REDE MUNICIPAL"
    c.no_qr = True
    width, height = A4

    capa.render(c, width, height, "REDE MUNICIPAL", "TODAS AS REGIONAIS")
    if not df_ideb.empty:
        ideb.render(c, width, height, df_ideb, df_taxa)
    if not df_taxa.empty:
        taxa_rendimento.render(c, width, height, df_taxa)
    if not df_distorcao.empty:
        distorcao.render(c, width, height, df_distorcao)
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
