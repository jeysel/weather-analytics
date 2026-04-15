"""
DAG: dag_weather_backfill
═════════════════════════════════════════════════════════════════════════════
Execução : APENAS MANUAL (schedule=None — nunca roda automaticamente)
Objetivo : Preencher o BigQuery com dados históricos da API Open-Meteo Archive
           para que o projeto tenha volume suficiente para dashboards com
           storytelling no Looker Studio.

Fluxo
─────
  prepare_bigquery ──┬── backfill_daily ──┐
                     │                    ├── trigger_transform
                     └── backfill_hourly ─┘

Decisões de design
──────────────────
• Grava DIRETAMENTE no BigQuery (weather_raw), sem passar pelo PostgreSQL.
  O dag_weather_ingest é incremental e carregaria 12 M+ linhas na memória de
  uma vez — o backfill contorna isso enviando em lotes de BQ_BATCH_SIZE linhas.

• A task prepare_bigquery pode TRUNCAR as tabelas raw antes de inserir
  (parâmetro truncate_existing=true). Use-a ao limpar dados antigos.

• Após o backfill, trigger_transform dispara o dag_weather_transform (dbt)
  para reconstruir staging → intermediate → marts com os dados históricos.

Parâmetros (configuráveis no formulário "Trigger DAG w/ config")
────────────────────────────────────────────────────────────────
  daily_start       : Data inicial dos dados diários   (padrão: 5 anos atrás)
  daily_end         : Data final dos dados diários     (padrão: ontem)
  hourly_start      : Data inicial dos dados horários  (padrão: 2 anos atrás)
  hourly_end        : Data final dos dados horários    (padrão: ontem)
  include_hourly    : Incluir dados horários?           (padrão: true)
  truncate_existing : Limpar tabelas raw antes?         (padrão: true)

Estimativa de tempo (295 municípios, conexão normal)
─────────────────────────────────────────────────────
  Diário 5 anos : ~10–20 min (295 chamadas API + ~540 k linhas no BQ)
  Horário 2 anos: ~30–60 min (295 chamadas API + ~12,9 M linhas no BQ)
"""

import csv
import logging
import os
import random
import time
from datetime import date, datetime, timedelta, timezone

import requests
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from google.cloud import bigquery
from google.oauth2 import service_account

log = logging.getLogger(__name__)

# ── Configuração ──────────────────────────────────────────────────────────────

ARCHIVE_API   = "https://archive-api.open-meteo.com/v1/archive"
API_TIMEOUT   = 60          # archive pode ser mais lento que a forecast API
API_SLEEP      = 30.0       # segundos entre cada requisição (evita HTTP 429)
API_RETRY_MAX  = 3          # tentativas em caso de 429 ou timeout
API_RETRY_WAIT = 15         # segundos de espera inicial ao receber 429
BQ_BATCH_SIZE = 50_000      # linhas por job load_table_from_json

GCP_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
BQ_DATASET  = "weather_raw"
BQ_LOCATION = os.environ.get("BIGQUERY_LOCATION", "southamerica-east1")
GCP_KEYFILE = "/secrets/gcp.json"

HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,precipitation,"
    "wind_speed_10m,wind_direction_10m,surface_pressure,"
    "cloud_cover,visibility,weather_code"
)
DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "rain_sum,wind_speed_10m_max,sunrise,sunset,uv_index_max"
)

_YESTERDAY   = (date.today() - timedelta(days=1)).isoformat()

# ── Períodos do backfill histórico ────────────────────────────────────────────
# Ajuste aqui antes de disparar a DAG, se necessário.
DAILY_START  = "2021-01-01"   # 5 anos de dados diários
DAILY_END    = _YESTERDAY
HOURLY_START = "2024-01-01"   # 2 anos de dados horários
HOURLY_END   = _YESTERDAY

