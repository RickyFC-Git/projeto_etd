import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

RAW_DIR = "data/raw"
SILVER_DIR = "data/silver"
GOLD_DIR = "data/gold"

os.makedirs(SILVER_DIR, exist_ok=True)
os.makedirs(GOLD_DIR, exist_ok=True)


# 1. CAMADA STAGING / SILVER (Limpeza e Tipagem)
def transform_silver_owid():
    path_raw = os.path.join(RAW_DIR, "owid-covid-data.csv")
    logging.info(f"A processar a camada Silver para OWID: {path_raw}")
    
    df = pd.read_csv(path_raw)
    
    df = df.dropna(subset=["iso_code"])
    df = df[~df["iso_code"].str.startswith("OWID_")]
    
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    
    metric_cols = ["new_cases", "new_deaths", "total_cases", "total_deaths"]
    df[metric_cols] = df[metric_cols].fillna(0)
    
    df = df.drop_duplicates(subset=["iso_code", "date"])
    
    path_output = os.path.join(SILVER_DIR, "silver_owid_covid.csv")
    df.to_csv(path_output, index=False)
    logging.info(f"Camada Silver OWID concluída. Registos: {len(df)}")
    return df


def transform_silver_who():
    path_raw = os.path.join(RAW_DIR, "who_life_expectancy.csv")
    logging.info(f"A processar a camada Silver para a WHO: {path_raw}")
    
    df = pd.read_csv(path_raw)
    
    if "SpatialDimType" in df.columns:
        df = df[df["SpatialDimType"] == "COUNTRY"]
        
    if "Dim1" in df.columns:
        df = df[df["Dim1"] == "SEX_BTSX"]
        
    rename_cols = {
        "SpatialDim": "iso_code",
        "TimeDim": "year",
        "NumericValue": "life_expectancy"
    }
    df = df.rename(columns=rename_cols)
    
    available_cols = [c for c in rename_cols.values() if c in df.columns]
    df = df[available_cols].dropna(subset=["iso_code", "year"])
    
    df = df.drop_duplicates(subset=["iso_code", "year"])
    
    path_output = os.path.join(SILVER_DIR, "silver_who_life_expectancy.csv")
    df.to_csv(path_output, index=False)
    logging.info(f"Camada Silver WHO concluída. Registos: {len(df)}")
    return df


def transform_silver_vaccination():
    path_raw = os.path.join(RAW_DIR, "country_vaccinations.csv")
    logging.info(f"A processar a camada Silver para a Vacinação: {path_raw}")

    df = pd.read_csv(path_raw)
    initial_count = len(df)

    before = len(df)
    df = df[~df["iso_code"].str.startswith("OWID_")]
    removed_owid = before - len(df)
    logging.info(f"  Removidas {removed_owid} linhas com iso_code OWID_* (regiões agregadas)")

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    cols_to_drop = [
        "source_name", "source_website",
        "total_vaccinations_per_hundred", "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred", "daily_vaccinations_per_million"
    ]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    df["num_vaccine_types"] = df["vaccines"].str.split(",").apply(len)

    cumulative_cols = ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]
    df = df.sort_values(["iso_code", "date"])
    df[cumulative_cols] = df.groupby("iso_code")[cumulative_cols].ffill()

    daily_cols = ["daily_vaccinations_raw", "daily_vaccinations"]
    df[daily_cols] = df[daily_cols].fillna(0)

    before_dup = len(df)
    df = df.drop_duplicates(subset=["iso_code", "date"])
    removed_dup = before_dup - len(df)
    if removed_dup > 0:
        logging.warning(f"  Removidos {removed_dup} duplicados (iso_code + date)")

    path_output = os.path.join(SILVER_DIR, "silver_vaccination.csv")
    df.to_csv(path_output, index=False)
    logging.info(f"Camada Silver Vacinação concluída. Registos: {len(df)} (de {initial_count})")
    return df


