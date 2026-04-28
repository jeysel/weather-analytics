# Weather Analytics Pipeline

Open-Meteo API → collector.py (PostgreSQL) → Airflow → BigQuery → dbt → BigQuery DW → Streamlit

## Arquitetura em Camadas

| Camada | Tecnologia | O que faz |
|--------|-----------|-----------|
| Orquestração | **Airflow** (Docker) | Agenda coleta, ingestão e transformação |
| Coleta | `collector.py` (Python) | Busca API Open-Meteo → grava em `raw.*` |
| Staging | PostgreSQL 17 | Armazena dados raw |
| Ingest | `dag_weather_ingest` (Python + BigQuery SDK) | Replica `raw.*` do PostgreSQL para o BigQuery de forma incremental |
| Transform | dbt | Lê `weather_raw` (prod) ou `raw` (dev) → materializa marts |
| Warehouse | BigQuery | Dataset `weather_dw` com tabelas analíticas finais |
| Visualização | **Streamlit** | 6 páginas analíticas + análise comparativa; deploy no Lightsail com Nginx + systemd |

## Estrutura

```
Weather-Analytics/
├── airflow/        # Orquestração: 4 DAGs (coleta + ingestão + transformação + backfill)
├── postgresql/     # Container Ubuntu 24.04 + PostgreSQL 17 + app coletor
├── dbt/            # Transformações: staging → marts (dev: Postgres, prod: BigQuery)
├── streamlit/      # Dashboard interativo em Python; deploy no Lightsail
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

### Backfill de dados históricos

A DAG `dag_weather_backfill` popula o BigQuery com dados históricos da API Open-Meteo Archive
diretamente, sem passar pelo PostgreSQL. Indicada para quem quer iniciar o projeto com volume
suficiente para dashboards com storytelling (5 anos de dados diários + 2 anos de dados horários).

**Estimativa:** ~90 min | **Storage BigQuery:** ~2 GB | Dentro do free tier (10 GB/mês)

Os períodos estão configurados diretamente no arquivo
`airflow/dags/dag_weather_backfill.py` nas constantes:

```python
DAILY_START  = "2021-01-01"   # 5 anos de dados diários
DAILY_END    = _YESTERDAY     # até ontem (calculado automaticamente)
HOURLY_START = "2024-01-01"   # 2 anos de dados horários
HOURLY_END   = _YESTERDAY
```

Ajuste antes de disparar, se necessário.

#### Passo 1 — Limpar dados existentes

```bash
# PostgreSQL (requer superusuário)
docker exec -it weather_postgres psql -U postgres -d weather_staging -c "TRUNCATE raw.open_meteo_daily CASCADE;"
docker exec -it weather_postgres psql -U postgres -d weather_staging -c "TRUNCATE raw.open_meteo_hourly CASCADE;"
```

No **BigQuery Console → Query editor**:

```sql
TRUNCATE TABLE `seu-projeto.weather_raw.open_meteo_daily`;
TRUNCATE TABLE `seu-projeto.weather_raw.open_meteo_hourly`;
```

> Substitua `seu-projeto` pelo seu `GCP_PROJECT_ID`.

#### Passo 2 — Despausar a DAG

```bash
docker exec -it airflow_scheduler airflow dags unpause dag_weather_backfill
```

Se o comando não persistir, acesse a Airflow UI em [http://localhost:8081](http://localhost:8081),
encontre a DAG `dag_weather_backfill` na lista e ative o toggle ao lado do nome.

#### Passo 3 — Disparar o backfill

```bash
docker exec -it airflow_scheduler airflow dags trigger dag_weather_backfill
```

#### Sequência de execução

```
prepare_bigquery  (~5s)    → cria tabelas e trunca weather_raw no BigQuery
backfill_daily    (~15min) → 295 cidades × 5 anos ≈ 540k linhas
backfill_hourly   (~20min) → 295 cidades × 2 anos ≈ 12,9M linhas
trigger_transform (~5min)  → dbt seed → run → test (reconstrói todos os marts)
```

> **Nota:** a DAG faz 1,5 requisições por segundo à API Open-Meteo com retry automático
> e backoff exponencial em caso de rate limit (HTTP 429). Não interrompa a execução durante o backfill.

#### Verificar dados inseridos no BigQuery

Após a execução, confirme no **BigQuery Console → Query editor** (substitua `seu-projeto` pelo `GCP_PROJECT_ID`):

```sql
-- Total de linhas inseridas
SELECT COUNT(*) FROM `seu-projeto.weather_raw.open_meteo_daily`;
SELECT COUNT(*) FROM `seu-projeto.weather_raw.open_meteo_hourly`;

