FROM apache/airflow:2.9.1-python3.11

# Instala todas as dependências na build da imagem.
# Evita pip install em runtime (que trava o airflow-init com dbt-bigquery).
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
