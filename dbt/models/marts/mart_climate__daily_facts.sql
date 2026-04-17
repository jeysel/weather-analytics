{{
  config(
    materialized = 'table',
    schema = 'marts',
    partition_by = {
      "field": "date",
      "data_type": "date",
      "granularity": "month"
    },
    cluster_by = ["location_id", "year_month"]
  )
}}



with enriched as (
    select * from {{ ref('int_weather__daily_enriched') }}
),

final as (
    select
        -- Chave única da linha
        {{ dbt_utils.generate_surrogate_key(['location_id', 'date']) }} as surrogate_key,

        -- Dimensão tempo
        date,
        CAST(extract(year from date) AS {{ dbt.type_int() }})     as year,
        CAST(extract(month from date) AS {{ dbt.type_int() }})    as month,
        CAST(extract(day from date) AS {{ dbt.type_int() }})      as day,
        {% if target.type == 'bigquery' %}
        FORMAT_DATE('%Y-%m', date)
        {% else %}
        to_char(date, 'YYYY-MM')
        {% endif %}                                                as year_month,
        CAST({% if target.type == 'bigquery' %}EXTRACT(DAYOFWEEK FROM date) - 1{% else %}extract(dow from date){% endif %} AS {{ dbt.type_int() }}) as day_of_week,
        case
            when {% if target.type == 'bigquery' %}EXTRACT(DAYOFWEEK FROM date) - 1{% else %}extract(dow from date){% endif %} in (0, 6)
            then true else false
        end                                                        as is_weekend,
        CAST(extract(quarter from date) AS {{ dbt.type_int() }})  as quarter,

        -- Dimensão localização
        location_id,
        city_name,
        state_name,
        country,
        region,
        mesoregion,
        latitude,
        longitude,
        altitude_m,

        -- Métricas de temperatura
        temp_max_c,
        temp_min_c,
        temp_avg_c,
        round(temp_max_c - temp_min_c, 2)                         as temp_amplitude_c,

        -- Anomalia de temperatura
        round(temp_avg_c - temp_avg_30d_c, 2)                     as temp_anomaly_c,
        temp_avg_30d_c,

        -- Precipitação
        precipitation_mm,
        rain_mm,
        precip_avg_30d_mm,
        round(precipitation_mm - precip_avg_30d_mm, 2)            as precip_anomaly_mm,
        case
            when precipitation_mm = 0     then 'dry'
            when precipitation_mm < 5     then 'light'
            when precipitation_mm < 20    then 'moderate'
            when precipitation_mm < 50    then 'heavy'
            else 'extreme'
        end                                                        as precipitation_class,

        -- Vento e UV
        wind_speed_max_kmh,
        uv_index_max,
        case
            when uv_index_max < 3  then 'low'
            when uv_index_max < 6  then 'moderate'
            when uv_index_max < 8  then 'high'
            when uv_index_max < 11 then 'very_high'
            else 'extreme'
        end                                                        as uv_risk_level,

        -- Horas de sol
        sunrise_at,
        sunset_at,
        daylight_hours,

        -- Metadados de pipeline
        _extracted_at,
        _loaded_at,
        current_timestamp                                          as _dbt_updated_at

    from enriched
)

select * from final
