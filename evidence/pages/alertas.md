---
title: Alertas Climáticos
---

```sql periodos_disponiveis
select distinct
  year_month as value,
  year_month as label
from weather_dw.mart_climate__alerts
where alert_type != '__no_alerts__'
order by value desc
limit 24
```

```sql periodo_mais_recente
select max(year_month) as value
from weather_dw.mart_climate__alerts
where alert_type != '__no_alerts__'
```

```sql mesorregioes
select value, label from (
  select 'Todas' as value, 'Todas as Mesorregiões' as label, 0 as ord
  union all
  select distinct mesoregion as value, mesoregion as label, 1 as ord
  from weather_dw.mart_climate__alerts
  where alert_type != '__no_alerts__'
)
order by ord, label
```

```sql cidades_disponiveis
select value, label from (
  select 'Todas' as value, 'Todos os Municípios' as label, 0 as ord
  union all
  select distinct city_name as value, city_name as label, 1 as ord
  from weather_dw.mart_climate__alerts
  where alert_type != '__no_alerts__'
    and ('${inputs.mesoregiao.value}' in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
)
order by ord, label
```

```sql tipos_alerta
select value, label from (
  select 'Todos' as value, 'Todos os Tipos' as label, 0 as ord
  union all
  select distinct alert_type as value, alert_type as label, 1 as ord
  from weather_dw.mart_climate__alerts
  where alert_type != '__no_alerts__'
)
order by ord, label
```

```sql severidades
select value, label from (
  select 'Todas'    as value, 'Todas as Severidades' as label, 0 as ord
  union all
  select 'critical' as value, 'Crítico'              as label, 1 as ord
  union all
  select 'high'     as value, 'Alto'                 as label, 2 as ord
  union all
  select 'medium'   as value, 'Médio'                as label, 3 as ord
  union all
  select 'low'      as value, 'Baixo'                as label, 4 as ord
)
order by ord
```

<Dropdown
  name="ano_mes"
  data={periodos_disponiveis}
  value="value"
  label="label"
  title="Mês/Ano"
  defaultValue={periodo_mais_recente[0]?.value}
/>

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
  name="tipo_alerta"
  data={tipos_alerta}
  value="value"
  label="label"
  title="Tipo de Alerta"
  defaultValue="Todos"
/>

<ButtonGroup name="severidade" title="Severidade">
    <ButtonGroupItem valueLabel="Todas" value="Todas" default />
    <ButtonGroupItem valueLabel="Crítico" value="critical" />
    <ButtonGroupItem valueLabel="Alto" value="high" />
    <ButtonGroupItem valueLabel="Médio" value="medium" />
    <ButtonGroupItem valueLabel="Baixo" value="low" />
</ButtonGroup>

```sql scorecards
select
  count(*)                                               as total_alertas,
  count(*) filter (where severity = 'critical')          as criticos,
  count(*) filter (where severity = 'high')              as altos,
  count(distinct city_name)                              as municipios_afetados
from weather_dw.mart_climate__alerts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and alert_type != '__no_alerts__'
  and ('${inputs.mesoregiao.value}'  in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'      in ('Todas', 'undefined', '') or city_name  = '${inputs.cidade.value}')
  and ('${inputs.tipo_alerta.value}' in ('Todos', 'undefined', '') or alert_type = '${inputs.tipo_alerta.value}')
  and ('${inputs.severidade.value}'  in ('Todas', 'undefined', '') or severity   = '${inputs.severidade.value}')
```

```sql frequencia_por_tipo
select
  alert_type                                             as tipo,
  count(*) filter (where severity = 'critical')          as critico,
  count(*) filter (where severity = 'high')              as alto,
  count(*) filter (where severity = 'medium')            as medio,
  count(*) filter (where severity = 'low')               as baixo,
  count(*)                                               as total
from weather_dw.mart_climate__alerts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and alert_type != '__no_alerts__'
  and ('${inputs.mesoregiao.value}'  in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'      in ('Todas', 'undefined', '') or city_name  = '${inputs.cidade.value}')
  and ('${inputs.tipo_alerta.value}' in ('Todos', 'undefined', '') or alert_type = '${inputs.tipo_alerta.value}')
  and ('${inputs.severidade.value}'  in ('Todas', 'undefined', '') or severity   = '${inputs.severidade.value}')
group by alert_type
order by total desc
```

```sql alertas_por_regiao
select
  mesoregion                                             as regiao,
  count(*) filter (where severity = 'critical')          as critico,
  count(*) filter (where severity = 'high')              as alto,
  count(*) filter (where severity = 'medium')            as medio,
  count(*) filter (where severity = 'low')               as baixo,
  count(*)                                               as total
from weather_dw.mart_climate__alerts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and alert_type != '__no_alerts__'
  and ('${inputs.mesoregiao.value}'  in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'      in ('Todas', 'undefined', '') or city_name  = '${inputs.cidade.value}')
  and ('${inputs.tipo_alerta.value}' in ('Todos', 'undefined', '') or alert_type = '${inputs.tipo_alerta.value}')
  and ('${inputs.severidade.value}'  in ('Todas', 'undefined', '') or severity   = '${inputs.severidade.value}')
group by mesoregion
order by total desc
```