-- Municípios distintos coletados (esperado: 295)
SELECT COUNT(DISTINCT location_id) AS municipios_coletados
FROM `seu-projeto.weather_raw.open_meteo_daily`;

-- Linhas por município (útil para identificar quem falhou)
SELECT location_id, COUNT(*) AS total
FROM `seu-projeto.weather_raw.open_meteo_daily`
GROUP BY location_id
ORDER BY location_id;
```

#### Passo 4 (opcional) — Re-executar para municípios que falharam

Se a execução terminar com erros em alguns municípios (visível no log da task como `✗ nome_cidade`),
edite as constantes no arquivo `airflow/dags/dag_weather_backfill.py` antes de disparar novamente:

```python
# Re-execução após falhas — coleta apenas municípios que falharam
TRUNCATE_EXISTING = False   # mantém dados já coletados
SKIP_EXISTING     = True    # pula quem já tem dados no BigQuery
```

> **Atenção:** a configuração padrão no arquivo é `TRUNCATE_EXISTING = True` / `SKIP_EXISTING = False`
> (primeira execução). Altere antes de disparar a re-execução.

Depois dispare normalmente:

```bash
docker exec -it airflow_scheduler airflow dags trigger dag_weather_backfill
```

A DAG vai consultar o BigQuery, identificar quais municípios já têm dados e pular esses automaticamente,
coletando apenas os que estão faltando. Ao final, restaure os valores originais para a próxima vez:

```python
TRUNCATE_EXISTING = True
SKIP_EXISTING     = False
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

## 🎯 Streamlit — Dashboard em Produção

Dashboard interativo construído em Python, conectado diretamente ao BigQuery via `google-cloud-bigquery`.
Deploy no AWS Lightsail com Nginx como proxy reverso e systemd gerenciando o processo.

### Estrutura

```
streamlit/
├── app.py                        ← Home: KPIs + linha de temperatura + mapa SC
├── pages/
│   ├── 1_Temperatura.py          ← Rankings hot/cold, tendência mesorregião, heatmap anomalia
│   ├── 2_Precipitacao.py         ← Top 20 acumulado, pizza de classes, heatmap diário
│   ├── 3_Alertas.py              ← KPIs severidade, barras por tipo, tabela filtrável
│   ├── 4_Horario.py              ← Temp+umidade, vento+chuva, perfil médio 24h
│   └── 5_Cidades.py              ← Perfil completo por município (temp/precip/vento/alertas)
├── utils/
│   └── bigquery.py               ← Client singleton (@cache_resource) + query (@cache_data 1h)
├── .streamlit/config.toml        ← Tema dark + server escutando só 127.0.0.1:8501
├── requirements.txt
├── .env.example
└── deploy/
    ├── nginx-weather.conf        ← Proxy com WebSocket headers (obrigatório pro Streamlit)
    └── weather-streamlit.service ← systemd com EnvironmentFile e restart automático
```

### Executar localmente (Windows)

#### 1. Criar o ambiente virtual