# ── Comportamento do backfill ─────────────────────────────────────────────────
# Altere estas duas variáveis conforme a situação antes de disparar a DAG:
#
#   Primeira execução (limpa tudo e recoleta):
#     TRUNCATE_EXISTING = True
#     SKIP_EXISTING     = False
#
#   Re-execução após falhas (coleta apenas municípios que falharam):
#     TRUNCATE_EXISTING = False
#     SKIP_EXISTING     = True
#
TRUNCATE_EXISTING = False    # True: apaga dados existentes | False: faz append
SKIP_EXISTING     = True   # True: pula municípios já no BQ | False: recoleta todos
INCLUDE_HOURLY    = True    # False: ignora dados horários (execução mais rápida)

# ── Schemas BigQuery ──────────────────────────────────────────────────────────

BQ_SCHEMA_DAILY = [
    bigquery.SchemaField("location_id",         "STRING"),
    bigquery.SchemaField("date",                "DATE"),
    bigquery.SchemaField("latitude",            "FLOAT64"),
    bigquery.SchemaField("longitude",           "FLOAT64"),
    bigquery.SchemaField("temperature_2m_max",  "FLOAT64"),
    bigquery.SchemaField("temperature_2m_min",  "FLOAT64"),
    bigquery.SchemaField("precipitation_sum",   "FLOAT64"),
    bigquery.SchemaField("rain_sum",            "FLOAT64"),
    bigquery.SchemaField("wind_speed_10m_max",  "FLOAT64"),
    bigquery.SchemaField("sunrise",             "TIMESTAMP"),
    bigquery.SchemaField("sunset",              "TIMESTAMP"),
    bigquery.SchemaField("uv_index_max",        "FLOAT64"),
    bigquery.SchemaField("_extracted_at",       "TIMESTAMP"),
]

BQ_SCHEMA_HOURLY = [
    bigquery.SchemaField("location_id",           "STRING"),
    bigquery.SchemaField("timestamp",             "TIMESTAMP"),
    bigquery.SchemaField("latitude",              "FLOAT64"),
    bigquery.SchemaField("longitude",             "FLOAT64"),
    bigquery.SchemaField("elevation",             "FLOAT64"),
    bigquery.SchemaField("timezone",              "STRING"),
    bigquery.SchemaField("temperature_2m",        "FLOAT64"),
    bigquery.SchemaField("relative_humidity_2m",  "INT64"),
    bigquery.SchemaField("precipitation",         "FLOAT64"),
    bigquery.SchemaField("wind_speed_10m",        "FLOAT64"),
    bigquery.SchemaField("wind_direction_10m",    "INT64"),
    bigquery.SchemaField("surface_pressure",      "FLOAT64"),
    bigquery.SchemaField("cloud_cover",           "INT64"),
    bigquery.SchemaField("visibility",            "FLOAT64"),
    bigquery.SchemaField("weather_code",          "INT64"),
    bigquery.SchemaField("_extracted_at",         "TIMESTAMP"),
]

# ── Funções utilitárias ───────────────────────────────────────────────────────

def _get_bq_client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_file(GCP_KEYFILE)
    return bigquery.Client(project=GCP_PROJECT, credentials=creds)


def _load_locations() -> list[dict]:
    """Carrega municípios do locations.csv (mesmo seed do dbt)."""
    candidates = [
        "/opt/dbt/seeds/locations.csv",
        os.path.normpath(
            os.path.join(os.path.dirname(__file__), "../../dbt/seeds/locations.csv")
        ),
    ]
    env_path = os.environ.get("LOCATIONS_CSV")
    if env_path:
        candidates.insert(0, env_path)

    for path in candidates:
        if os.path.exists(path):
            locs = []
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    locs.append({
                        "id":  row["location_id"],
                        "lat": float(row["latitude"]),
                        "lon": float(row["longitude"]),
                    })
            log.info("Localidades carregadas: %d municípios de %s", len(locs), path)
            return locs

    raise FileNotFoundError(
        "locations.csv não encontrado. Verifique o volume /opt/dbt/seeds/ "
        "ou defina a variável de ambiente LOCATIONS_CSV."
    )


