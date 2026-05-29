# Projeto de ETD: Saúde e Saúde Pública

Este projeto consiste no desenvolvimento de um pipeline ETL (Extract, Transform, Load) modular focado no domínio da Saúde & Saúde Pública. O objetivo é extrair dados epidemiológicos da COVID-19, taxas de vacinação e indicadores globais de expectativa de vida para realizar análises de correlação e impacto.

A arquitetura segue o princípio de **Medallion Architecture** (Raw ➔ Silver ➔ Gold), garantindo a rastreabilidade e qualidade dos dados.

---

## Arquitetura do Pipeline

```mermaid
graph TD
    subgraph "Camada Raw (Semana 1)"
        A[OWID CSV] -->|extract.py| R1[data/raw/owid-covid-data.csv]
        B[WHO GHO API] -->|extract.py| R2[data/raw/who_life_expectancy.csv]
        C[Kaggle CSV] -->|extract.py| R3[data/raw/country_vaccinations.csv]
    end

    subgraph "Camada Silver (Semana 2)"
        R1 -->|Limpeza e Filtros| S1[data/silver/silver_owid.csv]
        R2 -->|Deduplicação Anual| S2[data/silver/silver_who.csv]
        R3 -->|Forward Fill por País| S3[data/silver/silver_vaccination.csv]
    end

    S1 --> DQ[Data Quality Check]
    S2 --> DQ
    S3 --> DQ
    DQ -->|Log| DQR[data_quality_report.txt]

    subgraph "Camada Gold (Semana 2)"
        S1 -->|Joins e Métricas| G[data/gold/gold_covid_health_analytics.csv]
        S2 -->|Joins e Métricas| G
        S3 -->|Joins e Métricas| G
    end

### Modelação da Base de Dados (Diagrama ER)

```mermaid
erDiagram
    silver_covid_epidemiology {
        TEXT iso_code PK
        TEXT date PK
        TEXT continent
        TEXT location
        REAL total_cases
        REAL new_cases
        REAL total_deaths
        REAL new_deaths
        REAL population
        INTEGER year
    }
    silver_covid_vaccination {
        TEXT iso_code PK
        TEXT date PK
        TEXT country
        REAL total_vaccinations
        REAL people_vaccinated
        REAL people_fully_vaccinated
        REAL daily_vaccinations
        TEXT vaccines
        INTEGER year
    }
    silver_health_indicators {
        TEXT iso_code PK
        INTEGER year PK
        REAL life_expectancy
    }
    gold_fact_analytics {
        TEXT iso_code PK
        INTEGER year PK
        TEXT location
        REAL total_cases_year
        REAL total_deaths_year
        REAL max_stringency_index
        REAL population
        REAL life_expectancy
        REAL max_total_vaccinations
        REAL vaccination_rate
    }