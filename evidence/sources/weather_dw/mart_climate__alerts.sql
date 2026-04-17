-- Quando não há alertas, retorna uma linha placeholder com date='1900-01-01'
-- para evitar parquet vazio (0 bytes) que o DuckDB rejeita.
-- As queries nas páginas filtram por date >= últimos 30/60 dias,
-- o que descarta automaticamente a linha placeholder.
select * from marts.mart_climate__alerts
union all
select
  '__no_alerts__'          as surrogate_key,
  date '1900-01-01'        as date,
  cast(null as string)     as year_month,
  cast(null as string)     as location_id,
  cast(null as string)     as city_name,
  cast(null as string)     as state_name,
  cast(null as string)     as region,
  cast(null as string)     as mesoregion,
  '__no_alerts__'          as alert_type,
  'low'                    as severity,
  cast(0.0 as float64)     as temp_max_c,
  cast(0.0 as float64)     as temp_min_c,
  cast(0.0 as float64)     as temp_anomaly_c,
  cast(0.0 as float64)     as precipitation_mm,
  cast(0.0 as float64)     as wind_speed_max_kmh,
  cast(0.0 as float64)     as uv_index_max,
  current_timestamp()      as _dbt_updated_at
from (select 1)
where not exists (select 1 from marts.mart_climate__alerts limit 1)
