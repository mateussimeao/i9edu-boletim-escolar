import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def abrev_escola(escola: str) -> str:
    return (
        escola
        .replace("ESCOLA MUNICIPAL", "EM")
        .replace("CENTRO MUNICIPAL DE EDUCACAO INFANTIL", "CMEI")
    )


def aggregate_ideb(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = ['IDEB', 'NOTA_P', 'FLUXO', 'MATEMATICA', 'PORTUGUES']
    for col in cols:
        if col in df.columns:
            df = df.copy()
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.groupby(['IDEB_ANO', 'IDEB_ETAPA'], as_index=False)[
        [c for c in cols if c in df.columns]
    ].mean()


def aggregate_metas(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty:
        return df
    cols = ['PROF_POR', 'PROF_MAT', 'META_POR', 'META_MAT']
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df_agg = df.groupby(['ANO_AVALIACAO', 'ANO_ESCOLARIDADE'], as_index=False)[
        [c for c in cols if c in df.columns]
    ].mean()
    df_agg['ESCOLA'] = label
    return df_agg


def save_indicator_pdf(filename: str, escola_nome: str, indicator_name: str, render_func, *args, qr_code_name: str = None):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(f"SMED - {indicator_name}")
    c.escola_nome = escola_nome
    if qr_code_name is not None:
        c.qr_code_name = qr_code_name
    width, height = A4
    render_func(c, width, height, *args)
    try:
        c.save()
    except Exception:
        if os.path.exists(filename):
            os.remove(filename)


def _safe(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Retorna df filtrado se col existir, senão DataFrame vazio."""
    if not df.empty and col in df.columns:
        return df
    return pd.DataFrame()