def _fetch_archive(loc: dict, start_date: str, end_date: str, *, hourly: bool) -> dict:
    """
    Chama a API Open-Meteo Archive para uma localização.
    Retry automático com backoff exponencial em caso de HTTP 429 ou timeout.
    """
    params = {
        "latitude":   loc["lat"],
        "longitude":  loc["lon"],
        "timezone":   "America/Sao_Paulo",
        "start_date": start_date,
        "end_date":   end_date,
    }
    params["hourly" if hourly else "daily"] = HOURLY_VARS if hourly else DAILY_VARS

    wait = API_RETRY_WAIT
    for attempt in range(1, API_RETRY_MAX + 1):
        try:
            resp = requests.get(ARCHIVE_API, params=params, timeout=API_TIMEOUT)
            if resp.status_code == 429:
                log.warning(
                    "  HTTP 429 em %s (tentativa %d/%d) — aguardando %ds",
                    loc["id"], attempt, API_RETRY_MAX, wait,
                )
                time.sleep(wait)
                wait *= 2  # backoff exponencial
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.Timeout:
            log.warning(
                "  Timeout em %s (tentativa %d/%d) — aguardando %ds",
                loc["id"], attempt, API_RETRY_MAX, wait,
            )
            time.sleep(wait)
            wait *= 2

    raise RuntimeError(f"Falha após {API_RETRY_MAX} tentativas para {loc['id']}")


def _get_existing_locations(client: bigquery.Client, table_name: str, start_date: str, *, hourly: bool = False) -> set:
    """
    Retorna location_ids que já têm dados históricos no BQ cobrindo o início do período.
    Verifica a presença de registros nos primeiros 7 dias do backfill para distinguir
    dados históricos dos dados recentes inseridos pelo dag_weather_ingest.
    """
    table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{table_name}"
    if hourly:
        where = (
            f"timestamp >= TIMESTAMP('{start_date}') "
            f"AND timestamp < TIMESTAMP(DATE_ADD(DATE '{start_date}', INTERVAL 7 DAY))"
        )
    else:
        where = (
            f"date >= DATE '{start_date}' "
            f"AND date < DATE_ADD(DATE '{start_date}', INTERVAL 7 DAY)"
        )
    try:
        rows = client.query(
            f"SELECT DISTINCT location_id FROM `{table_id}` WHERE {where}"
        ).result()
        return {row.location_id for row in rows}
    except Exception:
        return set()


def _bq_flush(client: bigquery.Client, table_id: str, schema: list, rows: list):
    """Envia um lote de linhas para o BigQuery via load_table_from_json."""
    if not rows:
        return
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()  # bloqueia até concluir


# ── Tasks ─────────────────────────────────────────────────────────────────────

def prepare_bigquery(**context):
    """
    Cria o dataset e as tabelas raw no BigQuery.
    Se truncate_existing=True, apaga todos os dados antes do backfill.
    """
    truncate = context["params"].get("truncate_existing", TRUNCATE_EXISTING)
    client   = _get_bq_client()

    # Garante dataset
    ds_ref          = bigquery.Dataset(f"{GCP_PROJECT}.{BQ_DATASET}")
    ds_ref.location = BQ_LOCATION
    client.create_dataset(ds_ref, exists_ok=True)
    log.info("Dataset %s.%s: OK", GCP_PROJECT, BQ_DATASET)

    tables = {
        "open_meteo_daily":  BQ_SCHEMA_DAILY,
        "open_meteo_hourly": BQ_SCHEMA_HOURLY,
    }

    for table_name, schema in tables.items():
        table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{table_name}"
        table    = bigquery.Table(table_id, schema=schema)
        client.create_table(table, exists_ok=True)

        if truncate:
            try:
                client.query(f"TRUNCATE TABLE `{table_id}`").result()
                log.info("TRUNCATE %s: OK", table_id)
            except Exception as exc:
                # Tabela pode não existir ainda — ignorar
                log.warning("Não foi possível truncar %s: %s", table_id, exc)
        else:
            log.info("truncate_existing=False — mantendo dados existentes em %s", table_id)


