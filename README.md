# Weather Analytics Pipeline

Open-Meteo API → collector.py (PostgreSQL) → Airflow → BigQuery → dbt → BigQuery DW

## Arquitetura em Camadas

| Camada | Tecnologia | O que faz |
|--------|-----------|-----------|
| Orquestração | **Airflow** (Docker) | Agenda coleta, ingestão e transformação |
| Coleta | `collector.py` (Python) | Busca API Open-Meteo → grava em `raw.*` |
| Staging | PostgreSQL 17 | Armazena dados raw |
| Ingest | `dag_weather_ingest` (Python + BigQuery SDK) | Replica `raw.*` do PostgreSQL para o BigQuery de forma incremental |
| Transform | dbt | Lê `weather_raw` (prod) ou `raw` (dev) → materializa marts |
| Warehouse | BigQuery | Dataset `weather_dw` com tabelas analíticas finais |
| Visualização | Evidence.dev | Dashboards interativos gerados a partir dos marts do dbt |

## Estrutura

```
Weather-Analytics/
├── airflow/        # Orquestração: 3 DAGs (coleta + ingestão + transformação)
├── postgresql/     # Container Ubuntu 24.04 + PostgreSQL 17 + app coletor
├── dbt/            # Transformações: staging → marts (dev: Postgres, prod: BigQuery)
├── evidence/       # Dashboards interativos gerados a partir dos marts do dbt
└── docs/           # Arquitetura e decisões
```

## Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose disponível
- ~8GB de espaço livre em disco
- Conexão com internet para download de imagens e integração com APIs
- Conta GCP com BigQuery e um Service Account com roles: `BigQuery Data Editor` + `BigQuery Job User`

---


## 🐳 PostgreSQL + Collector

Siga o guia: `postgresql/README.md`

```bash
# Subir o PostgreSQL
cd postgresql
docker compose up -d

# Verificar dados coletados
docker exec weather_postgres psql -U weather_user -d weather_staging \
  -c "SELECT location_id, COUNT(*) FROM raw.open_meteo_daily GROUP BY 1 ORDER BY 1;"
```

---

## ⚡ Airflow — Orquestração do Pipeline

O Airflow centraliza o pipeline completo em três DAGs:

| DAG | Schedule | O que faz |
|-----|----------|-----------|
| `dag_weather_collection` | 00:30, 06:30, 12:30, 18:30 BRT | Coleta Open-Meteo → PostgreSQL + verifica inserção |
| `dag_weather_ingest` | 01:00, 07:00, 13:00, 19:00 BRT | PostgreSQL → BigQuery (incremental via SDK) |
| `dag_weather_transform` | 07:30 BRT (diário) | `dbt seed → dbt run → dbt test` no BigQuery (prod) |

### 1. Pré-requisito

O `postgresql/docker-compose.yml` deve estar rodando antes de subir o Airflow, pois a rede `weather_network` é criada por ele.

```powershell
# Confirmar que a rede existe
docker network ls | Select-String weather
```

### 2. Configurar variáveis de ambiente

```bash
cd airflow
cp .env.example .env
```

Editar o `.env` e preencher:

| Variável | Onde encontrar |
|----------|----------------|
| `POSTGRES_PASSWORD` | Mesmo valor do `postgresql/.env` |
| `DBT_PROFILES_DIR` | Caminho absoluto para a pasta com `profiles.yml` (ex: `C:/Users/seu-usuario/.dbt`) |
| `GCP_PROJECT_ID` | ID do projeto no Google Cloud Console |

### 3. Subir o Airflow

```bash
cd airflow
docker compose up -d
```

