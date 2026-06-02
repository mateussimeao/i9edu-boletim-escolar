import pandas as pd

df = pd.read_excel("microdados_ICA.xlsx")

df = df[df["FL_AVALIADO"] == 1]
df = df[df["DC_ETAPA_AVALIADA"] == "ENSINO FUNDAMENTAL DE 9 ANOS - 2º ANO"]
df = df[df["NM_DISCIPLINA"] == "Língua Portuguesa"]

df["FLAG_ALFABETIZADO"] = df["VL_PROFICIENCIA"].apply(lambda x: "Sim" if x >= 743 else "Não")

escolas = pd.read_parquet("data/prosa_escolas.parquet")
df = df.merge(escolas, left_on="NM_ESCOLA", right_on="TRI_NM_ESCOLA", how="left")

totais = df.groupby("NM_ESCOLA").size().rename("total")
contagens = df.groupby(["NM_ESCOLA", "FLAG_ALFABETIZADO"]).size().unstack(fill_value=0)

pivot = contagens.div(totais, axis=0)

for col in ["Sim", "Não"]:
    if col not in pivot.columns:
        pivot[col] = 0.0

pivot["Total Geral"] = pivot["Sim"] + pivot["Não"]
pivot = pivot[["Sim", "Não", "Total Geral"]].reset_index().rename(columns={"NM_ESCOLA": "ESCOLA"})

regional = (
    df[["NM_ESCOLA", "TRI_NM_REGIONAL"]]
    .drop_duplicates("NM_ESCOLA")
    .rename(columns={"NM_ESCOLA": "ESCOLA", "TRI_NM_REGIONAL": "REGIONAL"})
)
pivot = pivot.merge(regional, on="ESCOLA", how="left")
pivot = pivot[["ESCOLA", "Sim", "Não", "Total Geral", "REGIONAL"]]

resumo = pd.DataFrame([{
    "ESCOLA": "Total Geral",
    "Sim": pivot["Sim"].mean(),
    "Não": pivot["Não"].mean(),
    "Total Geral": pivot["Total Geral"].mean(),
    "REGIONAL": "",
}])

resultado = pd.concat([pivot, resumo], ignore_index=True)

resultado.to_csv("ICA.csv", index=False)
print(f"Concluido: {len(pivot)} escolas + linha de resumo")
print(resultado.tail(3).to_string())
