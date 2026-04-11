# Projeto: Weather Analytics Pipeline
# Open-Meteo API → collector.py (PostgreSQL) → Airbyte → BigQuery → dbt → BigQuery DW

## Estrutura

```
Weather-Analytics/
├── airflow/        # Orquestração: 2 DAGs (coleta 4x/dia + dbt diário)
├── postgresql/     # Container Ubuntu 24.04 + PostgreSQL 17 + app coletor
├── airbyte/        # Guia de configuração: Source PostgreSQL → Destination BigQuery
├── dbt/            # Transformações: staging → marts (dev: Postgres, prod: BigQuery)
├── evidence/       # Dashboards interativos gerados a partir dos marts do dbt
└── docs/           # Arquitetura e decisões
```

## Weather Analytics Pipeline - Arquitetura em camadas

| Camada | Tecnologia | O que faz |
|--------|-----------|-----------|
| Orquestração | **Airflow** (Docker) | Agenda coleta 4x/dia e dispara dbt diariamente |
| Coleta | `collector.py` (Python) | Busca API Open-Meteo → grava em `raw.*` |
| Staging | PostgreSQL 17 | Armazena dados raw e serve como Source para o Airbyte |
| Ingest | Airbyte (conector nativo PostgreSQL → BigQuery) | Replica `raw.*` para BigQuery `weather_raw` |
| Transform | dbt | Lê `weather_raw` (prod) ou `raw` (dev) → materializa marts |
| Warehouse | BigQuery | Dataset `weather_dw` com tabelas analíticas finais |
| Visualização | Evidence.dev | Dashboards interativos gerados a partir dos marts do dbt |

## Pré-requisitos

- Docker + Docker Compose
- Airbyte já instalado e rodando em `http://localhost:9000`
- Conta GCP com BigQuery e um Service Account com roles:
  `BigQuery Data Editor` + `BigQuery Job User`
---

## 🚀 Configuração Inicial

### Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose disponível
- ~8GB de espaço livre em disco
- Conexão com internet para download de imagens e integração com APIs

---

## 🐳 Configurar Container Docker para executar Airbyte localmente (Maquina com Windows 11)

* Acessar o link: https://docs.airbyte.com/using-airbyte/getting-started/oss-quickstart?_gl=1*1uywmn1*_gcl_au*MTU0OTM4MDYyMi4xNzMyNzk5MTYx

* Executar os passos em ordem:

# Opção A — Airbyte 1.7.1 (recomendado, estável, pós-fix)
abctl local install --chart-version 2.0.7 --port 9000

# Opção B — Airbyte 1.8.5 (mais recente ainda seguro)
abctl local install --chart-version 2.0.17 --port 9000

```
1- "Overview" -> Install ABCTL
2- Overview/Install abctl Passsos do sistema operacional (Aba Windows)
3- Download ABCTL, opção: "Download windows"
4- Extrair o conteúdo em c:\airbyte (Sugestão)
5- Acessar: Environment Variables
6- System variables 
7- Path (Edit)
8- New (Colar o caminho da pasta dos arquivos extraidos, passo 4) - Selecionar OK
9- No PowerShell digitar: abctl version  (Tem que retornar a versão)
10- No PowerShell executar: abctl local install --port 9000 --chart-version 1.2.0 --values "$env:USERPROFILE\airbyte-values.yaml" (Versão https://github.com/airbytehq/abctl/releases/tag/v0.29.0 estavel. Docker deve estar em execução)
OBS: Antes execute este comando:
@"
pod-sweeper:
  enabled: false
"@ | Out-File -FilePath "$env:USERPROFILE\airbyte-values.yaml" -Encoding utf8
11- No PowerShell, será exibido o link: http://localhost:9000/setup  
12- No Browser, Informar um endereço de email, organização e selecionar "Get started"
13- No PowerShell, executar: abctl local credentials
14- Será gerado uma senha, copiar a senha gerada, exemplo: zJomffmttWEF5FL0afTGAs59wQdangpu
15- Acessar o endereço: http://localhost:9000/ e informar o email e a senha gerada
16- Para desinstalar o airbyte local, Abra PowerShell de digite: abctl local uninstall --persisted 

```

## ⚡ Airflow — Orquestração do Pipeline

O Airflow substitui o container `collector` em modo agendado e o `dbt build` manual, centralizando o pipeline em duas DAGs:

| DAG | Schedule | O que faz |
|-----|----------|-----------|
| `dag_weather_collection` | 00:30, 06:30, 12:30, 18:30 BRT | Coleta Open-Meteo → PostgreSQL + verifica inserção |
| `dag_weather_transform` | 07:30 BRT (diário) | `dbt seed → dbt run → dbt test` no BigQuery (prod) |

### Pré-requisito

O `postgresql/docker-compose.yml` deve estar rodando antes de subir o Airflow, pois a rede `weather_network` é criada por ele.

```powershell
# Confirmar que a rede existe (PowerShell)
docker network ls | Select-String weather

# Bash/WSL
# docker network ls | grep weather
```

### 1. Configurar variáveis de ambiente

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

### 5. Executar as DAGs manualmente (primeiro teste)

