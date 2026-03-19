-- tests/test_raw_data_freshness.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Verifica se todas as localizações monitoradas receberam dados
-- nas últimas 25 horas (SLA do Airbyte).
-- Retorna localizações com dados desatualizados.
-- ─────────────────────────────────────────────────────────────────────────────

WITH expected_locations AS (
    SELECT location_id FROM {{ ref('locations') }}
),

latest_load AS (
    SELECT
        location_id,
        MAX(_extracted_at) AS latest_extracted_at
    FROM {{ source('open_meteo', 'daily') }}
    GROUP BY location_id
),

freshness_check AS (
    SELECT
        e.location_id,
        l.latest_extracted_at,
        {% if target.type == 'bigquery' %}
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(l.latest_extracted_at AS TIMESTAMP), HOUR) AS age_hours,
        CASE
            WHEN l.latest_extracted_at IS NULL THEN 'never_loaded'
            WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(l.latest_extracted_at AS TIMESTAMP), HOUR) > 25 THEN 'stale'
            ELSE 'fresh'
        END AS status
        {% else %}
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - l.latest_extracted_at)) / 3600 AS age_hours,
        CASE
            WHEN l.latest_extracted_at IS NULL THEN 'never_loaded'
            WHEN CURRENT_TIMESTAMP - l.latest_extracted_at > INTERVAL '25 hours' THEN 'stale'
            ELSE 'fresh'
        END AS status
        {% endif %}
    FROM expected_locations e
    LEFT JOIN latest_load l USING (location_id)
)

SELECT *
FROM freshness_check
WHERE status != 'fresh'
ORDER BY age_hours DESC NULLS FIRST
