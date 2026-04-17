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
 │   dag_weather_ingest      ──► PostgreSQL → BigQuery  │
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
             ┌──────────────────────────────────────────┐
             │   BigQuery — dataset: weather_dw          │
             │                                          │
             │   staging.*         (views)              │
             │   intermediate.*    (views)              │
             │   marts.*           (tables particionadas)│
             │                                          │
             │   mart_climate__daily_facts              │
             │   mart_climate__hourly_facts             │
             │   mart_climate__alerts                   │
             └──────────────┬───────────────────────────┘
                            │
                            │  Evidence.dev (npm run sources)
                            │  Parquet via BigQuery SDK
                            ▼
             ┌──────────────────────────────┐
             │   Evidence.dev               │
             │   DuckDB WASM (browser)      │
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
- `dev`: `weather_staging` (PostgreSQL local)
- `prod`: `weather_raw` (BigQuery, populado pelo ingestor Airflow)

## Responsabilidades por pasta

| Pasta | Responsabilidade |
|-------|-----------------|
| `airflow/` | Orquestração: 4 DAGs (coleta, ingestão PostgreSQL→BigQuery, transformação, backfill histórico) |
| `postgresql/` | Container PG17 + app coletor + setup documentado |
| `dbt/` | Transformações staging → intermediate → marts, testes, documentação |
| `evidence/` | Dashboards interativos + CI/CD via GitHub Actions → GitHub Pages |

## Estrutura de arquivos

```
Weather-Analytics/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── EPIC.md
│   ├── FEATURES.md
│   ├── USER-STORIES.md
│   ├── dashboards.md
│   ├── dashboard_pagina01_visao_geral.md
│   ├── dashboard_pagina02_precipitacao.md
│   ├── dashboard_pagina03_temperatura.md
│   ├── dashboard_pagina04_alertas.md
│   └── dashboard_pagina05_horario.md
│
├── airflow/
│   ├── Dockerfile                     # Airflow 2.9.1 + dbt-bigquery pré-instalado
│   ├── docker-compose.yml             # services: webserver + scheduler + postgres
│   ├── .env.example
│   └── dags/
│       ├── dag_weather_collection.py  # coleta 4x/dia + verificação PostgreSQL
│       ├── dag_weather_ingest.py      # PostgreSQL → BigQuery incremental (4x/dia)
│       ├── dag_weather_transform.py   # dbt seed → run → test (prod)
│       └── dag_weather_backfill.py    # backfill histórico direto da API
│
├── postgresql/
│   ├── Dockerfile                     # Ubuntu 24.04 + PG17 + Python
│   ├── docker-compose.yml             # services: postgres + dbt-*
│   ├── .env.example
│   ├── config/
│   │   ├── postgresql.conf.append
│   │   └── pg_hba.conf.append
│   ├── init/
│   │   ├── 01_schemas.sql             # schemas, roles, permissões
│   │   └── 02_raw_tables.sql          # tabelas raw pré-criadas
│   └── collector/
│       ├── collector.py               # busca API → upsert raw.*
│       └── README.md
│
├── dbt/
│   ├── Dockerfile
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml            # source parametrizado dev/prod
│   │   │   ├── schema.yml
│   │   │   ├── stg_weather__hourly.sql
│   │   │   └── stg_weather__daily.sql
│   │   ├── intermediate/
│   │   │   └── int_weather__daily_enriched.sql  # join staging + locations seed
│   │   └── marts/
│   │       ├── schema.yml
│   │       ├── mart_climate__daily_facts.sql    # 1 linha por município × dia
│   │       ├── mart_climate__hourly_facts.sql   # 1 linha por município × hora
│   │       └── mart_climate__alerts.sql         # 1 linha por evento extremo
│   ├── tests/                         # 5 testes personalizados (singular tests)
│   ├── macros/
│   └── seeds/
│       └── locations.csv              # 295 municípios de SC
│
└── evidence/
    ├── evidence.config.yaml
    ├── sources/
    │   └── weather_dw/
    │       ├── connection.yaml        # BigQuery via gcloud-cli ADC
    │       ├── mart_climate__daily_facts.sql
    │       ├── mart_climate__hourly_facts.sql
    │       └── mart_climate__alerts.sql
    └── pages/
        ├── index.md                   # Visão geral + mapa de bolhas
        ├── temperatura.md             # Ranking, amplitude, comparativo municipal
        ├── precipitacao.md            # Acumulados, heatmap diário, distribuição
        ├── alertas.md                 # Eventos extremos por tipo e mesorregião
        ├── horario.md                 # Padrões intradiários + detalhamento diário
        └── cidades/
            └── [cidade].md            # Drill-down por location_id
```

## Lineage dbt

```
raw.open_meteo_daily  ──► stg_weather__daily ──► int_weather__daily_enriched
                                                           │
seeds.locations ───────────────────────────────────────────┤
                                                           │
                                              ┌────────────┴────────────┐
                                              │                         │
                                    mart_climate__daily_facts   mart_climate__alerts
                                    (295 mun × 12 meses)        (eventos extremos)

raw.open_meteo_hourly ──► stg_weather__hourly ──► mart_climate__hourly_facts
                                                   (295 mun × últimos 30 dias)
```

## Detalhes técnicos importantes

### Evidence.dev e DuckDB
As queries nas páginas `.md` rodam em **DuckDB WASM no browser**, não no BigQuery. Os dados chegam como arquivos Parquet gerados pelo `npm run sources` (via BigQuery SDK). O dialeto SQL é DuckDB, não BigQuery SQL.

### mesoregion vs region
- `region` = macrorregião brasileira (sempre "Sul" para todos os 295 municípios de SC)
- `mesoregion` = mesorregião de SC (Grande Florianópolis, Serra Catarinense, Vale do Itajaí, Oeste Catarinense, Norte Catarinense, Sul Catarinense)

Os dashboards filtram por `mesoregion` para análise geográfica interna de Santa Catarina.

### Parquet placeholder em mart_climate__alerts
A query source do Evidence para `mart_climate__alerts` inclui uma linha placeholder (`alert_type = '__no_alerts__'`) via `UNION ALL` para evitar arquivo Parquet vazio (0 bytes), que o DuckDB rejeita. Todas as queries nas páginas filtram `where alert_type != '__no_alerts__'`.
