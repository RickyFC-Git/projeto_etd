import pandas as pd
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_raw_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, "data", "raw", filename)

def extract_owid_data():
    path = get_raw_path("owid-covid-data.csv")
    print(f"--- A ler Dataset Volumoso: {path}")
    
    if not os.path.exists(path):
        print(f"Ficheiro não encontrado em: {path}")
        return None
    
    df = pd.read_csv(path)
    print(f"Sucesso! {len(df)} linhas carregadas.")
    return df

def extract_who_api():
    url = "https://ghoapi.azureedge.net/api/WHOSIS_000001"
    print(f"--- A testar API da WHO: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df_api = pd.DataFrame(data['value'])
        print(f"API ligada com sucesso! {len(df_api)} registos obtidos.")
        return df_api
    except Exception as e:
        print(f"Problema no API: {e}")
        return None

def main():
    print("EXTRAÇÃO\n")
    
    covid_df = extract_owid_data()
    api_df = extract_who_api()
    
    print("\n VERIFICAÇÃO FINAL")
    if covid_df is not None and api_df is not None:
        print("PRONTO: Ambas as fontes (Volumosa + API) estão funcionais.")
    else:
        print("ATENÇÃO: Verifica os erros acima antes de entregar.")

if __name__ == "__main__":
    main()