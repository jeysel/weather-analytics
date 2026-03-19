-- tests/test_no_date_gaps_per_location.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Verifica se há dias faltando na série temporal de cada localização.
-- Lacunas maiores que 1 dia indicam falha no sync do Airbyte.
-- Retorna pares (location_id, date) onde existe um gap.
-- ─────────────────────────────────────────────────────────────────────────────

WITH date_series AS (
    SELECT
        location_id,
        date,
        LAG(date) OVER (
            PARTITION BY location_id
            ORDER BY date
        ) AS prev_date
    FROM {{ ref('mart_climate__daily_facts') }}
    WHERE date >= {% if target.type == 'bigquery' %}DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY){% else %}CURRENT_DATE - INTERVAL '30 days'{% endif %}
),

gaps AS (
    SELECT
        location_id,
        prev_date AS gap_start,
        date      AS gap_end,
        {% if target.type == 'bigquery' %}DATE_DIFF(date, prev_date, DAY){% else %}(date - prev_date){% endif %} AS gap_days
    FROM date_series
    WHERE {% if target.type == 'bigquery' %}DATE_DIFF(date, prev_date, DAY){% else %}(date - prev_date){% endif %} > 1
      AND prev_date IS NOT NULL
)

SELECT *
FROM gaps
ORDER BY location_id, gap_start