```powershell
cd streamlit
python.exe -m pip install --upgrade pip
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configurar credenciais

```powershell
copy .env.example .env
```

Editar o `.env` com os valores locais:

```env
GCP_PROJECT_ID=seu-projeto-gcp
BIGQUERY_DATASET=marts
BIGQUERY_SEEDS_DATASET=seeds
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/seu-usuario/secrets/gcp-service-account.json
```

> O arquivo `gcp-service-account.json` é o mesmo já usado no Airflow (`postgresql/secrets/`).
> Use barras `/` ou `\\` no caminho — barra invertida simples `\` causa erro no Python.

#### 3. Sobrescrever o endereço para desenvolvimento

O `config.toml` padrão escuta apenas `127.0.0.1` com `headless = true` (modo servidor).
Para rodar localmente sem precisar alterar o arquivo commitado, passe os overrides via CLI:

```powershell
streamlit run app.py --server.address localhost --server.headless false
```

O Streamlit abrirá automaticamente [http://localhost:8501](http://localhost:8501) no browser.

#### 4. Testar cada página

| Página | O que validar |
|--------|--------------|
| Home (`app.py`) | KPIs carregam, mapa SC renderiza com pontos |
| Temperatura | Rankings hot/cold preenchidos, heatmap de anomalia sem erros |
| Precipitação | Top 20 acumulado, pizza de classes sem fatias zeradas |
| Alertas | Tabela filtrável responde aos selects de severidade/tipo |
| Horário | Gráficos de temp+umidade e perfil 24h carregam para qualquer município |
| Cidades | Dropdown de município funciona e exibe todos os painéis |

#### 5. Verificar o cache

O cache de queries tem TTL de 1h. Para forçar recarga durante testes:

```powershell
# Na UI do Streamlit: menu ⋮ (canto superior direito) → "Clear cache"
# Ou reinicie o processo:
# Ctrl+C no terminal → streamlit run app.py ...
```

---

### Deploy no Lightsail — passo a passo

#### 1. Preparar o servidor

```bash
# Instalar Python venv e criar ambiente isolado
sudo apt install python3-venv python3-pip -y
python3 -m venv ~/venv/weather
source ~/venv/weather/bin/activate

# Clonar/atualizar o repositório
cd ~/Analytics-Engineer/Weather-Analytics/streamlit
pip install -r requirements.txt
```

#### 2. Configurar credenciais

```bash
# Copiar a service account do GCP para o servidor
mkdir -p ~/secrets
# scp da sua máquina local:
# scp postgresql/secrets/gcp-service-account.json ubuntu@<ip>:~/secrets/

# Criar o .env a partir do exemplo
cp .env.example .env
nano .env   # preencher GCP_PROJECT_ID e ajustar BIGQUERY_DATASET
```

> **Atenção nos datasets BigQuery:** o Evidence usa `dataset=marts` — provavelmente `BIGQUERY_DATASET=marts`.
> Verifique no console GCP quais datasets existem no projeto.

#### 3. Nginx

```bash
sudo cp deploy/nginx-weather.conf /etc/nginx/sites-available/weather.jeysel.dev
sudo ln -s /etc/nginx/sites-available/weather.jeysel.dev /etc/nginx/sites-enabled/

# Obter certificado SSL para o novo subdomínio
sudo certbot certonly --nginx -d weather.jeysel.dev

sudo nginx -t && sudo systemctl reload nginx
```

#### 4. systemd

```bash
# Ajustar o caminho do venv no .service se necessário
sudo cp deploy/weather-streamlit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weather-streamlit
sudo systemctl start weather-streamlit

# Verificar logs
sudo journalctl -u weather-streamlit -f
```

### Decisões de arquitetura

| Decisão | Motivo |
|---------|--------|
| `@st.cache_data(ttl=3600)` em todas as queries | Evita hits desnecessários no BigQuery; 1h é adequado dado o pipeline diário |
| `@st.cache_resource` no client BigQuery | Singleton por processo — não re-autentica a cada página |
| Streamlit escuta só `127.0.0.1` | Nginx faz o proxy; app não fica exposta diretamente |
| `QUALIFY ROW_NUMBER()` no mapa | Filtra último dia por município sem subquery extra, aproveitando o partition pruning do BigQuery |
| `clip(lower=1)` nos scatter mapbox | Plotly mapbox falha silenciosamente com tamanho zero |

---

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
**Resultado:** 295 municípios de SC monitorados, atualização automática 4×/dia

#### Feature 2: Pipeline ELT com Data Quality
**Objetivo:** Transformar dados brutos em modelo analytics confiável  
**Tecnologia:** Airflow + BigQuery SDK + dbt  
**Resultado:**
- Camadas staging → intermediate → marts
- 49 testes automatizados (data quality)
- Freshness checks diários

#### Feature 3: Dashboard Interativo em Produção
**Objetivo:** Visualização de insights climáticos em tempo real com interatividade  
**Tecnologia:** Streamlit + BigQuery + Nginx + systemd (AWS Lightsail)  
**Resultado:** 6 páginas analíticas (Home, Temperatura, Precipitação, Alertas, Horário, Cidades) + página de Análise Comparativa, servidas com SSL via subdomínio dedicado

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
- CI/CD automático via GitHub Actions (Evidence → GitHub Pages)
- Streamlit gerenciado via systemd com restart automático
- Deploy incremental (não afeta dados históricos)
- Rollback automático em caso de falha nos testes dbt
