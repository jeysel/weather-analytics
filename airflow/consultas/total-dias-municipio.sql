
SELECT location_id, COUNT(*) as total
FROM `weather-analytics-490113.weather_raw.open_meteo_daily`
GROUP BY location_id
ORDER BY location_id;