-- =============================================================================
-- Macro: test_accepted_range
-- Descrição: Teste genérico de data quality que valida se os valores de uma
--            coluna numérica estão dentro de um intervalo esperado [min, max].
--            Retorna o número de registros que violam o intervalo.
--            O teste falha se COUNT(*) > 0.
-- Uso no schema.yml:
--   tests:
--     - utils.test_accepted_range:
--         min_value: 0
--         max_value: 100
-- =============================================================================
 
{% macro test_accepted_range(model, column_name, min_value, max_value) %}
 
WITH validation AS (
    SELECT
        {{ column_name }} AS value
    FROM {{ model }}
    WHERE {{ column_name }} < {{ min_value }}
       OR {{ column_name }} > {{ max_value }}
)
 
SELECT COUNT(*) AS failures
FROM validation
HAVING COUNT(*) > 0
 
{% endmacro %}