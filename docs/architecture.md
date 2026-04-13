# Arquitetura — Weather Analytics Pipeline

## Fluxo de dados

```
 ┌──────────────────────┐
 │   Open-Meteo API     │  REST JSON, gratuita, sem autenticação
 └──────────┬───────────┘
            │  HTTP GET 4x/dia (00:30, 06:30, 12:30, 18:30 BRT)
            ▼
 ┌──────────────────────────────────────────────────────┐
 │   Airflow (Docker — LocalExecutor)                   │
 │                                                      │
 │   dag_weather_collection  ──► collector.py --once    │
 │   dag_weather_transform   ──► dbt seed/run/test      │
 └──────────────────┬───────────────────────────────────┘
                    │
                    ▼
 ┌──────────────────────────────────────────────────────┐
 │   container: weather_postgres (Ubuntu 24.04 + PG 17) │
 │                                                      │
 │   collector.py        UPSERT                         │
 │   (Python)      ──────► raw.open_meteo_hourly        │
 │                          raw.open_meteo_daily         │
 └──────────────────────────┬───────────────────────────┘
                            │
                            │  dag_weather_ingest (Airflow + BigQuery SDK)
                            │  Incremental por _extracted_at | 4x/dia
                            ▼
             ┌──────────────────────────────┐
             │   BigQuery — dataset          │
             │   weather_raw                 │
             │                               │
             │   open_meteo_hourly           │
             │   open_meteo_daily            │
             └──────────────┬────────────────┘
                            │
                            │  dbt (target: prod)
                            │  Sources: weather_raw.*
                            ▼
             ┌──────────────────────────────┐
             │   BigQuery — dataset          │
             │   weather_dw                  │
             │                               │
             │   staging.*  (views)          │
             │   marts.*    (tables parti.)  │
             └──────────────┬────────────────┘
                            │
                            ▼
             ┌──────────────────────────────┐
             │   Evidence.dev               │
             │   GitHub Pages               │
             │                               │
             │   Dashboard público ao vivo  │
             └──────────────────────────────┘
```

## Dois targets do dbt

| Target | Source | Destination | Quando usar |
|--------|--------|-------------|-------------|
| `dev` | `weather_staging.raw` (PostgreSQL) | `weather_staging.dbt_dev` (PostgreSQL) | Desenvolvimento local |
| `prod` | `weather_raw` (BigQuery) | `weather_dw` (BigQuery) | Produção |

A variável `DBT_SOURCE_DATABASE` controla qual banco o dbt usa como source:
- dev: `weather_staging` (PostgreSQL)
- prod: `weather_raw` (BigQuery, populado pelo Airbyte)

## Responsabilidades por pasta

| Pasta | Responsabilidade |
|-------|-----------------|
| `airflow/` | Orquestração: 3 DAGs (coleta, ingestão PostgreSQL→BigQuery, transformação) |
| `postgresql/` | Container PG17 + app coletor + setup documentado |
| `dbt/` | Transformações staging → marts, testes, documentação |
| `evidence/` | Dashboards interativos + CI/CD via GitHub Actions |

## Estrutura de arquivos

```
Weather-Analytics/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── EPIC.md
│   ├── FEATURES.md
│   └── USER-STORIES.md
│
├── airflow/
│   ├── Dockerfile                   # Airflow 2.9.1 + dbt-bigquery pré-instalado
│   ├── docker-compose.yml           # services: webserver + scheduler + postgres
│   ├── .env.example
│   └── dags/
│       ├── dag_weather_collection.py  # coleta 4x/dia + verificação PostgreSQL
│       ├── dag_weather_ingest.py      # PostgreSQL → BigQuery incremental (4x/dia)
│       └── dag_weather_transform.py   # dbt seed → run → test (prod)
│
├── postgresql/
│   ├── Dockerfile                   # Ubuntu 24.04 + PG17 + Python
│   ├── docker-compose.yml           # services: postgres + dbt-*
│   ├── .env.example
│   ├── config/
│   │   ├── postgresql.conf.append
│   │   └── pg_hba.conf.append
│   ├── init/
│   │   ├── 01_schemas.sql           # schemas, roles, permissões
│   │   └── 02_raw_tables.sql        # tabelas raw pré-criadas
│   └── collector/
│       ├── collector.py             # busca API → upsert raw.*
│       └── README.md
│
├── dbt/
│   ├── Dockerfile
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml          # source parametrizado dev/prod
│   │   │   ├── schema.yml
│   │   │   ├── stg_weather__hourly.sql
│   │   │   └── stg_weather__daily.sql
│   │   └── marts/
│   │       ├── schema.yml
│   │       ├── mart_climate__daily_facts.sql
│   │       └── mart_climate__alerts.sql
│   ├── tests/                       # 5 testes personalizados
│   ├── macros/
│   └── seeds/
│       └── locations.csv
│
└── evidence/
    ├── pages/
    │   ├── index.md                 # Visão geral + KPIs
    │   ├── temperatura.md
    │   ├── precipitacao.md
    │   ├── alertas.md
    │   └── cidades/[location_id].md # Drill-down por localidade
    └── .github/workflows/
        └── deploy.yml               # CI/CD → GitHub Pages
```
