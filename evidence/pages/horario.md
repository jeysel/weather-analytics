---
title: Análise Horária
---

```sql mesorregioes
select value, label from (
  select 'Todas' as value, 'Todas as Mesorregiões' as label, 0 as ord
  union all
  select distinct mesoregion as value, mesoregion as label, 1 as ord
  from weather_dw.mart_climate__hourly_facts
)
order by ord, label
```

```sql cidades_disponiveis
select distinct
  location_id as value,
  city_name   as label
from weather_dw.mart_climate__hourly_facts
where ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
order by city_name
```

```sql datas_disponiveis
select distinct
  strftime(date, '%Y-%m-%d') as value,
  strftime(date, '%d/%m/%Y') as label
from weather_dw.mart_climate__hourly_facts
order by value desc
limit 30
```

```sql data_mais_recente
select max(strftime(date, '%Y-%m-%d')) as value
from weather_dw.mart_climate__hourly_facts
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
  defaultValue="florianopolis"
/>

<Dropdown
  name="data_ref"
  data={datas_disponiveis}
  value="value"
  label="label"
  title="Dia de referência"
  defaultValue={data_mais_recente[0]?.value}
/>

```sql perfil_hora_regiao
select
  hour                                   as hora,
  round(avg(temperature_c), 1)          as temp_media,
  round(min(temperature_c), 1)          as temp_min,
  round(max(temperature_c), 1)          as temp_max,
  round(avg(relative_humidity_pct), 1)  as umidade_media
from weather_dw.mart_climate__hourly_facts
where ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
group by hour
order by hour
```

```sql serie_dia_municipio
select
  hour                                   as hora,
  round(avg(temperature_c), 1)          as temperatura_c,
  round(avg(relative_humidity_pct), 1)  as umidade_pct,
  round(avg(precipitation_mm), 2)       as precipitacao_mm,
  round(avg(wind_speed_kmh), 1)         as vento_kmh,
  round(avg(cloud_cover_pct), 1)        as nebulosidade_pct
from weather_dw.mart_climate__hourly_facts
where ('${inputs.cidade.value}' in ('undefined', '') or location_id = '${inputs.cidade.value}')
  and (strftime(date, '%Y-%m-%d') = '${inputs.data_ref.value}' or '${inputs.data_ref.value}' in ('undefined', ''))
group by hour
order by hour
```

```sql comparativo_dia_vs_media
select
  h.hour                                                                    as hora,
  round(avg(case when strftime(h.date, '%Y-%m-%d') = '${inputs.data_ref.value}'
    then h.temperature_c end), 1)                                           as temp_dia_ref,
  round(avg(h.temperature_c), 1)                                            as temp_media_30d
from weather_dw.mart_climate__hourly_facts h
where ('${inputs.cidade.value}' in ('undefined', '') or h.location_id = '${inputs.cidade.value}')
group by h.hour
order by h.hour
```

```sql condicao_mais_frequente
select
  wmo_weather_label                      as condicao,
  count(*)                               as ocorrencias,
  round(avg(temperature_c), 1)          as temp_media,
  round(avg(relative_humidity_pct), 1)  as umidade_media
from weather_dw.mart_climate__hourly_facts
where ('${inputs.cidade.value}' in ('undefined', '') or location_id = '${inputs.cidade.value}')
group by wmo_weather_label
order by ocorrencias desc
limit 10
```

```sql mapa_temperatura_atual
select
  city_name,
  mesoregion,
  round(avg(latitude), 4)         as latitude,
  round(avg(longitude), 4)        as longitude,
  round(avg(temperature_c), 1)    as temp_media,
  round(avg(wind_speed_kmh), 1)   as vento_medio
