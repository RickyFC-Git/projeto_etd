import os
import sqlite3
import pandas as pd
import logging
from dotenv import load_dotenv

load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SILVER_DIR = os.path.join(BASE_DIR, "data", "processed")
GOLD_DIR = os.path.join(BASE_DIR, os.getenv("GOLD_DATA_PATH", "data/gold"))
DB_PATH = os.path.join(BASE_DIR, os.getenv("DB_PATH", "data/covid_health_analytics.db"))

SQL_SCHEMAS = {
    "silver_covid_epidemiology": """
        CREATE TABLE IF NOT EXISTS silver_covid_epidemiology (
            iso_code TEXT NOT NULL,
            continent TEXT,
            location TEXT,
            date TEXT NOT NULL,
            total_cases REAL,
            new_cases REAL,
            total_deaths REAL,
            new_deaths REAL,
            population REAL,
            year INTEGER,
            PRIMARY KEY (iso_code, date)
        );
    """,
    "silver_covid_vaccination": """
        CREATE TABLE IF NOT EXISTS silver_covid_vaccination (
            country TEXT,
            iso_code TEXT NOT NULL,
            date TEXT NOT NULL,
            total_vaccinations REAL,
            people_vaccinated REAL,
            people_fully_vaccinated REAL,
            daily_vaccinations_raw REAL,
            daily_vaccinations REAL,
            vaccines TEXT,
            year INTEGER,
            num_vaccine_types INTEGER,
            PRIMARY KEY (iso_code, date)
        );
    """,
    "silver_health_indicators": """
        CREATE TABLE IF NOT EXISTS silver_health_indicators (
            iso_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            life_expectancy REAL,
            PRIMARY KEY (iso_code, year)
        );
    """,
    "gold_fact_analytics": """
        CREATE TABLE IF NOT EXISTS gold_fact_analytics (
            iso_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            location TEXT,
            total_cases_year REAL,
            total_deaths_year REAL,
            max_stringency_index REAL,
            population REAL,
            life_expectancy REAL,
            max_total_vaccinations REAL,
            max_people_vaccinated REAL,
            max_people_fully_vaccinated REAL,
            total_daily_vaccinations REAL,
            num_vaccine_types REAL,
            death_rate_per_100k REAL,
            vaccination_rate REAL,
            PRIMARY KEY (iso_code, year)
        );
    """
}

def connect_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database(conn):
    cursor = conn.cursor()
    for table_name, create_query in SQL_SCHEMAS.items():
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        cursor.execute(create_query)
        logging.info(f"Tabela estruturada com sucesso: {table_name} (Esquema estrito aplicado).")
    conn.commit()

def load_table(conn, csv_path, table_name):
    if not os.path.exists(csv_path):
        logging.error(f"Ficheiro CSV em falta para carregamento: {csv_path}")
        return False
    
    df = pd.read_csv(csv_path)
    
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    valid_cols = [col[1] for col in cursor.fetchall()]
    df_filtered = df[[c for c in df.columns if c in valid_cols]]
    
    df_filtered.to_sql(table_name, conn, if_exists='append', index=False)
    logging.info(f"Dados inseridos em '{table_name}': {len(df_filtered)} linhas carregadas do CSV.")
    return True

def run_post_load_validation(conn):
    logging.info("--- A iniciar Validações Pós-Carga (Data Quality SQL) ---")
    cursor = conn.cursor()
    passed_all = True

    cursor.execute("SELECT COUNT(*) FROM gold_fact_analytics WHERE iso_code IS NULL OR year IS NULL;")
    null_pks = cursor.fetchone()[0]
    if null_pks > 0:
        logging.error(f"[FALHA] Detetados {null_pks} registos com Chaves Primárias nulas na tabela Gold!")
        passed_all = False
    else:
        logging.info("[SUCESSO] Sem Chaves Primárias nulas na camada Gold.")

    cursor.execute("""
        SELECT COUNT(DISTINCT g.iso_code) 
        FROM gold_fact_analytics g
        WHERE g.iso_code NOT IN (SELECT DISTINCT s.iso_code FROM silver_covid_epidemiology s);
    """)
    orphan_records = cursor.fetchone()[0]
    if orphan_records > 0:
        logging.warning(f"[AVISO] Foram encontrados {orphan_records} iso_codes órfãos na tabela Gold que não constam na Silver.")
        passed_all = False
    else:
        logging.info("[SUCESSO] Integridade Referencial validada: todos os países mapeados existem nas origens.")

    cursor.execute("SELECT COUNT(*) FROM gold_fact_analytics WHERE vaccination_rate > 200;")
    anomalous_vaccines = cursor.fetchone()[0]
    if anomalous_vaccines > 0:
        logging.warning(f"[AVISO] Encontradas {anomalous_vaccines} linhas com taxa de vacinação anormal (>200%).")
        passed_all = False
    else:
        logging.info("[SUCESSO] Sem anomalias severas detetadas nas métricas calculadas.")

    if passed_all:
        logging.info("=== [CONCLUÍDO] Todos os testes de qualidade SQL passaram com distinção! ===")
    else:
        logging.warning("=== [CONCLUÍDO] Ingestão terminada com alertas pendentes de revisão. ===")

def main():
    logging.info("=== INÍCIO DA ETAPA: LOAD AVANÇADO (SEMANA 3) ===")
    
    conn = connect_db()
    
    try:
        init_database(conn)
        
        datasets_to_load = {
            os.path.join(SILVER_DIR, "silver_owid_covid.csv"): "silver_covid_epidemiology",
            os.path.join(SILVER_DIR, "silver_vaccination.csv"): "silver_covid_vaccination",
            os.path.join(SILVER_DIR, "silver_who_life_expectancy.csv"): "silver_health_indicators",
            os.path.join(GOLD_DIR, "gold_covid_health_analytics.csv"): "gold_fact_analytics"
        }
        
        for csv_file, table_name in datasets_to_load.items():
            load_table(conn, csv_file, table_name)
            
        run_post_load_validation(conn)
        
    except Exception as e:
        logging.critical(f"Falha catastrófica durante o processo de Load: {e}", exc_info=True)
    finally:
        conn.close()
        logging.info("=== Conexão à Base de Dados SQLite encerrada de forma segura ===")

if __name__ == "__main__":
    main()