```sql tabela_eventos
select
  date,
  city_name,
  mesoregion,
  alert_type,
  severity,
  temp_max_c,
  temp_min_c,
  temp_anomaly_c,
  precipitation_mm,
  wind_speed_max_kmh,
  uv_index_max
from weather_dw.mart_climate__alerts
where (year_month = '${inputs.ano_mes.value}' or length('${inputs.ano_mes.value}') != 7)
  and alert_type != '__no_alerts__'
  and ('${inputs.mesoregiao.value}'  in ('Todas', 'undefined', '') or mesoregion = '${inputs.mesoregiao.value}')
  and ('${inputs.cidade.value}'      in ('Todas', 'undefined', '') or city_name  = '${inputs.cidade.value}')
  and ('${inputs.tipo_alerta.value}' in ('Todos', 'undefined', '') or alert_type = '${inputs.tipo_alerta.value}')
  and ('${inputs.severidade.value}'  in ('Todas', 'undefined', '') or severity   = '${inputs.severidade.value}')
order by date desc, severity
```

# Alertas Climáticos — Santa Catarina

Geadas na Serra, chuvas torrenciais no Vale do Itajaí e ondas de calor no Oeste fazem parte do calendário catarinense. Esta página responde: **quais eventos aconteceram, onde, com que severidade, e quais valores os causaram?**

A diferença entre dados climáticos e alertas climáticos é a **ação**. Enquanto as páginas anteriores descrevem o clima, esta identifica situações que ultrapassaram limiares definidos de risco. A página serve ao analista que quer entender padrões históricos e ao gestor que precisa acompanhar eventos recentes — basta ajustar o filtro de período.

---

<BigValue
  data={scorecards}
  value="total_alertas"
  title="Total de Alertas"
/>
<BigValue
  data={scorecards}
  value="criticos"
  title="Alertas Críticos"
/>
<BigValue
  data={scorecards}
  value="altos"
  title="Alertas Altos"
/>
<BigValue
  data={scorecards}
  value="municipios_afetados"
  title="Municípios Afetados"
/>

---

## Frequência por Tipo de Alerta

Qual fenômeno extremo foi mais frequente no período? Em Santa Catarina, a distribuição entre `frost`, `heavy_rain` e `heat_anomaly` varia bastante por estação — este gráfico torna essa sazonalidade visível e comparável entre períodos.

<BarChart
  data={frequencia_por_tipo}
  x="tipo"
  y={["critico", "alto", "medio", "baixo"]}
  yAxisTitle="Ocorrências"
  type="stacked"
  colorPalette={["#B2182B", "#EF8A62", "#FDD49E", "#D9F0D3"]}
  labels
/>

---

## Alertas por Região e Severidade

Algumas regiões acumulam muitos alertas de baixa severidade; outras registram poucos eventos mas predominantemente críticos. Essa distinção é essencial para priorizar atenção — volume alto nem sempre significa risco alto.

<BarChart
  data={alertas_por_regiao}
  x="regiao"
  y={["critico", "alto", "medio", "baixo"]}
  yAxisTitle="Número de alertas"
  type="stacked"
  swapXY=true
  colorPalette={["#B2182B", "#EF8A62", "#FDD49E", "#D9F0D3"]}
/>

---

## Detalhamento dos Eventos

Cada linha é um evento climático extremo com os valores exatos que acionaram o alerta. Use esta tabela para verificar a origem de cada alerta, investigar casos específicos ou validar se os limiares do pipeline estão gerando alertas coerentes com a realidade observada.

<DataTable data={tabela_eventos} rows=20 search=true>
  <Column id="date" title="Data" fmt="dd/MM/yyyy" />
  <Column id="city_name" title="Município" />
  <Column id="mesoregion" title="Região" />
  <Column id="alert_type" title="Tipo de Alerta" />
  <Column id="severity" title="Severidade" contentType="colorscale" />
  <Column id="temp_max_c" title="Temp. Máx (°C)" fmt="0.0" contentType="colorscale" />
  <Column id="temp_min_c" title="Temp. Mín (°C)" fmt="0.0" />
  <Column id="temp_anomaly_c" title="Anomalia (°C)" fmt="+0.0;-0.0" contentType="colorscale" />
  <Column id="precipitation_mm" title="Precip. (mm)" fmt="0.0" contentType="colorscale" />
  <Column id="wind_speed_max_kmh" title="Vento (km/h)" fmt="0.0" />
  <Column id="uv_index_max" title="UV Máx" fmt="0" />
</DataTable>

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Precipitação](/precipitacao) · [Horário](/horario)