from weather_dw.mart_climate__hourly_facts
where (strftime(date, '%Y-%m-%d') = '${inputs.data_ref.value}' or '${inputs.data_ref.value}' in ('undefined', ''))
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
group by city_name, mesoregion
```

# Análise Horária — Santa Catarina

Os dados diários mostram o que aconteceu num dia. Os dados horários mostram **como** aconteceu — o pico de calor foi às 14h ou às 16h? A umidade cai com o vento? A chuva foi pela manhã ou à noite? Esta página revela os padrões intradiários que ficam invisíveis nas médias diárias.

---

## Perfil de Temperatura por Hora do Dia

Como a temperatura varia ao longo das 24 horas na mesorregião selecionada, considerando os últimos 30 dias. A banda entre mínima e máxima revela a amplitude típica de cada hora — horas da madrugada tendem a ter banda estreita; o início da tarde, a mais larga.

<LineChart
  data={perfil_hora_regiao}
  x="hora"
  y={["temp_max", "temp_media", "temp_min"]}
  yAxisTitle="Temperatura (°C)"
  xAxisTitle="Hora do dia"
  colorPalette={["#D73027", "#FC8D59", "#4575B4"]}
  labels
/>

---

## Umidade Média por Hora do Dia

A umidade relativa segue um padrão inverso à temperatura — cai no período mais quente do dia e sobe à noite. Regiões costeiras tendem a manter umidade alta mesmo no período seco; o Oeste e o Planalto apresentam as maiores quedas diurnas.

<LineChart
  data={perfil_hora_regiao}
  x="hora"
  y="umidade_media"
  yAxisTitle="Umidade relativa (%)"
  xAxisTitle="Hora do dia"
  colorPalette={["#3182BD"]}
/>

---

## Detalhamento do Dia — {inputs.cidade.label}

Curva horária completa do município selecionado no dia de referência: temperatura, umidade, precipitação, vento e nebulosidade hora a hora.

<LineChart
  data={serie_dia_municipio}
  x="hora"
  y={["temperatura_c", "umidade_pct"]}
  yAxisTitle="Temperatura (°C) / Umidade (%)"
  xAxisTitle="Hora do dia"
  colorPalette={["#D73027", "#3182BD"]}
  labels
/>

<BarChart
  data={serie_dia_municipio}
  x="hora"
  y="precipitacao_mm"
  yAxisTitle="Precipitação (mm)"
  xAxisTitle="Hora do dia"
  colorPalette={["#08519C"]}
  title="Precipitação por hora"
/>

<LineChart
  data={serie_dia_municipio}
  x="hora"
  y={["vento_kmh", "nebulosidade_pct"]}
  yAxisTitle="Vento (km/h) / Nebulosidade (%)"
  xAxisTitle="Hora do dia"
  colorPalette={["#74ADD1", "#999999"]}
  title="Vento e Nebulosidade"
/>

---

## Dia de Referência vs Média dos Últimos 30 dias

Compara a curva de temperatura do dia selecionado com a média histórica das mesmas horas nos últimos 30 dias para o mesmo município. Permite identificar se o dia foi atipicamente quente, frio ou dentro do padrão esperado para cada período do dia.

<LineChart
  data={comparativo_dia_vs_media}
  x="hora"
  y={["temp_dia_ref", "temp_media_30d"]}
  yAxisTitle="Temperatura (°C)"
  xAxisTitle="Hora do dia"
  colorPalette={["#D73027", "#999999"]}
  labels
/>

---

## Condições Climáticas mais Frequentes — {inputs.cidade.label}

Distribuição das condições atmosféricas registradas nos últimos 30 dias com temperatura e umidade média associadas a cada condição.

<DataTable data={condicao_mais_frequente}>
  <Column id="condicao" title="Condição" />
  <Column id="ocorrencias" title="Horas registradas" />
  <Column id="temp_media" title="Temp. Média (°C)" fmt="0.0" contentType="colorscale" />
  <Column id="umidade_media" title="Umidade Média (%)" fmt="0.0" />
</DataTable>

---

## Temperatura por Município no Dia Selecionado

Mapa com a temperatura média de cada município no dia de referência, calculada sobre todas as horas disponíveis. Revela quais regiões foram mais quentes ou frias naquele dia específico.

<BubbleMap
  data={mapa_temperatura_atual}
  lat="latitude"
  long="longitude"
  size="vento_medio"
  value="temp_media"
  pointName="city_name"
  valueFmt="0.0°C"
  title="Temperatura média do dia por município (tamanho = velocidade do vento)"
/>

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Precipitação](/precipitacao) · [Alertas](/alertas)
