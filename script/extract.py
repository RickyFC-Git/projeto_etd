import pandas as pd
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

def get_raw_path(filename):
    """Garante o caminho correto para a pasta data/raw definida ou calculada"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    raw_dir = os.getenv("RAW_DATA_PATH", "data/raw/")
    return os.path.join(project_root, raw_dir, filename)

def extract_owid_data():
    path = get_raw_path("owid-covid-data.csv")
    logging.info(f"A ler Dataset Volumoso: {path}")
    
    if not os.path.exists(path):
        logging.error(f"Ficheiro não encontrado em: {path}")
        return None
    
    df = pd.read_csv(path)
    logging.info(f"Sucesso! {len(df)} linhas carregadas do OWID.")
    return df

def extract_who_api():
    base_url = os.getenv("WHO_API_URL")
    if not base_url:
        logging.error("Variável WHO_API_URL não encontrada no ficheiro .env")
        return None
        
    url = f"{base_url}WHOSIS_000001"
    logging.info(f"A chamar API da WHO: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        df_api = pd.DataFrame(data['value'])
        logging.info(f"API ligada com sucesso! {len(df_api)} registos obtidos.")
        
        output_path = get_raw_path("who_life_expectancy.csv")
        df_api.to_csv(output_path, index=False)
        logging.info(f"Dados brutos da API gravados em: {output_path}")
        
        return df_api
    except Exception as e:
        logging.error(f"Problema ao extrair dados da API: {e}")
        return None

if __name__ == "__main__":
    logging.info("A iniciar o pipeline de extração (Semana 1)...")
    owid_df = extract_owid_data()
    who_df = extract_who_api()
    logging.info("Extração concluída com sucesso.")