def backfill_daily(**context):
    """
    Busca dados diários na API Open-Meteo Archive para todos os municípios
    e grava diretamente nas tabelas raw do BigQuery em lotes.
    """
    params     = context["params"]
    start_date = params.get("daily_start", DAILY_START)
    end_date   = params.get("daily_end",   DAILY_END)

    params       = context["params"]
    skip_existing = params.get("skip_existing", False)

    locations    = _load_locations()
    client       = _get_bq_client()
    table_id     = f"{GCP_PROJECT}.{BQ_DATASET}.open_meteo_daily"
    extracted_at = datetime.now(timezone.utc).isoformat()

    existing = _get_existing_locations(client, "open_meteo_daily", start_date) if skip_existing else set()
    if skip_existing:
        log.info("skip_existing=True — %d localizações já no BQ serão puladas", len(existing))

    log.info("Backfill DIÁRIO: %s → %s | %d municípios", start_date, end_date, len(locations))

    batch   = []
    total   = 0
    errors  = 0
    skipped = 0

    for i, loc in enumerate(locations, start=1):
        if skip_existing and loc["id"] in existing:
            log.info("  [%d/%d] %s — já coletado, pulando", i, len(locations), loc["id"])
            skipped += 1
            continue
        try:
            raw   = _fetch_archive(loc, start_date, end_date, hourly=False)
            daily = raw.get("daily", {})
            dates = daily.get("time", [])
            n     = len(dates)

            for j, d in enumerate(dates):
                batch.append({
                    "location_id":        loc["id"],
                    "date":               d,
                    "latitude":           raw.get("latitude"),
                    "longitude":          raw.get("longitude"),
                    "temperature_2m_max": daily.get("temperature_2m_max", [None] * n)[j],
                    "temperature_2m_min": daily.get("temperature_2m_min", [None] * n)[j],
                    "precipitation_sum":  daily.get("precipitation_sum",  [None] * n)[j],
                    "rain_sum":           daily.get("rain_sum",            [None] * n)[j],
                    "wind_speed_10m_max": daily.get("wind_speed_10m_max",  [None] * n)[j],
                    "sunrise":            daily.get("sunrise",             [None] * n)[j],
                    "sunset":             daily.get("sunset",              [None] * n)[j],
                    "uv_index_max":       daily.get("uv_index_max",        [None] * n)[j],
                    "_extracted_at":      extracted_at,
                })

            # Envia ao BigQuery quando o lote atingir BQ_BATCH_SIZE
            if len(batch) >= BQ_BATCH_SIZE:
                _bq_flush(client, table_id, BQ_SCHEMA_DAILY, batch)
                total += len(batch)
                log.info("  → %d registros enviados ao BQ (acumulado)", total)
                batch = []

            log.info("  [%d/%d] %s — %d dias coletados", i, len(locations), loc["id"], n)
            time.sleep(random.uniform(API_SLEEP, API_SLEEP * 2))  # intervalo aleatório evita detecção

            if i % 50 == 0:
                log.info("  Pausa de 60s após %d municípios...", i)
                time.sleep(60)

        except requests.HTTPError as exc:
            log.error("  ✗ %s — HTTP %s: %s", loc["id"], exc.response.status_code, exc)
            errors += 1
        except Exception as exc:
            log.error("  ✗ %s — %s", loc["id"], exc)
            errors += 1

    # Flush do restante
    if batch:
        _bq_flush(client, table_id, BQ_SCHEMA_DAILY, batch)
        total += len(batch)

    log.info(
        "Backfill diário concluído: %d inseridos | %d pulados | %d erros",
        total, skipped, errors,
    )
    if errors:
        log.warning(
            "%d município(s) falharam — re-execute com skip_existing=true para coletar apenas estes.", errors
        )


