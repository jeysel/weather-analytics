-- horas esperadas x horas faltando
SELECT
  location_id,
  COUNT(*)                                                              AS horas_coletadas,
  20016                                                                 AS horas_esperadas,
  20016 - COUNT(*)                                                      AS horas_faltando
FROM `weather-analytics-490113.weather_raw.open_meteo_hourly`
GROUP BY location_id
HAVING COUNT(*) < 20016
ORDER BY horas_faltando DESC;


-- municipios com dados horários  completos
SELECT COUNT(DISTINCT location_id) AS municipios_completos
FROM `weather-analytics-490113.weather_raw.open_meteo_hourly`
WHERE location_id IN (
  SELECT location_id
  FROM `weather-analytics-490113.weather_raw.open_meteo_hourly`
  GROUP BY location_id
  HAVING COUNT(*) >= 20016
);

