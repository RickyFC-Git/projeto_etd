# Projeto de ETD: Saúde e Saúde Pública

Este projeto consiste no desenvolvimento de um pipeline ETL (Extract, Transform, Load) modular focado no domínio da Saúde & Saúde Pública. O objetivo principal é a consolidação de dados de múltiplas fontes para analisar correlações entre indicadores de saúde pública, propagação da COVID-19 e coberturas vacinais globais.

A arquitetura segue o princípio de **Medallion Architecture** (Raw ➔ Silver ➔ Gold), garantindo a rastreabilidade e qualidade dos dados e garante a rastreabilidade, integridade estrutural e qualidade dos dados através da aplicação de regras estritas de validação, culminando no carregamento automatizado dos dados para um sistema relacional local (**SQLite**).


---

## Arquitetura do Pipeline

```mermaid
graph TD

    subgraph "Camada Raw (Semana 1) - Extração"
        A[Our World in Data - CSV] -->|extract.py| R1[data/raw/owid-covid-data.csv]
        B[WHO GHO API - JSON] -->|extract.py| R2[data/raw/who_life_expectancy.csv]
        C[Kaggle Dataset - CSV] -->|extract.py| R3[data/raw/country_vaccinations.csv]
    end

    subgraph "Camada Silver (Semana 2) - Limpeza & Tipagem"
        R1 -->|Limpeza e Filtros| S1[data/silver/silver_owid_covid.csv]
        R2 -->|Deduplicação Anual| S2[data/silver/silver_who_life_expectancy.csv]
        R3 -->|Forward Fill por País| S3[data/silver/silver_vaccination.csv]
    end

    subgraph "Camada Gold (Semana 2) - Enriquecimento & Negócio"
        S1 -->|Joins e Métricas| G[data/gold/gold_covid_health_analytics.csv]
        S2 -->|Joins e Métricas| G
        S3 -->|Joins e Métricas| G
    end

    subgraph "Camada SQL / Relacional (Semana 3) - Carga Avançada"
        S1 -->|load.py - DDL Estrito| T1[(silver_covid_epidemiology)]
        S3 -->|load.py - DDL Estrito| T2[(silver_covid_vaccination)]
        S2 -->|load.py - DDL Estrito| T3[(silver_health_indicators)]
        G -->|load.py - DDL Estrito| T4[(gold_fact_analytics)]

        T1 --> DQ{Validações SQL Pós-Carga}
        T2 --> DQ
        T3 --> DQ
        T4 --> DQ
    end
```

---

# 2. Modelação da Base de Dados (Diagrama ER)

Os dados processados foram carregados para SQLite. Para assegurar a integridade analítica, foram definidas chaves primárias compostas e tipos de dados estritos.

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

    gold_fact_analytics ||--o{ silver_covid_epidemiology : agrega
    gold_fact_analytics ||--o{ silver_covid_vaccination : agrega
    gold_fact_analytics ||--o{ silver_health_indicators : associa
```

---

## Prova da Validação

2026-05-29 22:03:03,296 - INFO - === INÍCIO DA ETAPA: LOAD AVANÇADO (SEMANA 3) ===
2026-05-29 22:03:03,340 - INFO - Tabela estruturada com sucesso: silver_covid_epidemiology (Esquema estrito aplicado).
2026-05-29 22:03:03,359 - INFO - Tabela estruturada com sucesso: silver_covid_vaccination (Esquema estrito aplicado).
2026-05-29 22:03:03,367 - INFO - Tabela estruturada com sucesso: silver_health_indicators (Esquema estrito aplicado).
2026-05-29 22:03:03,375 - INFO - Tabela estruturada com sucesso: gold_fact_analytics (Esquema estrito aplicado).
c:\Users\IG\Desktop\projeto_etd\script\load.py:97: DtypeWarning: Columns (33) have mixed types. Specify dtype option on import or set low_memory=False.
  df = pd.read_csv(csv_path)
2026-05-29 22:03:06,123 - INFO - Dados inseridos em 'silver_covid_epidemiology': 393903 linhas carregadas do CSV.
2026-05-29 22:03:06,578 - INFO - Dados inseridos em 'silver_covid_vaccination': 84056 linhas carregadas do CSV.
2026-05-29 22:03:06,594 - INFO - Dados inseridos em 'silver_health_indicators': 4070 linhas carregadas do CSV.
2026-05-29 22:03:06,608 - INFO - Dados inseridos em 'gold_fact_analytics': 925 linhas carregadas do CSV.
2026-05-29 22:03:06,609 - INFO - --- A iniciar Validações Pós-Carga (Data Quality SQL) ---
2026-05-29 22:03:06,609 - INFO - [SUCESSO] Sem Chaves Primárias nulas na camada Gold.
2026-05-29 22:03:06,633 - INFO - [SUCESSO] Integridade Referencial validada: todos os países mapeados existem nas origens.
2026-05-29 22:03:06,633 - INFO - [SUCESSO] Sem anomalias severas detetadas nas métricas calculadas.
2026-05-29 22:03:06,634 - INFO - === [CONCLUÍDO] Todos os testes de qualidade SQL passaram com distinção! ===
2026-05-29 22:03:06,634 - INFO - === Conexão à Base de Dados SQLite encerrada de forma segura ===