def backfill_hourly(**context):
    """
    Busca dados horários na API Open-Meteo Archive para todos os municípios
    e grava diretamente nas tabelas raw do BigQuery em lotes.

    Pode ser desabilitado via parâmetro include_hourly=false.
    """
    params = context["params"]

    if not params.get("include_hourly", True):
        log.info("include_hourly=false — backfill horário ignorado.")
        return

    start_date = params.get("hourly_start", HOURLY_START)
    end_date   = params.get("hourly_end",   HOURLY_END)

    skip_existing = params.get("skip_existing", False)

    locations    = _load_locations()
    client       = _get_bq_client()
    table_id     = f"{GCP_PROJECT}.{BQ_DATASET}.open_meteo_hourly"
    extracted_at = datetime.now(timezone.utc).isoformat()

    existing = _get_existing_locations(client, "open_meteo_hourly", start_date, hourly=True) if skip_existing else set()
    if skip_existing:
        log.info("skip_existing=True — %d localizações já no BQ serão puladas", len(existing))

    log.info("Backfill HORÁRIO: %s → %s | %d municípios", start_date, end_date, len(locations))

    batch   = []
    total   = 0
    errors  = 0
    skipped = 0

    for i, loc in enumerate(locations, start=1):
        if skip_existing and loc["id"] in existing:
            log.info("  [%d/%d] %s — já coletado, pulando", i, len(locations), loc["id"])
            skipped += 1
            continue
        try:
            raw    = _fetch_archive(loc, start_date, end_date, hourly=True)
            hourly = raw.get("hourly", {})
            times  = hourly.get("time", [])
            n      = len(times)

            for j, ts in enumerate(times):
                batch.append({
                    "location_id":          loc["id"],
                    "timestamp":            ts,
                    "latitude":             raw.get("latitude"),
                    "longitude":            raw.get("longitude"),
                    "elevation":            raw.get("elevation"),
                    "timezone":             raw.get("timezone"),
                    "temperature_2m":       hourly.get("temperature_2m",       [None] * n)[j],
                    "relative_humidity_2m": hourly.get("relative_humidity_2m", [None] * n)[j],
                    "precipitation":        hourly.get("precipitation",         [None] * n)[j],
                    "wind_speed_10m":       hourly.get("wind_speed_10m",        [None] * n)[j],
                    "wind_direction_10m":   hourly.get("wind_direction_10m",    [None] * n)[j],
                    "surface_pressure":     hourly.get("surface_pressure",      [None] * n)[j],
                    "cloud_cover":          hourly.get("cloud_cover",           [None] * n)[j],
                    "visibility":           hourly.get("visibility",            [None] * n)[j],
                    "weather_code":         hourly.get("weather_code",          [None] * n)[j],
                    "_extracted_at":        extracted_at,
                })

            if len(batch) >= BQ_BATCH_SIZE:
                _bq_flush(client, table_id, BQ_SCHEMA_HOURLY, batch)
                total += len(batch)
                log.info("  → %d registros enviados ao BQ (acumulado)", total)
                batch = []

            log.info("  [%d/%d] %s — %d horas coletadas", i, len(locations), loc["id"], n)
            time.sleep(random.uniform(API_SLEEP, API_SLEEP * 2))  # intervalo aleatório evita detecção

            if i % 50 == 0:
                log.info("  Pausa de 60s após %d municípios...", i)
                time.sleep(60)

        except requests.HTTPError as exc:
            log.error("  ✗ %s — HTTP %s: %s", loc["id"], exc.response.status_code, exc)
            errors += 1
        except Exception as exc:
            log.error("  ✗ %s — %s", loc["id"], exc)
            errors += 1

    if batch:
        _bq_flush(client, table_id, BQ_SCHEMA_HOURLY, batch)
        total += len(batch)

    log.info(
        "Backfill horário concluído: %d inseridos | %d pulados | %d erros",
        total, skipped, errors,
    )
    if errors:
        log.warning(
            "%d município(s) falharam — re-execute com skip_existing=true para coletar apenas estes.", errors
        )


