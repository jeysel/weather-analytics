---
title: Alertas Climáticos
---

```sql alertas_recentes
select
  date,
  city_name,
  state_name,
  region,
  alert_type,
  severity,
  temp_max_c,
  temp_min_c,
  temp_anomaly_c,
  precipitation_mm,
  wind_speed_max_kmh,
  uv_index_max
from weather_dw.mart_climate__alerts
where date >= current_date - interval '30 days'
order by date desc, severity desc
```

```sql contagem_por_tipo
select
  alert_type                                        as tipo_alerta,
  count(*)                                          as total,
  count(*) filter (where severity = 'critical')                    as criticos,
  count(*) filter (where severity = 'high')                        as altos,
  count(*) filter (where severity = 'medium')                      as medios,
  count(*) filter (where severity = 'low')                         as baixos
from weather_dw.mart_climate__alerts
where date >= current_date - interval '30 days'
group by alert_type
order by total desc
```

```sql contagem_por_severidade
with severidades as (
  select 'critical' as severidade, 1 as ord union all
  select 'high',   2 union all
  select 'medium', 3 union all
  select 'low',    4
),
atual as (
  select severity as severidade, count(*) as total
  from weather_dw.mart_climate__alerts
  where date >= current_date - interval '30 days'
    and alert_type != '__no_alerts__'
  group by severity
)
select s.severidade, coalesce(a.total, 0) as total
from severidades s
left join atual a on s.severidade = a.severidade
order by s.ord
```

```sql historico_alertas_diario
select
  date,
  count(*)                                          as total_alertas,
  count(*) filter (where severity = 'critical')                    as criticos,
  count(*) filter (where severity = 'high')                        as altos
from weather_dw.mart_climate__alerts
where date >= current_date - interval '60 days'
group by date
order by date
```

```sql cidades_mais_alertas
select
  city_name,
  state_name,
  region,
  count(*)                                          as total_alertas,
  count(*) filter (where severity = 'critical')                    as criticos,
  string_agg(distinct alert_type, ', ')             as tipos_detectados
from weather_dw.mart_climate__alerts
where date >= current_date - interval '30 days'
group by city_name, state_name, region
order by total_alertas desc
limit 15
```

```sql alertas_criticos
select
  date,
  city_name,
  state_name,
  alert_type,
  temp_max_c,
  precipitation_mm,
  wind_speed_max_kmh,
  uv_index_max
from weather_dw.mart_climate__alerts
where severity = 'critical'
  and date >= current_date - interval '30 days'
order by date desc
```

# Alertas Climáticos

Eventos climáticos extremos detectados nos **últimos 30 dias**.

<BigValue
  data={contagem_por_severidade}
  value="total"
  title="Alertas Críticos"
  filter="severidade = 'critical'"
/>
<BigValue
  data={contagem_por_severidade}
  value="total"
  title="Alertas Altos"
  filter="severidade = 'high'"
/>
<BigValue
  data={contagem_por_severidade}
  value="total"
  title="Alertas Médios"
  filter="severidade = 'medium'"
/>

---

## Evolução Diária de Alertas

{#if historico_alertas_diario.length > 0}

<AreaChart
  data={historico_alertas_diario}
  x="date"
  y={["criticos", "altos", "total_alertas"]}
  yAxisTitle="Número de alertas"
  title="Alertas por dia (últimos 60 dias)"
  xFmt="dd/MM/yyyy"
/>

{:else}

> Nenhum alerta nos últimos 60 dias.

{/if}

---

## Alertas por Tipo

{#if contagem_por_tipo.length > 0}

<BarChart
  data={contagem_por_tipo}
  x="tipo_alerta"
  y={["criticos", "altos", "medios", "baixos"]}
  yAxisTitle="Ocorrências"
  title="Breakdown por severidade dentro de cada tipo"
  type="stacked"
/>

{:else}

> Nenhum alerta por tipo nos últimos 30 dias.

{/if}

---

## Cidades com Mais Alertas

{#if cidades_mais_alertas.length > 0}

<DataTable data={cidades_mais_alertas}>
  <Column id="city_name" title="Cidade" />
  <Column id="state_name" title="UF" />
  <Column id="region" title="Região" />
  <Column id="total_alertas" title="Total" />
  <Column id="criticos" title="Críticos" contentType="colorscale" />
  <Column id="tipos_detectados" title="Tipos Detectados" />
</DataTable>

{:else}

> Nenhuma cidade com alertas nos últimos 30 dias.

{/if}

---

## Alertas Críticos — Detalhes

{#if alertas_criticos.length > 0}

<DataTable data={alertas_criticos} rows=20>
  <Column id="date" title="Data" fmt="dd/MM/yyyy" />
  <Column id="city_name" title="Cidade" />
  <Column id="state_name" title="Estado" />
  <Column id="alert_type" title="Tipo de Alerta" />
  <Column id="temp_max_c" title="Temp. Máx (°C)" fmt="0.0" />
  <Column id="precipitation_mm" title="Precip. (mm)" fmt="0.0" />
  <Column id="wind_speed_max_kmh" title="Vento (km/h)" fmt="0.0" />
  <Column id="uv_index_max" title="UV Máx" fmt="0.0" />
</DataTable>

{:else}

> Nenhum alerta crítico nos últimos 30 dias.

{/if}

---

## Todos os Alertas Recentes

{#if alertas_recentes.length > 0}

<DataTable data={alertas_recentes} rows=30 search=true>
  <Column id="date" title="Data" fmt="dd/MM/yyyy" />
  <Column id="city_name" title="Cidade" />
  <Column id="region" title="Região" />
  <Column id="alert_type" title="Tipo" />
  <Column id="severity" title="Severidade" contentType="colorscale" />
  <Column id="temp_max_c" title="Temp. Máx" fmt="0.0" />
  <Column id="precipitation_mm" title="Precip." fmt="0.0mm" />
  <Column id="wind_speed_max_kmh" title="Vento" fmt="0.0 km/h" />
</DataTable>

{:else}

> Nenhum alerta recente nos últimos 30 dias.

{/if}

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Precipitação](/precipitacao)
