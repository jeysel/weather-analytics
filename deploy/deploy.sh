#!/bin/bash
# deploy.sh — Atualiza o weather-analytics no servidor de produção
# Uso: bash deploy.sh
set -euo pipefail

cd /home/ubuntu/app_weather

echo "→ Atualizando repositório..."
git pull origin main

echo "→ Subindo Streamlit..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "✅ weather-analytics atualizado!"
echo "   Dashboard: https://weather.jeysel.dev"
echo "   Logs:      docker compose -f docker-compose.prod.yml logs -f"
