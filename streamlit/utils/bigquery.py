import os
import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()


def _project() -> str:
    val = os.environ.get("GCP_PROJECT_ID", "")
    if not val:
        raise EnvironmentError(
            "GCP_PROJECT_ID não definido. Crie um arquivo .env com base em .env.example"
        )
    return val


def _dataset(seeds: bool = False) -> str:
    if seeds:
        return os.environ.get(
            "BIGQUERY_SEEDS_DATASET",
            os.environ.get("BIGQUERY_DATASET", "marts"),
        )
    return os.environ.get("BIGQUERY_DATASET", "marts")


def tbl(name: str, seeds: bool = False) -> str:
    """Returns a backtick-quoted fully-qualified BigQuery table reference."""
    return f"`{_project()}.{_dataset(seeds)}.{name}`"


def _location() -> str | None:
    return os.environ.get("BIGQUERY_LOCATION") or None


@st.cache_resource
def _client() -> bigquery.Client:
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path:
        creds = service_account.Credentials.from_service_account_file(key_path)
        return bigquery.Client(project=_project(), credentials=creds, location=_location())
    return bigquery.Client(project=_project(), location=_location())


@st.cache_data(ttl=3600, show_spinner="Consultando BigQuery...")
def query(sql: str) -> pd.DataFrame:
    return _client().query(sql).to_dataframe()


MESOREGIONS = [
    "Grande Florianópolis",
    "Norte Catarinense",
    "Vale do Itajaí",
    "Serrana",
    "Oeste Catarinense",
    "Sul Catarinense",
]