Acessar: [http://localhost:8081](http://localhost:8081) — `admin` / `admin`

### 4. Verificar os containers

```bash
docker compose ps
```

Esperado: `airflow_webserver (healthy)`, `airflow_scheduler (healthy)`, `airflow_meta_postgres (healthy)`, `airflow_init (Exited 0)`.

### 5. Executar as DAGs manualmente (primeiro teste)

Via UI em [http://localhost:8081](http://localhost:8081), acionar na ordem:

1. `dag_weather_collection` → botão "Trigger DAG"
   - `collect_open_meteo` — coleta os 295 municípios de SC via API Open-Meteo e insere no PostgreSQL (`raw.open_meteo_daily` e `raw.open_meteo_hourly`)
   - `verify_rows_inserted` — verifica se há linhas com `_extracted_at` nos últimos 30 minutos

2. Após conclusão: `dag_weather_ingest` → botão "Trigger DAG"
   - `ingest_daily` — copia `raw.open_meteo_daily` do PostgreSQL para o BigQuery (incremental)
   - `ingest_hourly` — copia `raw.open_meteo_hourly` do PostgreSQL para o BigQuery (incremental)
   - `verify_ingest` — verifica se ambas as tabelas têm dados recentes no BigQuery

3. Após conclusão: `dag_weather_transform` → botão "Trigger DAG"
   - `dbt_seed` — carrega `seeds/locations.csv`
   - `dbt_run` — materializa os modelos no BigQuery (target prod)
   - `dbt_test` — valida os testes de qualidade

Via CLI (PowerShell):

```powershell
# Trigger coleta
docker exec airflow_scheduler airflow dags trigger dag_weather_collection

# Trigger ingestão
docker exec airflow_scheduler airflow dags trigger dag_weather_ingest

# Trigger transformação
docker exec airflow_scheduler airflow dags trigger dag_weather_transform
```

### 6. Monitorar logs

```bash
# Logs do scheduler
docker logs -f airflow_scheduler

# Logs de uma task específica
docker exec airflow_scheduler \
  airflow tasks logs dag_weather_collection collect_open_meteo <run_id>
```

### Parar o Airflow

```bash
cd airflow
docker compose down
```

### Estrutura das DAGs

```
dag_weather_collection (00:30 / 06:30 / 12:30 / 18:30 BRT)
  └── collect_open_meteo        BashOperator   → python3 collector.py --mode once
  └── verify_rows_inserted      PythonOperator → verifica inserção no PostgreSQL

dag_weather_ingest (01:00 / 07:00 / 13:00 / 19:00 BRT)
  ├── ingest_daily              PythonOperator → PostgreSQL raw.open_meteo_daily → BigQuery
  ├── ingest_hourly             PythonOperator → PostgreSQL raw.open_meteo_hourly → BigQuery
  └── verify_ingest             PythonOperator → verifica dados recentes no BigQuery

dag_weather_transform (07:30 BRT)
  └── dbt_seed    BashOperator → dbt seed  --target prod
  └── dbt_run     BashOperator → dbt run   --target prod   [SLA: 30 min]
  └── dbt_test    BashOperator → dbt test  --target prod
```

### Backfill de dados históricos - Buscar dados antigos

```bash
docker exec weather_postgres \
  python3 /opt/collector/collector.py --mode backfill --start 2024-01-01 --end 2024-12-31
```

---

## 🔧 Executar o dbt manualmente (desenvolvimento)

Siga o guia: `dbt/README.md`

```bash
cd postgresql

# Desenvolvimento (PostgreSQL local)
docker compose run --rm dbt-seed
docker compose run --rm dbt-build

# Produção (BigQuery)
DBT_TARGET=prod docker compose run --rm dbt-build
```

PowerShell:

```powershell
$env:DBT_TARGET="prod"; docker compose run --rm dbt-seed
$env:DBT_TARGET="prod"; $env:DBT_SOURCE_DATABASE="weather-analytics-490113"; $env:DBT_SOURCE_SCHEMA="raw"; docker compose run --rm dbt-build
```

---

## 📈 Visualizar os Dashboards (ver `evidence/README.md`)

```bash
cd evidence
```

| Página | URL | Conteúdo |
|--------|-----|----------|
| Visão Geral | `/` | KPIs do pipeline, temperatura nacional, alertas por região |
| Temperatura | `/temperatura` | Série temporal, anomalias rolling 30d, ranking de cidades |
| Precipitação | `/precipitacao` | Acumulados, classificação de chuva, anomalias por região |
| Alertas | `/alertas` | Eventos extremos, evolução diária, cidades mais afetadas |
| Cidade | `/cidades/[location_id]` | Drill-down completo por localidade |

---

## 📋 Metodologia Ágil

Este projeto foi desenvolvido seguindo práticas **Scrum** e **Behavior-Driven Development (BDD)**, combinando competências de **Analytics Engineering** e **Product Ownership**.

### Epic

**Weather Analytics Platform**
Criar pipeline analytics end-to-end para monitoramento climático em tempo real de localidades brasileiras, permitindo análise histórica e detecção de anomalias para tomada de decisão baseada em dados.

### Features Principais

#### Feature 1: Ingestão Automatizada de Dados Climáticos
**Objetivo:** Coletar dados climáticos de múltiplas localidades via API Open-Meteo
**Tecnologia:** PostgreSQL + Python + Docker
**Resultado:** 18 localidades monitoradas, atualização diária automatizada

#### Feature 2: Pipeline ELT com Data Quality
**Objetivo:** Transformar dados brutos em modelo analytics confiável
**Tecnologia:** Airflow + BigQuery SDK + dbt
**Resultado:**
- Camadas staging → intermediate → marts
- 49 testes automatizados (data quality)
- Freshness checks diários

#### Feature 3: Dashboard Interativo em Produção
**Objetivo:** Visualização de insights climáticos em tempo real
**Tecnologia:** Evidence.dev + GitHub Actions + GitHub Pages
**Resultado:** Dashboard público ao vivo com CI/CD automático

### Processo de Desenvolvimento

**Sprint Planning:**
- Definição de Features baseadas em análise de valor (impacto vs esforço)
- Decomposição em User Stories técnicas

**Development:**
- TDD approach: testes dbt escritos antes das transformações
- Code review via Git (branches + pull requests)
- Documentação inline (schema.yml completo)

**Testing:**
- 49 testes automatizados (unique, not_null, ranges, freshness)
- Validação manual do dashboard antes do deploy
- Smoke tests no CI/CD pipeline

**Deployment:**
- CI/CD automático via GitHub Actions
- Deploy incremental (não afeta dados históricos)
- Rollback automático em caso de falha nos testes
