Projeto de ETD: Saúde e Saúde Pública



Este projeto consiste no desenvolvimento de um pipeline ETL (Extract, Transform, Load) modular focado no domínio da Saúde \& Saúde Pública. O objetivo é extrair dados epidemiológicos da COVID-19 e enriquecê-los com indicadores globais de expectativa de vida para futuras análises de correlação e impacto.



\---



&#x09;Semana 1 - Extração

O pipeline consome dados de duas fontes principais:



1\. OWID-covid-data - Dataset da COVID-19

&#x20;  Tipo: Ficheiro CSV de grande volume.

&#x20;  Conteúdo: Dados históricos mundiais diários sobre contágios, óbitos, internamentos e taxas de vacinação por país.

&#x20;  Justificação Técnica: O volume do ficheiro justifica cuidados no carregamento e futuras otimizações de memória e processamento.



2\. World Health Organization (WHO) - GHO API (API)

&#x20;  Tipo: API Pública (`https://ghoapi.azureedge.net/api/WHOSIS\_000001`).

&#x20;  Conteúdo: Indicador oficial de Expectativa de Vida à Nascença (Life Expectancy at Birth) segregado por país e ano.

&#x20;  Justificação Técnica: Permite enriquecer o dataset com o panorama da saúde base pré-pandemia de cada nação.

