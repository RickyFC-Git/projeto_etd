# Projeto de ETD: Saúde e Saúde Pública

Este projeto consiste no desenvolvimento de um pipeline ETL (Extract, Transform, Load) modular focado no domínio da Saúde & Saúde Pública. O objetivo principal é a consolidação de dados de múltiplas fontes para analisar correlações entre indicadores de saúde pública, propagação da COVID-19 e coberturas vacinais globais.

A arquitetura segue o princípio de **Medallion Architecture** (Raw ➔ Silver ➔ Gold), garantindo a rastreabilidade e qualidade dos dados e garante a rastreabilidade, integridade estrutural e qualidade dos dados através da aplicação de regras estritas de validação, culminando no carregamento automatizado dos dados para um sistema relacional local (**SQLite**).


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
        
        T1 & T2 & T3 & T4 --> DQ{Validações SQL Pós-Carga}
    end