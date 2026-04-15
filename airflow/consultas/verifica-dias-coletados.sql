--
-- Se retornar zero linhas, todos os 295 municípios estão completos. Se retornar algum, a coluna dias_faltando mostra quantos dias estão faltando por município.
--


SELECT
  location_id,
  COUNT(*)                                                          AS dias_coletados,
  DATE_DIFF(DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), DATE '2021-01-01', DAY) + 1 AS dias_esperados,
  DATE_DIFF(DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), DATE '2021-01-01', DAY) + 1
    - COUNT(*)                                                      AS dias_faltando
FROM `weather-analytics-490113.weather_raw.open_meteo_daily`
GROUP BY location_id
HAVING COUNT(*) < DATE_DIFF(DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), DATE '2021-01-01', DAY) + 1
ORDER BY dias_faltando DESC;