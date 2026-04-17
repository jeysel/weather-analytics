---
title: Análise de Temperatura
---

```sql mesorregioes
select value, label from (
  select 'Todas' as value, 'Todas as Mesorregiões' as label, 0 as ord
  union all
  select distinct mesoregion as value, mesoregion as label, 1 as ord
  from weather_dw.mart_climate__daily_facts
)
order by ord, label
```

```sql cidades_disponiveis
select distinct
  location_id as value,
  city_name   as label
from weather_dw.mart_climate__daily_facts
where ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
order by city_name
```

```sql meses_disponiveis
select distinct
  year_month as value,
  year_month as label
from weather_dw.mart_climate__daily_facts
order by year_month desc
limit 24
```

```sql mes_mais_recente
select max(year_month) as value
from weather_dw.mart_climate__daily_facts
```

<Dropdown
  name="mesoregiao"
  data={mesorregioes}
  value="value"
  label="label"
  title="Mesorregião"
  defaultValue="Todas"
/>

<Dropdown
  name="ano_mes"
  data={meses_disponiveis}
  value="value"
  label="label"
  title="Mês/Ano"
  defaultValue={mes_mais_recente[0]?.value}
/>

<Dropdown
  name="cidade_a"
  data={cidades_disponiveis}
  value="value"
  label="label"
  title="Município A"
  defaultValue="florianopolis"
/>

<Dropdown
  name="cidade_b"
  data={cidades_disponiveis}
  value="value"
  label="label"
  title="Município B"
  defaultValue="lages"
/>

<Dropdown
  name="cidade_c"
  data={cidades_disponiveis}
  value="value"
  label="label"
  title="Município C (opcional)"
  defaultValue="chapeco"
/>

```sql scorecards
select
  round(max(temp_max_c), 1)                                              as temp_maxima_abs,
  round(min(temp_min_c), 1)                                              as temp_minima_abs,
  round(avg(temp_avg_c), 1)                                              as temp_media,
  round(max(temp_amplitude_c), 1)                                        as maior_amplitude,
  count(distinct city_name) filter (where temp_max_c > 38)               as municipios_acima_38
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
```

```sql ranking_por_regiao
select
  mesoregion                        as regiao,
  round(max(temp_max_c), 1)        as temp_maxima,
  round(avg(temp_avg_c), 1)        as temp_media,
  round(min(temp_min_c), 1)        as temp_minima,
  round(avg(temp_amplitude_c), 1)  as amplitude_media
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
group by mesoregion
order by temp_maxima desc
```

```sql amplitude_por_regiao
select
  mesoregion                        as regiao,
  round(avg(temp_amplitude_c), 1)  as amplitude_media,
  round(max(temp_max_c), 1)        as temp_maxima,
  round(avg(temp_avg_c), 1)        as temp_media,
  round(min(temp_min_c), 1)        as temp_minima
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
group by mesoregion
order by amplitude_media desc
```

```sql serie_comparativa
select
  date,
  city_name,
  round(avg(temp_max_c), 1) as temp_max_c
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and location_id in (
    '${inputs.cidade_a.value}',
    '${inputs.cidade_b.value}',
    '${inputs.cidade_c.value}'
  )
group by date, city_name
order by date, city_name
```

```sql media_geral_sc
select
  date,
  round(avg(temp_max_c), 1) as media_sc
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
group by date
order by date
```

# Análise de Temperatura — Santa Catarina

A temperatura define o conforto térmico, o risco à saúde, a produção agrícola e o consumo de energia. Mas entendê-la exige mais do que saber o máximo do dia: é preciso ver **onde está quente, quanto varia e como cada município se comporta ao longo do tempo**.

Santa Catarina é um caso único no Brasil — concentra municípios como São Joaquim e Urupema, entre os mais frios do país, e ao mesmo tempo regiões de calor intenso no Oeste e no Vale do Itajaí. Essa heterogeneidade torna a análise de amplitude térmica especialmente relevante aqui.

---

<BigValue
  data={scorecards}
  value="temp_maxima_abs"
  title="Temperatura Máxima"
  fmt="0.0°C"
/>
<BigValue
  data={scorecards}
  value="temp_minima_abs"
  title="Temperatura Mínima"
  fmt="0.0°C"
/>
<BigValue
  data={scorecards}
  value="temp_media"
  title="Temperatura Média"
  fmt="0.0°C"
/>
<BigValue
  data={scorecards}
  value="maior_amplitude"
  title="Maior Amplitude"
  fmt="0.0°C"
/>
<BigValue
  data={scorecards}
  value="municipios_acima_38"
  title="Municípios acima de 38°C"
/>

---

## Temperaturas Máximas por Região

O ranking de regiões é o ponto de partida: quais áreas de Santa Catarina registraram os maiores picos de calor? A distância entre a máxima e a média de cada região revela se o calor foi pontual — um dia de pico isolado — ou se representou um período sustentado de temperaturas elevadas.

<BarChart
  data={ranking_por_regiao}
  x="regiao"
  y={["temp_maxima", "temp_media", "temp_minima"]}
  yAxisTitle="Temperatura (°C)"
  swapXY=true
  type="grouped"
  colorPalette={["#D73027", "#FC8D59", "#4575B4"]}
/>

---

## Amplitude Térmica por Região

A amplitude térmica — diferença entre máxima e mínima no período — é o indicador de heterogeneidade climática interna. Regiões com alta amplitude têm clima mais continental: noites frias e dias quentes. A Serra Catarinense costuma liderar esse indicador, com impacto direto na agricultura (risco de geada após dias quentes), na saúde pública e no planejamento urbano.

<BarChart
  data={amplitude_por_regiao}
  x="regiao"
  y="amplitude_media"
  yAxisTitle="Amplitude térmica média (°C)"
  swapXY=true
  colorPalette={["#FC8D59"]}
  labels
/>

<DataTable data={amplitude_por_regiao}>
  <Column id="regiao" title="Região" />
  <Column id="temp_minima" title="Mínima (°C)" fmt="0.0" />
  <Column id="temp_media" title="Média (°C)" fmt="0.0" />
  <Column id="temp_maxima" title="Máxima (°C)" fmt="0.0" contentType="colorscale" />
  <Column id="amplitude_media" title="Amplitude (°C)" fmt="0.0" contentType="colorscale" />
</DataTable>

---

## Temperatura Máxima Diária — Comparativo por Município

Selecione até três municípios nos filtros acima para comparar como a temperatura máxima evoluiu ao longo do mês. É possível identificar divergências entre localidades próximas, detectar episódios de calor intenso localizados e acompanhar se a tendência de um município acompanha ou se distancia da média geral do estado.

<LineChart
  data={serie_comparativa}
  x="date"
  y="temp_max_c"
  series="city_name"
  yAxisTitle="Temperatura Máxima (°C)"
  xFmt="dd/MM/yyyy"
  labels
/>

<LineChart
  data={media_geral_sc}
  x="date"
  y="media_sc"
  yAxisTitle="Temperatura Máxima Média — SC (°C)"
  xFmt="dd/MM/yyyy"
  colorPalette={["#999999"]}
  title="Média geral de Santa Catarina no período"
/>

---

**Navegação:** [Início](/) · [Precipitação](/precipitacao) · [Alertas](/alertas) · [Horário](/horario)