# ── DAG ───────────────────────────────────────────────────────────────────────

with DAG(
    dag_id="dag_weather_backfill",
    description=(
        "Backfill histórico Open-Meteo Archive → BigQuery. "
        "EXECUÇÃO MANUAL ÚNICA. Não possui agendamento."
    ),
    schedule=None,           # nunca roda automaticamente
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,       # impede execuções paralelas acidentais
    tags=["weather", "backfill", "bigquery", "manual"],
    params={
        "daily_start": Param(
            default=DAILY_START,
            type="string",
            description="Data inicial dos dados DIÁRIOS (YYYY-MM-DD).",
        ),
        "daily_end": Param(
            default=DAILY_END,
            type="string",
            description="Data final dos dados DIÁRIOS (YYYY-MM-DD).",
        ),
        "include_hourly": Param(
            default=INCLUDE_HOURLY,
            type="boolean",
            description="Incluir dados HORÁRIOS? Adiciona ~30–60 min ao tempo de execução.",
        ),
        "hourly_start": Param(
            default=HOURLY_START,
            type="string",
            description="Data inicial dos dados HORÁRIOS (YYYY-MM-DD).",
        ),
        "hourly_end": Param(
            default=HOURLY_END,
            type="string",
            description="Data final dos dados HORÁRIOS (YYYY-MM-DD).",
        ),
        "truncate_existing": Param(
            default=TRUNCATE_EXISTING,
            type="boolean",
            description=(
                "Truncar tabelas weather_raw antes de inserir? "
                "True ao limpar dados antigos. False para APPEND (re-execução)."
            ),
        ),
        "skip_existing": Param(
            default=SKIP_EXISTING,
            type="boolean",
            description=(
                "Pular localizações que já têm dados no BigQuery? "
                "True em re-execuções para coletar apenas os municípios que falharam."
            ),
        ),
    },
    default_args={
        "owner": "analytics",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "email_on_failure": False,
    },
) as dag:

    task_prepare = PythonOperator(
        task_id="prepare_bigquery",
        python_callable=prepare_bigquery,
        doc_md=(
            "Cria dataset e tabelas raw no BigQuery. "
            "Se `truncate_existing=true`, apaga dados antes do backfill."
        ),
    )

    task_daily = PythonOperator(
        task_id="backfill_daily",
        python_callable=backfill_daily,
        execution_timeout=timedelta(hours=6),
        doc_md=(
            "Coleta dados **diários** (temperatura, precipitação, UV, vento, nascer/pôr do sol) "
            "da API Open-Meteo Archive para todos os 295 municípios de Santa Catarina."
        ),
    )

    task_hourly = PythonOperator(
        task_id="backfill_hourly",
        python_callable=backfill_hourly,
        execution_timeout=timedelta(hours=8),
        doc_md=(
            "Coleta dados **horários** (temperatura, umidade, precipitação, vento, pressão, "
            "cobertura de nuvens, visibilidade, código WMO) da API Open-Meteo Archive "
            "para todos os 295 municípios. Ignorado se `include_hourly=false`."
        ),
    )

    task_transform = TriggerDagRunOperator(
        task_id="trigger_transform",
        trigger_dag_id="dag_weather_transform",
        wait_for_completion=True,
        poke_interval=30,
        doc_md=(
            "Dispara o `dag_weather_transform` (dbt seed → run → test) para reconstruir "
            "staging, intermediate e marts com os dados históricos inseridos."
        ),
    )

    task_prepare >> [task_daily, task_hourly] >> task_transform
