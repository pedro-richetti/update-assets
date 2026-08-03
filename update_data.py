import pandas as pd
import json
from datetime import datetime
import os

url = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"

# Os titulos desejados e como formata-los
# O CSV tem "Tipo Titulo" e "Data Vencimento"
titulos_desejados = {
    ("Tesouro IPCA+", "2035"): "Tesouro IPCA+ 2035",
    ("Tesouro IPCA+", "2032"): "Tesouro IPCA+ 2032",
    ("Tesouro IPCA+ com Juros Semestrais", "2035"): "Tesouro IPCA+ 2035 c/ Juros",
    ("Tesouro IPCA+", "2029"): "Tesouro IPCA+ 2029",
    ("Tesouro Selic", "2029"): "Tesouro Selic 2029",
    ("Tesouro Selic", "2031"): "Tesouro Selic 2031",
}

try:
    df = pd.read_csv(url, sep=";", decimal=",")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit(1)

# O CSV tem colunas: 'Tipo Titulo', 'Data Vencimento', 'Data Base', 'Taxa Compra Manha', 'Taxa Venda Manha', 'PU Compra Manha', 'PU Venda Manha', 'PU Base Manha'
df['Data Base'] = pd.to_datetime(df['Data Base'], format='%d/%m/%Y')
# Seleciona o dia mais recente
ultima_data = df['Data Base'].max()
df_recente = df[df['Data Base'] == ultima_data].copy()

resultados = []
for index, row in df_recente.iterrows():
    tipo = row['Tipo Titulo']
    vencimento_ano = row['Data Vencimento'].split('/')[-1]

    chave = (tipo, vencimento_ano)
    if chave in titulos_desejados:
        titulo_nome = titulos_desejados[chave]
        venda = row['PU Venda Manha']

        resultados.append({
            "titulo": titulo_nome,
            "venda": venda,
            "atualizado": ultima_data.strftime("%d/%m/%Y")
        })

# Garantir a ordem original desejada
ordem_desejada = list(titulos_desejados.values())
resultados.sort(key=lambda x: ordem_desejada.index(x["titulo"]) if x["titulo"] in ordem_desejada else 999)

with open('dados.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"Atualizado dados.json com {len(resultados)} títulos em {ultima_data.strftime('%d/%m/%Y')}.")