# 2. VALIDAÇÃO E DATA QUALITY (Relatório)
def run_data_quality_checks(df_owid, df_who, df_vacc):
    logging.info("A executar testes de Data Quality...")
    report_lines = ["=== RELATÓRIO DE QUALIDADE DE DADOS ===\n"]

    report_lines.append("[ OWID COVID ]")
    report_lines.append(f"  Total de registos: {len(df_owid)}")
    report_lines.append(f"  Países únicos: {df_owid['iso_code'].nunique()}")
    report_lines.append(f"  Intervalo de datas: {df_owid['date'].min()} -> {df_owid['date'].max()}")

    neg_cases = (df_owid["new_cases"] < 0).sum()
    report_lines.append(f"  Registos com new_cases negativos: {neg_cases}")

    null_iso = df_owid["iso_code"].isnull().sum()
    report_lines.append(f"  iso_code nulos: {null_iso}")

    dup_owid = df_owid.duplicated(subset=["iso_code", "date"]).sum()
    report_lines.append(f"  Duplicados (iso_code + date): {dup_owid}")

    report_lines.append(f"  Países sem nenhum caso registado: {(df_owid.groupby('iso_code')['new_cases'].sum() == 0).sum()}")

    report_lines.append("\n[ WHO Life Expectancy ]")
    report_lines.append(f"  Total de registos: {len(df_who)}")
    report_lines.append(f"  Países únicos: {df_who['iso_code'].nunique()}")
    report_lines.append(f"  Anos cobertos: {sorted(df_who['year'].unique())[0]} -> {sorted(df_who['year'].unique())[-1]}")

    null_iso_who = df_who["iso_code"].isnull().sum()
    report_lines.append(f"  iso_code nulos: {null_iso_who}")

    out_of_bounds = ((df_who["life_expectancy"] < 30) | (df_who["life_expectancy"] > 100)).sum()
    report_lines.append(f"  Life expectancy fora do intervalo [30-100]: {out_of_bounds}")

    dup_who = df_who.duplicated(subset=["iso_code", "year"]).sum()
    report_lines.append(f"  Duplicados (iso_code + year): {dup_who}")

    report_lines.append("\n[ Vacinação COVID (Kaggle) ]")
    report_lines.append(f"  Total de registos (pós-limpeza): {len(df_vacc)}")
    report_lines.append(f"  Países únicos: {df_vacc['iso_code'].nunique()}")
    report_lines.append(f"  Intervalo de datas: {df_vacc['date'].min()} -> {df_vacc['date'].max()}")

    null_total_vacc = df_vacc["total_vaccinations"].isnull().sum()
    null_pct = round(null_total_vacc / len(df_vacc) * 100, 1)
    report_lines.append(f"  Nulos em total_vaccinations (pós-ffill): {null_total_vacc} ({null_pct}%)")
    report_lines.append(f"  Decisão: forward fill por país para colunas cumulativas; dias sem reporte preenchidos com 0 nos diários")

    dup_vacc = df_vacc.duplicated(subset=["iso_code", "date"]).sum()
    report_lines.append(f"  Duplicados (iso_code + date): {dup_vacc}")

    report_lines.append(f"  Média de tipos de vacina por país: {round(df_vacc.groupby('iso_code')['num_vaccine_types'].max().mean(), 1)}")

    report_lines.append("\n[ Integração entre fontes ]")
    owid_countries = set(df_owid["iso_code"].unique())
    who_countries = set(df_who["iso_code"].unique())
    vacc_countries = set(df_vacc["iso_code"].unique())

    common_owid_who = owid_countries & who_countries
    common_all = owid_countries & who_countries & vacc_countries

    report_lines.append(f"  Países em comum OWID + WHO: {len(common_owid_who)}")
    report_lines.append(f"  Países em comum OWID + WHO + Vacinação: {len(common_all)}")
    report_lines.append(f"  Países apenas no OWID (sem life expectancy): {len(owid_countries - who_countries)}")
    report_lines.append(f"  Países apenas na WHO (sem dados COVID): {len(who_countries - owid_countries)}")
    report_lines.append(f"  Países com dados COVID mas sem dados de vacinação: {len(owid_countries - vacc_countries)}")
    report_lines.append(f"  Decisão: inner join entre OWID e WHO; left join com vacinação para reter países sem dados de vacinas")

    report_lines.append("\n=== FIM DO RELATÓRIO ===")

    report_path = "data_quality_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logging.info(f"Relatório de qualidade guardado em '{report_path}'.")


# 3. CAMADA CURATED / GOLD (Integração e Métricas)
def transform_gold_curated(df_owid, df_who, df_vacc):
    logging.info("A gerar a camada Gold (Métricas e Integração)...")

    df_owid_yearly = df_owid.groupby(["iso_code", "year", "location"]).agg(
        total_cases_year=("new_cases", "sum"),
        total_deaths_year=("new_deaths", "sum"),
        max_stringency_index=("stringency_index", "max"),
        population=("population", "first")
    ).reset_index()

    df_who_latest = (
        df_who.sort_values("year")
        .groupby("iso_code")
        .last()
        .reset_index()
        .drop(columns=["year"], errors="ignore")
    )

    df_vacc_yearly = df_vacc.groupby(["iso_code", "year"]).agg(
        max_total_vaccinations=("total_vaccinations", "max"),
        max_people_vaccinated=("people_vaccinated", "max"),
        max_people_fully_vaccinated=("people_fully_vaccinated", "max"),
        total_daily_vaccinations=("daily_vaccinations", "sum"),
        num_vaccine_types=("num_vaccine_types", "max")
    ).reset_index()

    df_gold = pd.merge(df_owid_yearly, df_who_latest, on="iso_code", how="inner")
    df_gold = pd.merge(df_gold, df_vacc_yearly, on=["iso_code", "year"], how="left")

    df_gold["death_rate_per_100k"] = (df_gold["total_deaths_year"] / df_gold["population"]) * 100000
    df_gold["vaccination_rate"] = (df_gold["max_people_vaccinated"] / df_gold["population"]) * 100

    path_output = os.path.join(GOLD_DIR, "gold_covid_health_analytics.csv")
    df_gold.to_csv(path_output, index=False)
    logging.info(f"Camada Gold gerada com sucesso! Registos finais: {len(df_gold)}")
    return df_gold


if __name__ == "__main__":
    logging.info("A iniciar a transformação de dados...")

    silver_owid = transform_silver_owid()
    silver_who = transform_silver_who()
    silver_vacc = transform_silver_vaccination()

    run_data_quality_checks(silver_owid, silver_who, silver_vacc)

    transform_gold_curated(silver_owid, silver_who, silver_vacc)

    logging.info("Transformação de dados concluída com sucesso!")