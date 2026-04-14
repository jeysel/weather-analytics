{{
  config(
    materialized = 'table',
    schema = 'marts',
    partition_by = {
      "field": "date",
      "data_type": "date",
      "granularity": "day"
    },
    cluster_by = ["location_id", "mesoregion"]
  )
}}

with hourly as (
    select * from {{ ref('stg_weather__hourly') }}
),

locations as (
    select * from {{ ref('locations') }}
),

joined as (
    select
        -- Chave única da linha
        {{ dbt_utils.generate_surrogate_key(['h.location_id', 'h.observed_at']) }} as surrogate_key,

        -- Dimensão tempo
        h.observed_at,
        {% if target.type == 'bigquery' %}
        DATE(h.observed_at)
        {% else %}
        CAST(h.observed_at AS DATE)
        {% endif %}                                                          as date,
        CAST(EXTRACT(HOUR FROM h.observed_at) AS {{ dbt.type_int() }})      as hour,
        CAST(EXTRACT(YEAR FROM h.observed_at) AS {{ dbt.type_int() }})      as year,
        CAST(EXTRACT(MONTH FROM h.observed_at) AS {{ dbt.type_int() }})     as month,
        {% if target.type == 'bigquery' %}
        FORMAT_DATE('%Y-%m', DATE(h.observed_at))
        {% else %}
        TO_CHAR(DATE(h.observed_at), 'YYYY-MM')
        {% endif %}                                                          as year_month,

        -- Dimensão localização
        h.location_id,
        l.city_name,
        l.state_name,
        l.region,
        l.mesoregion,
        l.latitude,
        l.longitude,

        -- Temperatura
        h.temperature_c,

        -- Umidade
        h.relative_humidity_pct,

        -- Precipitação
        h.precipitation_mm,

        -- Vento
        h.wind_speed_kmh,
        h.wind_direction_deg,

        -- Atmosfera
        h.surface_pressure_hpa,
        h.cloud_cover_pct,
        h.visibility_m,

        -- Condição climática
        h.wmo_weather_code,
        {{ wmo_code_to_label('h.wmo_weather_code') }}                       as wmo_weather_label,

        -- Metadados de pipeline
        h._extracted_at,
        h._loaded_at,
        current_timestamp                                                    as _dbt_updated_at

    from hourly h
    left join locations l using (location_id)
)

select * from joined
