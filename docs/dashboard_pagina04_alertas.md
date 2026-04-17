# Página 04 — Alertas Climáticos

**Ferramenta:** Evidence.dev
**Rota:** `/alertas`
**Fonte:** `weather_dw.mart_climate__alerts`

---

## Storytelling

> "Eventos climáticos extremos não são anomalias raras em Santa Catarina — geadas na Serra, chuvas torrenciais no Vale do Itajaí e ondas de calor no Oeste fazem parte do calendário. Esta página responde: *quais eventos aconteceram, onde, com que severidade, e quais valores os causaram?*"

A diferença entre dados climáticos e alertas climáticos é a **ação**. Enquanto as páginas anteriores descrevem o clima, esta identifica situações que ultrapassaram limiares definidos de risco. Cada registro não é apenas uma observação meteorológica — é um evento que acionou critérios configurados no pipeline dbt.

A página tem duplo uso: **monitoramento operacional** para acompanhar eventos recentes, e **análise histórica** para identificar padrões de risco por tipo de alerta, por mesorregião e por sazonalidade. O filtro de período permite navegar por qualquer mês desde 2021.

---

## Filtros

| Filtro | Tipo | Comportamento padrão |
|--------|------|----------------------|
| Mês/Ano | Dropdown | Mês mais recente com alertas |
| Mesorregião | Dropdown | Todas as Mesorregiões |
| Município | Dropdown | Todos (cascateado da mesorregião) |
| Tipo de Alerta | Dropdown | Todos os Tipos |
| Severidade | ButtonGroup | Todas (Crítico / Alto / Médio / Baixo) |

Os cinco filtros são aplicados em conjunto em todas as queries da página.

---

## Tipos de alerta

| Tipo | Descrição |
|------|-----------|
| `frost` | Temperatura mínima ≤ 2°C |
| `heat_anomaly` | Anomalia de temperatura > limiar configurado |
| `cold_anomaly` | Anomalia de temperatura < limiar configurado |
| `heavy_rain` | Precipitação diária acima do limiar de chuva forte |
| `precip_anomaly` | Anomalia de precipitação acima do limiar |

---

## Componentes

### Scorecards — Visão Rápida

Quatro BigValues: total de alertas, alertas críticos, alertas altos e municípios afetados no período filtrado.

---

### BarChart — Frequência por Tipo de Alerta

Barras empilhadas com quatro séries de severidade (crítico, alto, médio, baixo) para cada tipo de alerta. Revela qual fenômeno extremo foi mais frequente no período e qual a distribuição de severidade dentro de cada tipo.

Paleta: vermelho (crítico) → laranja → amarelo → verde claro (baixo).

---

### BarChart — Alertas por Mesorregião e Severidade

Barras horizontais empilhadas mostrando o volume total de alertas por mesorregião de SC, com mesma segmentação de severidade. Identifica quais sub-regiões acumulam mais eventos e se o risco é volumoso (muitos alertas leves) ou concentrado (poucos alertas críticos).

---

### DataTable — Detalhamento dos Eventos

Tabela paginada (20 linhas) com busca livre. Cada linha é um evento extremo com:
- Data, Município, Mesorregião, Tipo de Alerta, Severidade
- Temperatura máx/mín, Anomalia de temperatura, Precipitação, Vento máx, UV máx

Ordenada por data decrescente. Permite auditar a origem de cada alerta e validar se os limiares do pipeline estão gerando alertas coerentes com os valores observados.
