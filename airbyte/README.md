# Airbyte — Configuração PostgreSQL → BigQuery

O Airbyte usa dois conectores nativos — sem configuração customizada:

- **Source**: PostgreSQL (lê `raw.*` populado pelo `collector.py` via Airflow)
- **Destination**: BigQuery (envia os dados ao Data Warehouse)

Acesse: **http://localhost:9000**

## Pré-requisito

O container PostgreSQL deve estar rodando e as tabelas `raw.open_meteo_hourly`
e `raw.open_meteo_daily` devem conter dados antes de configurar as connections.
Ver `postgresql/README.md`.

---

## 1. Configurar o Source — PostgreSQL

### 1.1 Criar novo Source

Menu lateral → **Sources → New Source**
Busque e selecione: **PostgreSQL**

### 1.2 Preencher os campos

| Campo | Valor |
|-------|-------|
| Source name | `weather-postgres-raw` |
| Host | `host.docker.internal` (Airbyte roda em Docker via abctl) |
| Port | `5432` |
| Database | `weather_staging` |
| Optional fields (Schema) | `raw` |
| Username | `airbyte_user` |
| Password | `airbyte_pass_troque` (definido em `postgresql/init/01_schemas.sql` — altere antes de usar em produção) |
| SSL mode | `disable` (rede local) |
| Advanced / Update method | **Detect Changes with Xmin System Column** |

Selecione: **Test and save**

---

## 2. Configurar o Destination — BigQuery

### 2.1 Criar novo Destination

Menu lateral → **Destinations → New Destination**
Busque e selecione: **BigQuery**

### 2.2 Preencher os campos

| Campo | Valor |
|-------|-------|
| Destination name | `weather-bigquery` |
| Project ID | ID do seu projeto GCP (ex: `weather-analytics-490113`) |
| Dataset Location | `southamerica-east1` |
| Default Dataset ID | `weather_raw` |
| Loading Method | Batched Standard Inserts |
| Service Account Key JSON | cole o conteúdo do arquivo `gcp-service-account.json` |
| Advanced / Transformation Query Run Type | `interactive` |
| Advanced / Raw Table Dataset Name | `airbyte_raw` |

Selecione: **Test and save**

> **Erro de caractere ao colar o Service Account?**
> Execute no PowerShell para copiar o JSON limpo:
>
> ```powershell
> $content = [System.IO.File]::ReadAllText(
>   "C:\Dev\Analytics-Engineer\Weather-Analytics\postgresql\secrets\gcp-service-account.json",
>   [System.Text.Encoding]::UTF8
> ).TrimStart([char]0xFEFF)
>
> $content | Set-Clipboard
> ```
>
> No Airbyte: clique no campo → `Ctrl+A` → `Delete` → `Ctrl+V`

---

## 3. Criar a Connection — hourly

**Menu**: Connections → New Connection

### 3.1 Source → Destination

- Select an existing source → `weather-postgres-raw`
- Select an existing destination → `weather-bigquery`

### 3.2 Selecionar Schema

- Selecione → `open_meteo_hourly`
- Select sync mode → Replicate Source
- Next

### 3.3 Configurar a Connection

| Campo | Valor |
|-------|-------|
| Connection name | `postgres-raw-hourly-to-bigquery` |
| Schedule type | `Scheduled` |
| Replication frequency | `Every 6 hours` |
| Destination namespace | `Source-defined` |
| Stream prefix | *(deixar vazio)* |
| When the source schema changes | `Propagate field changes only` |

Selecione: **Finish & Sync**

---

## 4. Criar a Connection — daily

**Menu**: Connections → New Connection

### 4.1 Source → Destination

- Select an existing source → `weather-postgres-raw`
- Select an existing destination → `weather-bigquery`

### 4.2 Selecionar Schema

- Selecione → `open_meteo_daily`
- Select sync mode → Replicate Source
- Next

### 4.3 Configurar a Connection

| Campo | Valor |
|-------|-------|
| Connection name | `postgres-raw-daily-to-bigquery` |
| Schedule type | `Scheduled` |
| Replication frequency | `Every 24 hours` |
| Destination namespace | `Source-defined` |
| Stream prefix | *(deixar vazio)* |
| When the source schema changes | `Propagate field changes only` |

Selecione: **Finish & Sync**

---

## 5. Executar sync manual e verificar

Connections → selecionar a conexão → **Sync now**

Para confirmar no BigQuery, execute no console GCP:

```sql
SELECT location_id, COUNT(*) as registros, MAX(_extracted_at) as ultima_carga
FROM `weather-analytics-490113.raw.open_meteo_daily`
GROUP BY 1
ORDER BY 1;
```
