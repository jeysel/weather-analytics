{{
  config(
    materialized = 'view',
    schema = 'staging',
  )
}}

/*
  stg_weather__daily
  ──────────────────
  Dados diários agregados da Open-Meteo (forecast + archive).
*/

with source as (
    select * from {{ source('open_meteo', 'daily') }}
),

renamed as (
    select
        CAST(location_id AS {{ dbt.type_string() }})        as location_id,
        CAST(date AS DATE)                                  as date,
        CAST(latitude AS {{ dbt.type_numeric() }})          as latitude,
        CAST(longitude AS {{ dbt.type_numeric() }})         as longitude,

        -- Temperatura
        CAST(temperature_2m_max AS {{ dbt.type_numeric() }})    as temp_max_c,
        CAST(temperature_2m_min AS {{ dbt.type_numeric() }})    as temp_min_c,
        CAST((temperature_2m_max + temperature_2m_min) AS {{ dbt.type_numeric() }})
            / 2                                                 as temp_avg_c,

        -- Precipitação
        CAST(precipitation_sum AS {{ dbt.type_numeric() }})     as precipitation_mm,
        CAST(rain_sum AS {{ dbt.type_numeric() }})              as rain_mm,

        -- Vento
        CAST(wind_speed_10m_max AS {{ dbt.type_numeric() }})    as wind_speed_max_kmh,

        -- Radiação / UV
        CAST(uv_index_max AS {{ dbt.type_numeric() }})          as uv_index_max,

        -- Sol
        CAST(sunrise AS {{ dbt.type_timestamp() }})             as sunrise_at,
        CAST(sunset AS {{ dbt.type_timestamp() }})              as sunset_at,

        -- Metadados
        CAST(_extracted_at AS {{ dbt.type_timestamp() }})       as _extracted_at,
        current_timestamp                                        as _loaded_at

    from source
    where date is not null
      and location_id is not null
)

select * from renamed
