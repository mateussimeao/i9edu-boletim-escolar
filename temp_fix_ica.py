import pandas as pd


def main():
    df_ica = pd.read_excel('data/ICA.xlsx', sheet_name='Planilha4', header=3)
    df_dim = pd.read_parquet('data/prosa_escolas.parquet')

    df_ica_fix = pd.merge(df_ica, df_dim, how='left', left_on='Rótulos de Linha', right_on='TRI_NM_ESCOLA')
    df_ica_fix = df_ica_fix.drop(columns=['TRI_NM_ESCOLA'])
    df_ica_fix = df_ica_fix.rename(columns={'TRI_NM_REGIONAL': 'REGIONAL', 'Rótulos de Linha': 'ESCOLA'})
    print(df_ica_fix.head())
    df_ica_fix.to_csv('data/ICA.csv')

if __name__ == "__main__":
    main()
