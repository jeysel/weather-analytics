-- Total de linhas inseridas
SELECT COUNT(*) FROM `seu-projeto.weather_raw.open_meteo_daily`;
SELECT COUNT(*) FROM `seu-projeto.weather_raw.open_meteo_hourly`;

-- Municípios distintos coletados (esperado: 295)
SELECT COUNT(DISTINCT location_id) AS municipios_coletados
FROM `seu-projeto.weather_raw.open_meteo_daily`;

-- Linhas por município (dados diários)
-- Resultado esperado para o período: Período: 2021-01-01 → 2026-04-15 = 1.931 dias
SELECT location_id, COUNT(*) AS total
FROM `seu-projeto.weather_raw.open_meteo_daily`
GROUP BY location_id
ORDER BY location_id;

-- Municípios com coleta INCOMPLETA — diário (menos de 1931 linhas)
-- Municípios ausentes da tabela também aparecem (via seeds/locations.csv como referência)
SELECT location_id, COUNT(*) AS total_coletado,
       1931 - COUNT(*) AS dias_faltando
FROM `seu-projeto.weather_raw.open_meteo_daily`
GROUP BY location_id
HAVING COUNT(*) < 1931
ORDER BY dias_faltando DESC;

-- Linhas por município (dados por hora)
-- Resultado esperado para o período: Período: 2021-01-01 → 2026-04-15 = 20064 linhas
SELECT location_id, COUNT(*) AS total,
       COUNT(*) - 20064 AS diferenca
FROM `seu-projeto.weather_raw.open_meteo_hourly`
GROUP BY location_id
HAVING COUNT(*) != 20064
ORDER BY diferenca;

-- Municípios com coleta INCOMPLETA — horário (menos de 20064 linhas)
SELECT location_id, COUNT(*) AS total_coletado,
       20064 - COUNT(*) AS horas_faltando
FROM `seu-projeto.weather_raw.open_meteo_hourly`
GROUP BY location_id
HAVING COUNT(*) < 20064
ORDER BY horas_faltando DESC;
