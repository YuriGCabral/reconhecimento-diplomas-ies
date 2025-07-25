import pandas as pd

# Carrega os dados uma única vez (pode ser melhorado com cache depois)
df = pd.read_excel("data/RELATORIO_CURSOS_DEFERIMENTO_PLENO_25-06-2025.xlsx")

def filtrar_por_ies(nome_ies):
    filtrado = df[df["noIes"].str.contains(nome_ies, case=False, na=False)]
    return filtrado.to_dict(orient="records")
