---
title: Weather Analytics — Visão Geral
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
select value, label from (
  select 'Todas' as value, 'Todos os Municípios' as label, 0 as ord
  union all
  select distinct location_id as value, city_name as label, 1 as ord
  from weather_dw.mart_climate__daily_facts
  where ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
)
order by ord, label
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
  name="cidade"
  data={cidades_disponiveis}
  value="value"
  label="label"
  title="Município"
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

```sql scorecards
select
  round(max(temp_max_c), 1)        as temp_maxima,
  round(min(temp_min_c), 1)        as temp_minima,
  round(avg(temp_avg_c), 1)        as temp_media,
  round(sum(precipitation_mm), 1)  as precip_acumulada_mm,
  round(avg(temp_anomaly_c), 2)    as anomalia_media
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
```

```sql serie_diaria
select
  date,
  round(avg(temp_avg_c), 1)     as temp_media_c,
  round(avg(temp_anomaly_c), 2) as anomalia_c
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
group by date
order by date
```

```sql mapa_municipios
select
  city_name,
  mesoregion,
  round(avg(latitude), 4)          as latitude,
  round(avg(longitude), 4)         as longitude,
  round(avg(temp_avg_c), 1)        as temp_media_c,
  round(avg(temp_amplitude_c), 1)  as amplitude_media_c
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
group by city_name, mesoregion
```

# Visão Geral Climática — Santa Catarina

Santa Catarina concentra ao mesmo tempo alguns dos municípios mais frios do Brasil e regiões de calor intenso no Oeste e no Vale do Itajaí. Esta página responde uma pergunta simples: **como está o clima no mês selecionado, comparado ao que é esperado para esta época?**

---

<BigValue
  data={scorecards}
  value="temp_maxima"
  title="Temperatura Máxima"
  fmt="0.0°C"
/>
<BigValue
  data={scorecards}
  value="temp_minima"
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
  value="precip_acumulada_mm"
  title="Precipitação Acumulada"
  fmt="0.0mm"
/>
<BigValue
  data={scorecards}
  value="anomalia_media"
  title="Anomalia Média"
  fmt="+0.00;-0.00°C"
/>

---

## Temperatura Média Diária e Desvio Histórico

A linha azul mostra a temperatura média diária no período. A linha laranja indica o desvio em relação à média dos últimos 30 dias — valores positivos significam dias mais quentes que o normal histórico recente; negativos, mais frios.

<LineChart
  data={serie_diaria}
  x="date"
  y={["temp_media_c", "anomalia_c"]}
  yAxisTitle="Temperatura (°C)"
  xFmt="dd/MM/yyyy"
  labels
  colorPalette={["#4A90D9", "#FF6B35"]}
/>

---

## Temperatura Média por Município

O mapa mostra onde está mais quente ou mais frio no estado. O tamanho de cada bolha representa a amplitude térmica do município — quão diferente foi a temperatura entre máxima e mínima no período. A Serra Catarinense e o Oeste costumam apresentar os maiores contrastes.

<BubbleMap
  data={mapa_municipios}
  lat="latitude"
  long="longitude"
  size="amplitude_media_c"
  value="temp_media_c"
  pointName="city_name"
  valueFmt="0.0°C"
  title="Temperatura média por município (tamanho = amplitude térmica)"
/>

---

**Navegação:** [Temperatura](/temperatura) · [Precipitação](/precipitacao) · [Alertas](/alertas) · [Horário](/horario)
