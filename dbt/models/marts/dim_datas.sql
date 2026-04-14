{{
  config(
    materialized = 'table',
    schema = 'marts',
  )
}}

/*
  dim_datas
  ─────────
  Dimensão calendário gerada pelo pacote dbt_date.
  Período: 2024-01-01 a 2030-12-31.
  Enriquecida com nomes em português e estações do Hemisfério Sul.
*/

with base as (
    {{ dbt_date.get_date_dimension('2024-01-01', '2030-12-31') }}
),

enriched as (
    select
        -- Chave natural (DATE é única por definição — sem necessidade de surrogate key)
        date_day                                                        as dt_data,

        -- Atributos numéricos
        year_number                                                     as ano,
        month_of_year                                                   as mes,
        day_of_month                                                    as dia,
        quarter_of_year                                                 as trimestre,
        week_of_year                                                    as semana_ano,
        iso_week_of_year                                                as semana_iso,
        day_of_week                                                     as dia_semana_num,  -- 0=Dom, 6=Sáb
        day_of_year                                                     as dia_do_ano,

        -- Nomes em português
        case month_of_year
            when 1  then 'Janeiro'    when 2  then 'Fevereiro'
            when 3  then 'Março'      when 4  then 'Abril'
            when 5  then 'Maio'       when 6  then 'Junho'
            when 7  then 'Julho'      when 8  then 'Agosto'
            when 9  then 'Setembro'   when 10 then 'Outubro'
            when 11 then 'Novembro'   when 12 then 'Dezembro'
        end                                                             as nm_mes,

        case month_of_year
            when 1  then 'Jan'  when 2  then 'Fev'  when 3  then 'Mar'
            when 4  then 'Abr'  when 5  then 'Mai'  when 6  then 'Jun'
            when 7  then 'Jul'  when 8  then 'Ago'  when 9  then 'Set'
            when 10 then 'Out'  when 11 then 'Nov'  when 12 then 'Dez'
        end                                                             as nm_mes_abrev,

        case day_of_week
            when 0 then 'Domingo'       when 1 then 'Segunda-feira'
            when 2 then 'Terça-feira'   when 3 then 'Quarta-feira'
            when 4 then 'Quinta-feira'  when 5 then 'Sexta-feira'
            when 6 then 'Sábado'
        end                                                             as nm_dia_semana,

        case day_of_week
            when 0 then 'Dom'  when 1 then 'Seg'  when 2 then 'Ter'
            when 3 then 'Qua'  when 4 then 'Qui'  when 5 then 'Sex'
            when 6 then 'Sáb'
        end                                                             as nm_dia_semana_abrev,

        -- Estação do ano — Hemisfério Sul (Santa Catarina)
        case
            when (month_of_year = 12 and day_of_month >= 21)
              or  month_of_year in (1, 2)
              or (month_of_year = 3  and day_of_month <= 20)  then 'Verão'
            when (month_of_year = 3  and day_of_month >= 21)
              or  month_of_year in (4, 5)
              or (month_of_year = 6  and day_of_month <= 20)  then 'Outono'
            when (month_of_year = 6  and day_of_month >= 21)
              or  month_of_year in (7, 8)
              or (month_of_year = 9  and day_of_month <= 22)  then 'Inverno'
            else 'Primavera'
        end                                                             as estacao,

        -- Formatos compostos
        {% if target.type == 'bigquery' %}
        FORMAT_DATE('%Y-%m', date_day)
        {% else %}
        TO_CHAR(date_day, 'YYYY-MM')
        {% endif %}                                                     as ano_mes,

        CAST(quarter_of_year AS {{ dbt.type_string() }}) || 'º Tri'    as nm_trimestre,
        'Q' || CAST(quarter_of_year AS {{ dbt.type_string() }})        as sigla_trimestre,

        -- Flags
        day_of_week in (0, 6)                                          as fl_fim_de_semana,

        -- Limites de período
        month_start_date                                                as primeiro_dia_mes,
        month_end_date                                                  as ultimo_dia_mes,
        quarter_start_date                                              as primeiro_dia_trimestre,
        quarter_end_date                                                as ultimo_dia_trimestre,
        year_start_date                                                 as primeiro_dia_ano,
        year_end_date                                                   as ultimo_dia_ano,

        -- Referências ano anterior (útil para YoY no Looker Studio)
        prior_year_date_day                                             as dt_data_ano_anterior,
        prior_date_day                                                  as dt_data_ontem,
        next_date_day                                                   as dt_data_amanha

    from base
)

select * from enriched
order by dt_data
