#!/bin/bash
# Pipeline principal: ingestão + transformação dbt
# Chamado pelo cron via docker compose run --rm weather-pipeline

set -euo pipefail

LOG_DIR=/app/logs
LOG_FILE="$LOG_DIR/pipeline_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "════════════════════════════════════════════"
echo "  Weather Analytics Pipeline"
echo "  Início: $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════"

PASSO_OK=0
PASSO_FALHOU=""

# ── Passo 1: Ingestão Open-Meteo → BigQuery ──────────────────────────────────
echo ""
echo "--- [1/3] Ingestão Open-Meteo → BigQuery ---"
if python /app/pipeline/ingest.py; then
    echo "✓ Ingestão concluída"
    PASSO_OK=$((PASSO_OK + 1))
else
    echo "✗ ERRO: ingestão falhou (exit $?)"
    PASSO_FALHOU="ingest.py"
    echo ""
    echo "Pipeline abortado em: $(date '+%Y-%m-%d %H:%M:%S')"
    exit 1
fi

# ── Passo 2: dbt deps + run ──────────────────────────────────────────────────
echo ""
echo "--- [2/3] dbt run ---"
if dbt deps --project-dir /app/dbt --profiles-dir /app/pipeline --no-use-colors \
   && dbt run  --project-dir /app/dbt --profiles-dir /app/pipeline --no-use-colors; then
    echo "✓ dbt run concluído"
    PASSO_OK=$((PASSO_OK + 1))
else
    echo "✗ ERRO: dbt run falhou"
    PASSO_FALHOU="dbt run"
    echo ""
    echo "Pipeline abortado em: $(date '+%Y-%m-%d %H:%M:%S')"
    exit 1
fi

# ── Passo 3: dbt test ────────────────────────────────────────────────────────
echo ""
echo "--- [3/3] dbt test ---"
if dbt test --project-dir /app/dbt --profiles-dir /app/pipeline --no-use-colors; then
    echo "✓ dbt test passou"
    PASSO_OK=$((PASSO_OK + 1))
else
    echo "✗ AVISO: dbt test falhou (dados carregados, mas testes detectaram anomalias)"
    PASSO_FALHOU="dbt test"
    # Falha nos testes é exit 1 mas não reverte os dados — apenas alerta
    echo ""
    echo "Pipeline concluído com alertas em: $(date '+%Y-%m-%d %H:%M:%S')"
    exit 1
fi

# ── Resumo ────────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════"
echo "  Resumo: $PASSO_OK/3 passos concluídos"
echo "  Fim:    $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════"
