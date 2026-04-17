---
title: Análise de Precipitação
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

<ButtonGroup name="classe" title="Intensidade de Chuva">
    <ButtonGroupItem valueLabel="Todas" value="Todas" default />
    <ButtonGroupItem valueLabel="Seco" value="dry" />
    <ButtonGroupItem valueLabel="Leve" value="light" />
    <ButtonGroupItem valueLabel="Moderado" value="moderate" />
    <ButtonGroupItem valueLabel="Forte" value="heavy" />
    <ButtonGroupItem valueLabel="Extremo" value="extreme" />
</ButtonGroup>

```sql scorecards
select
  round(sum(precipitation_mm), 1)                                           as precip_total_mm,
  round(avg(precip_anomaly_mm), 1)                                          as anomalia_media_mm,
  count(*) filter (where precipitation_mm > 0)                              as dias_com_chuva,
  count(distinct city_name) filter (where precipitation_class = 'extreme')  as municipios_extremo
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
  and ('${inputs.classe.value}'  in ('Todas', 'undefined', '') or precipitation_class = '${inputs.classe.value}')
```

```sql precip_por_municipio
select
  city_name,
  round(sum(precipitation_mm), 1)                                as acumulado_mm,
  round(avg(precip_anomaly_mm), 1)                               as anomalia_media_mm,
  count(*) filter (where precipitation_mm > 0)                   as dias_com_chuva,
  count(*) filter (where precipitation_class = 'heavy')          as dias_forte,
  count(*) filter (where precipitation_class = 'extreme')        as dias_extremo
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
  and ('${inputs.classe.value}'  in ('Todas', 'undefined', '') or precipitation_class = '${inputs.classe.value}')
group by city_name
order by acumulado_mm desc
```

```sql media_estadual
select
  round(avg(acumulado_mm), 1) as media_sc_mm
from (
  select
    city_name,
    sum(precipitation_mm) as acumulado_mm
  from weather_dw.mart_climate__daily_facts
  where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
    and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
    and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
  group by city_name
)
```

```sql heatmap_intensidade
select
  strftime(date, '%d/%m')                                        as dia,
  date,
  count(*) filter (where precipitation_class = 'dry')            as seco,
  count(*) filter (where precipitation_class = 'light')          as leve,
  count(*) filter (where precipitation_class = 'moderate')       as moderado,
  count(*) filter (where precipitation_class = 'heavy')          as forte,
  count(*) filter (where precipitation_class = 'extreme')        as extremo
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
group by date, dia
order by date
```

```sql distribuicao_classes
select
  precipitation_class                                                      as classe,
  count(*)                                                                 as registros,
  round(100.0 * count(*) / sum(count(*)) over (), 1)                      as percentual
from weather_dw.mart_climate__daily_facts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'  in ('Todas', 'undefined', '') or location_id = '${inputs.cidade.value}')
  and ('${inputs.classe.value}'  in ('Todas', 'undefined', '') or precipitation_class = '${inputs.classe.value}')
group by precipitation_class
order by
  case precipitation_class
    when 'dry'      then 1
    when 'light'    then 2
    when 'moderate' then 3
    when 'heavy'    then 4
    when 'extreme'  then 5
  end
```

# Análise de Precipitação — Santa Catarina

Das enchentes no Vale do Itajaí ao déficit hídrico no Oeste, a chuva é o fenômeno com maior impacto direto na vida da população catarinense. Esta página responde três perguntas em sequência: **onde choveu mais, quando choveu, e com que intensidade?**

A leitura conjunta dessas três dimensões revela algo que nenhuma isolada consegue — o *perfil* da chuva no período. Um mês com chuvas concentradas em dois dias intensos e um mês com chuvas distribuídas podem ter o mesmo total acumulado, mas consequências completamente diferentes para drenagem, agricultura e risco de desastre.

---

<BigValue
  data={scorecards}
  value="precip_total_mm"
  title="Precipitação Total"
  fmt="0.0mm"
/>
<BigValue
  data={scorecards}
  value="anomalia_media_mm"
  title="Anomalia Média"
  fmt="+0.0;-0.0mm"
/>
<BigValue
  data={scorecards}
  value="dias_com_chuva"
  title="Dias com Chuva"
/>
<BigValue
  data={scorecards}
  value="municipios_extremo"
  title="Municípios com Chuva Extrema"
/>

---

## Precipitação Acumulada por Município

Municípios ordenados do mais chuvoso ao mais seco no período. A linha de referência marca a média estadual — barras acima indicam municípios com precipitação extraordinária; abaixo, comportamento mais seco que o padrão de Santa Catarina no mesmo período.

<BarChart
  data={precip_por_municipio}
  x="city_name"
  y="acumulado_mm"
  yAxisTitle="Precipitação acumulada (mm)"
  swapXY=true
  colorPalette={["#3182BD"]}
  referenceLine={media_estadual[0].media_sc_mm}
  referenceLineLabel="Média SC"
/>

---

## Quando Choveu — Intensidade por Dia

Cada linha é um dia do mês. As colunas mostram quantos municípios registraram cada intensidade de chuva naquele dia. Dias com muitos municípios em **forte** ou **extremo** sinalizam eventos generalizados — o tipo de situação que sobrecarrega sistemas de drenagem em todo o estado. Dias isolados com cores intensas revelam eventos localizados.

<DataTable data={heatmap_intensidade} rows=31>
  <Column id="dia" title="Dia" />
  <Column id="seco" title="Seco" contentType="colorscale" colorScale="negative" />
  <Column id="leve" title="Leve" contentType="colorscale" />
  <Column id="moderado" title="Moderado" contentType="colorscale" />
  <Column id="forte" title="Forte" contentType="colorscale" />
  <Column id="extremo" title="Extremo" contentType="colorscale" />
</DataTable>

---

## Perfil do Período — Distribuição por Intensidade

Qual foi o perfil dominante das chuvas no mês? Um perfil saudável tem predominância de dias `seco` e `leve`. Uma fatia relevante de `forte` ou `extremo` indica que as chuvas não foram apenas volumosas, mas concentradas em eventos de alta intensidade — o que eleva o risco independentemente do total acumulado.

<BarChart
  data={distribuicao_classes}
  x="classe"
  y="percentual"
  yAxisTitle="% dos dias (município × dia)"
  labels
  colorPalette={["#F5F5F5", "#DEEBF7", "#9ECAE1", "#3182BD", "#08519C"]}
/>

<DataTable data={distribuicao_classes}>
  <Column id="classe" title="Intensidade" />
  <Column id="registros" title="Registros" />
  <Column id="percentual" title="%" fmt="0.0" contentType="colorscale" />
</DataTable>

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Alertas](/alertas) · [Horário](/horario)