Via UI em [http://localhost:8081]
Acionar as DAGs na ordem:

1. `dag_weather_collection` -> botão "Trigger DAG" 
- O airflow vai executar na sequencia:
collect_open_meteo, que rodou python3 /opt/collector/collector.py --mode once, para coletar os dados das 18 localidades via API Open-Meteo 
- Inseriu no PostgreSQL (raw.open_meteo_daily e raw.open_meteo_hourly)
- verify_rows_inserted — conectou no PostgreSQL e verificou se havia linhas com _extracted_at nos últimos 30 minutos em ambas as tabelas


2. Após conclusão: `dag_weather_transform` -> botão "Trigger DAG" 
- O airflow vai executar na sequencia:
- dbt_seed — carrega seeds/locations.csv
- dbt_run — materializa os modelos no BigQuery (target prod)
- dbt_test — valida os 49 testes de qualidade

PowerShell:
```bash
# Trigger coleta
docker exec airflow_scheduler airflow dags trigger dag_weather_collection

# Trigger transformação
docker exec airflow_scheduler airflow dags trigger dag_weather_transform
```

### 6. Monitorar logs

```bash
# Logs do scheduler (mostra execuções agendadas)
docker logs -f airflow_scheduler

# Logs de uma task específica via CLI
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

dag_weather_transform (07:30 BRT)
  └── dbt_seed    BashOperator → dbt seed  --target prod
  └── dbt_run     BashOperator → dbt run   --target prod   [SLA: 30 min]
  └── dbt_test    BashOperator → dbt test  --target prod
```

### históricos de dados 

```bash
docker exec weather_postgres \
  python3 /opt/collector/collector.py --mode backfill --start 2024-01-01 --end 2024-12-31
```

---

## 🐳 Configurar Container Docker para executar: PostgreSQL, integração com API Open-Meteo e DBT


* Subir e configurar seguindo os passos disponíveis em: postgresql/README.md

* Primeira coleta | Pré requisito: Configuração concluída conforme: postgresql/README.md

```
docker exec weather_postgres python3 /opt/collector/collector.py --mode once
```

* Verificar dados

```
docker exec weather_postgres psql -U weather_user -d weather_staging -c  "SELECT location_id, COUNT(*) FROM raw.open_meteo_daily GROUP BY 1 ORDER BY 1;"
```

* Coletor agendado

```
docker compose --profile collector up -d collector
docker logs -f weather_collector


Roda automaticamente às 00:30, 06:30, 12:30 e 18:30 (horário de Brasília).
```

##  Configurar o e Executar o dbt

* Siga o guia: Weather-Analytics\dbt\README.md
cd ../dbt
docker compose run --rm dbt-seed
docker compose run --rm dbt-build                  # dev (PostgreSQL)
DBT_TARGET=prod docker compose run --rm dbt-build  # prod (BigQuery)


## Configurar o Airbyte (ver airbyte/README.md)

* Acessar http://localhost:9000 e 
* Siguir o guia: Weather-Analytics\airbyte\README.md

## Rodar o DBT em prod (BigQuery) - PowerShell

* cd \Weather-Analytics\postgresql
* $env:DBT_TARGET="prod"; docker compose run --rm dbt-seed
* $env:DBT_TARGET="prod"; $env:DBT_SOURCE_DATABASE="weather-analytics-490113"; $env:DBT_SOURCE_SCHEMA="raw"; docker compose run --rm dbt-build

* O que foi criado:
  - weather-analytics-490113.weather_dw_marts.mart_climate__daily_facts — 144 linhas
  - weather-analytics-490113.weather_dw_marts.mart_climate__alerts — 0 linhas (nenhum evento extremo nos dados atuais)


## Visualizar os dashboards (ver evidence/README.md)

```
cd \Weather-Analytics\evidence

```

* Páginas disponíveis

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

### 🎯 Epic

**Weather Analytics Platform**  
Criar pipeline analytics end-to-end para monitoramento climático em tempo real de localidades brasileiras, permitindo análise histórica e detecção de anomalias para tomada de decisão baseada em dados.

### 🚀 Features Principais

#### Feature 1: Ingestão Automatizada de Dados Climáticos
**Objetivo:** Coletar dados climáticos de múltiplas localidades via API Open-Meteo  
**Tecnologia:** PostgreSQL + Python + Docker  
**Resultado:** 18 localidades monitoradas, atualização diária automatizada

#### Feature 2: Pipeline ELT com Data Quality
**Objetivo:** Transformar dados brutos em modelo analytics confiável  
**Tecnologia:** Airbyte + BigQuery + dbt  
**Resultado:** 
- Camadas staging → intermediate → marts
- 49 testes automatizados (data quality)
- Freshness checks diários

#### Feature 3: Dashboard Interativo em Produção
**Objetivo:** Visualização insights climáticos em tempo real  
**Tecnologia:** Evidence.dev + GitHub Actions + GitHub Pages  
**Resultado:** Dashboard público ao vivo com CI/CD automático

### 🔄 Processo de Desenvolvimento

**Sprint Planning:**
- Definição Features baseadas em análise valor (impacto vs esforço)
- Decomposição em User Stories técnicas

**Development:**
- TDD approach: testes dbt escritos ANTES das transformações
- Code review via Git (branches + pull requests)
- Documentação inline (schema.yml completo)

**Testing:**
- 49 testes automatizados (unique, not_null, ranges, freshness)
- Validação manual dashboard antes deploy
- Smoke tests CI/CD pipeline

**Deployment:**
- CI/CD automático via GitHub Actions
- Deploy incremental (não afeta dados históricos)
- Rollback automático em caso falha testes
---






