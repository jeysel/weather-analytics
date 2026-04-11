## Pré-requisito
---
O container PostgreSQL deve estar rodando e as tabelas `raw.open_meteo_hourly`
e `raw.open_meteo_daily` devem conter dados antes de configurar as connections.
Ver `postgresql/README.md` — passos 1 a 10.

---

# Airbyte — Configuração PostgreSQL → BigQuery
O Airbyte usa dois conectores nativos — sem configuração customizada:

- **Source**: PostgreSQL (lê `raw.*` populado pelo `collector.py`)
- **Destination**: BigQuery (envia os dados ao Data Warehouse)

Acesse: **http://localhost:9000**



## 1. Configurar o Source — PostgreSQL

### 1.1 Criar novo Source

Menu lateral → **Sources → New Source**
Busque e selecione: **PostgreSQL**

### 1.2 Preencher os campos

* Source name -> `weather-postgres-raw` 
* Host -> `host.docker.internal` (Airbyte roda em Docker via abctl) 
* Port -> `5432` 
* Database -> `weather_staging` 
* Optional fields -> `raw` 
* Username -> `airbyte_user` 
* Password -> `airbyte_pass_troque` -> Definido em: `postgresql/init/01_schemas.sql` — variável `airbyte_pass_troque` (altere antes de usar em produção) 
* SSL mode -> `disable` (rede local) 
* Advanced/Update method -> Selecione: **Detect Changes with Xmin System Column**
* Selecione: Test and save —> o Airbyte testa a conexão automaticamente ao salvar.

## 2. Configurar o Destination — BigQuery

### 2.1 Criar novo Destination

Menu lateral → **Destinations → New Destination**
Busque e selecione: **BigQuery**

### 2.2 Preencher os campos

* Destination name -> `weather-bigquery` 
* Project ID -> ID do seu projeto GCP (ex: `weather-analytics-490113`) 
* Dataset Location -> `southamerica-east1` 
* Default Dataset ID -> `weather_raw` 
* Loading Method -> Batched Standard Inserts
* Service Account Key JSON -> cole o conteúdo do arquivo `gcp-service-account.json` 
## -------------------------------------------------------------------------------------------
* Caso ocorra erro de caractere ao informar o service account, siga os passos:
* 1.1- No PowerShell ->
$content = [System.IO.File]::ReadAllText(
  "C:\Dev\Analytics-Engineer\Weather-Analytics\postgresql\secrets\gcp-service-account.json",
  [System.Text.Encoding]::UTF8
).TrimStart([char]0xFEFF)

$content | Set-Clipboard

* 1.2- No Airbyte ->

Clique no campo Service Account Key JSON
Ctrl+A para selecionar tudo
Delete para limpar
Ctrl+V para colar o conteúdo limpo
## ----------------------------------------------------------------------------------------------

* Advanced/Transformation Query Run Type -> interactive
* Advanced/Raw Table Dataset Name -> airbyte_raw
* Selecione: Test and save —> o Airbyte testa a conexão automaticamente ao salvar.


## 3. Criar a Connection hourly

**Menu**: Connections → New Connection

### 3.1 Source → Destination

* Select an existing source -> Selecione: `weather-postgres-raw` 
* Select an existing destination -> Selecione:  `weather-bigquery`


### 3.2 Selecionar Schema

* Selecione -> `open_meteo_hourly`
* Select sync mode ->  Replicat Source
* Next


### 3.3 Configure a connection

* Connection name -> `postgres-raw-hourly-to-bigquery` 
* Schedule type -> `Scheduled` 
* Replication frequency -> `Every 6 hours` 
* Destination namespace -> `Source-defined` 
* Stream prefix -> *(deixar vazio)* 
* Advanced settings/When the source schema changes, I want to: -> `Propagate field changes only` 
* Finish & Sync

## 4. Criar a Connection daily

**Menu**: Connections → New Connection

### 4.1 Source → Destination

* Select an existing source -> Selecione: `weather-postgres-raw` 
* Select an existing destination -> Selecione:  `weather-bigquery`

### 4.2 Selecionar Schema

* Selecione -> `open_meteo_daily`
* Select sync mode ->  Replicat Source
* Next

### 4.3 Configure a connection

* Connection name -> `postgres-raw-daily-to-bigquery` 
* Schedule type -> `Scheduled` 
* Replication frequency -> `Every 24 hours` 
* Destination namespace -> `Source-defined` 
* Stream prefix -> *(deixar vazio)* 
* Advanced settings/When the source schema changes, I want to: -> `Propagate field changes only` 
* Finish & Sync

## 5. Executar sync manual e verificar

* Connections
* Selecionar a conexão -> Sync now

Para confirmar no BigQuery, execute no console GCP:

```sql
SELECT location_id, COUNT(*) as registros, MAX(_extracted_at) as ultima_carga
FROM `weather-analytics-490113.raw.open_meteo_daily`
GROUP BY 1
ORDER BY 1;
```

