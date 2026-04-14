{{
  config(
    materialized = 'view',
    schema = 'staging',
  )
}}

/*
  stg_weather__hourly
  ───────────────────
  Limpeza e tipagem dos dados brutos horários vindos do Airbyte.
  Fonte: raw.open_meteo_hourly (PostgreSQL staging)
*/

with source as (
    select * from {{ source('open_meteo', 'hourly') }}
),

-- Deduplica por (location_id, timestamp), mantendo a extração mais recente.
-- Necessário porque o BigQuery acumula re-ingestões via WRITE_APPEND.
deduped as (
    select *,
        row_number() over (
            partition by location_id, timestamp
            order by _extracted_at desc
        ) as _row_num
    from source
    where timestamp is not null
      and location_id is not null
),

renamed as (
    select
        -- Chaves
        CAST(location_id AS {{ dbt.type_string() }})        as location_id,
        CAST(timestamp AS {{ dbt.type_timestamp() }})       as observed_at,

        -- Geo
        CAST(latitude AS {{ dbt.type_numeric() }})          as latitude,
        CAST(longitude AS {{ dbt.type_numeric() }})         as longitude,
        CAST(elevation AS {{ dbt.type_numeric() }})         as elevation_m,
        CAST(timezone AS {{ dbt.type_string() }})           as timezone,

        -- Temperatura
        CAST(temperature_2m AS {{ dbt.type_numeric() }})    as temperature_c,

        -- Umidade
        CAST(relative_humidity_2m AS {{ dbt.type_int() }})  as relative_humidity_pct,

        -- Precipitação
        CAST(precipitation AS {{ dbt.type_numeric() }})     as precipitation_mm,

        -- Vento
        CAST(wind_speed_10m AS {{ dbt.type_numeric() }})    as wind_speed_kmh,
        CAST(wind_direction_10m AS {{ dbt.type_int() }})    as wind_direction_deg,

        -- Atmosfera
        CAST(surface_pressure AS {{ dbt.type_numeric() }})  as surface_pressure_hpa,
        CAST(cloud_cover AS {{ dbt.type_int() }})           as cloud_cover_pct,
        CAST(visibility AS {{ dbt.type_numeric() }})        as visibility_m,

        -- Código WMO de condição climática
        CAST(weather_code AS {{ dbt.type_int() }})          as wmo_weather_code,

        -- Metadados
        CAST(_extracted_at AS {{ dbt.type_timestamp() }})   as _extracted_at,
        current_timestamp                                    as _loaded_at

    from deduped
    where _row_num = 1
)

select * from renamed
