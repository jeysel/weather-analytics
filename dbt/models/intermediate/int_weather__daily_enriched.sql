{{
  config(
    materialized = 'view',
    schema = 'intermediate',
  )
}}



with daily as (
    select * from {{ ref('stg_weather__daily') }}
),

locations as (
    select * from {{ ref('locations') }}
),

joined as (
    select
       
        d.location_id,
        d.date,

      
        l.city_name,
        l.state_name,
        l.country,
        l.region,
        l.mesoregion,
        l.latitude,
        l.longitude,
        l.altitude_m,

        
        d.temp_max_c,
        d.temp_min_c,
        d.temp_avg_c,

        
        d.precipitation_mm,
        d.rain_mm,

        
        d.wind_speed_max_kmh,
        d.uv_index_max,

      
        d.sunrise_at,
        d.sunset_at,
        {% if target.type == 'bigquery' %}
        TIMESTAMP_DIFF(d.sunset_at, d.sunrise_at, SECOND)
        {% else %}
        extract(epoch from (d.sunset_at - d.sunrise_at))
        {% endif %} / 3600.0                                as daylight_hours,

       
        avg(d.temp_avg_c) over (
            partition by d.location_id
            order by d.date
            rows between 29 preceding and current row
        )                                                   as temp_avg_30d_c,

        avg(d.precipitation_mm) over (
            partition by d.location_id
            order by d.date
            rows between 29 preceding and current row
        )                                                   as precip_avg_30d_mm,

        
        d._extracted_at,
        d._loaded_at

    from daily d
    left join locations l using (location_id)
)

select * from joined
