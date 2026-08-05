import pandas as pd
import json
from datetime import datetime
import os
import requests
import io
import time

import zipfile
import datetime

def fetch_fund_quota(cnpj):
    now = datetime.datetime.now()
    # Tenta o mes atual e o mes anterior (se o mes virou hoje, o csv pode nao estar pronto)
    for months_ago in [0, 1]:
        # Logica para subtrair meses
        # usando timedelta aproximado (30 dias) ou replace no mes (precisa tratar mudanca de ano)
        year = now.year
        month = now.month - months_ago
        if month <= 0:
            month += 12
            year -= 1

        date_str = f"{year}{month:02d}"
        url = f'https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_{date_str}.zip'
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    filename = z.namelist()[0]
                    with z.open(filename) as zf:
                        df_fundo_full = pd.read_csv(zf, sep=';')
                        if 'CNPJ_FUNDO_CLASSE' in df_fundo_full.columns:
                            col_cnpj = 'CNPJ_FUNDO_CLASSE'
                        elif 'CNPJ_FUNDO' in df_fundo_full.columns:
                            col_cnpj = 'CNPJ_FUNDO'
                        else:
                            continue

                        df_fundo = df_fundo_full[df_fundo_full[col_cnpj] == cnpj]
                        if not df_fundo.empty:
                            latest_date = df_fundo['DT_COMPTC'].max()
                            latest_data = df_fundo[df_fundo['DT_COMPTC'] == latest_date].iloc[0]
                            date_obj = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
                            return date_obj.strftime('%d/%m/%Y'), float(latest_data['VL_QUOTA'])
        except Exception as e:
            print(f"Erro ao buscar cota do fundo em {date_str}: {e}")
    return None, None

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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

max_retries = 3
retry_delay = 5
csv_content = None

for attempt in range(max_retries):
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        csv_content = response.text
        break
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
        else:
            print(f"Failed to fetch CSV after {max_retries} attempts.")
            exit(1)

try:
    df = pd.read_csv(io.StringIO(csv_content), sep=";", decimal=",")
except Exception as e:
    print(f"Error parsing CSV: {e}")
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


# Buscar cota do fundo REAL INVESTOR
cnpj_real_investor = "10.500.884/0001-05"
data_fundo, cota_fundo = fetch_fund_quota(cnpj_real_investor)
if data_fundo and cota_fundo:
    resultados.append({
        "titulo": "REAL INVESTOR FIC FIA - BDR NIVEL I",
        "venda": cota_fundo,
        "atualizado": data_fundo
    })

with open('dados.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"Atualizado dados.json com {len(resultados)} títulos em {ultima_data.strftime('%d/%m/%Y')}.")
