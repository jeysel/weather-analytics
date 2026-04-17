# Página 02 — Análise de Precipitação

**Ferramenta:** Evidence.dev
**Rota:** `/precipitacao`
**Fonte:** `weather_dw.mart_climate__daily_facts`

---

## Storytelling

> "A chuva é o fenômeno climático com maior impacto direto na vida da população catarinense — das enchentes no Vale do Itajaí ao déficit hídrico no Oeste. Esta página responde três perguntas em sequência: *onde choveu mais, quando choveu, e com que intensidade?*"

A leitura conjunta dessas três dimensões revela algo que nenhuma isolada consegue — o *perfil* da chuva no período. Um mês com chuvas concentradas em dois dias intensos e um mês com chuvas distribuídas podem ter o mesmo total acumulado, mas consequências completamente diferentes para drenagem, agricultura e risco de desastre.

---

## Filtros

| Filtro | Comportamento padrão |
|--------|----------------------|
| Mesorregião | Todas as Mesorregiões |
| Município | Todos os Municípios (cascateado) |
| Mês/Ano | Mês mais recente disponível |
| Intensidade de Chuva | Todas (ButtonGroup: Seco / Leve / Moderado / Forte / Extremo) |

---

## Componentes

### Scorecards — Resumo do Período

Quatro BigValues: precipitação total (mm), anomalia média (mm), dias com chuva e municípios com chuva extrema.

---

### BarChart — Precipitação Acumulada por Município

Barras horizontais ordenadas do município mais chuvoso ao mais seco. Uma linha de referência marca a média estadual — barras acima indicam comportamento extraordinário; abaixo, comportamento mais seco que o padrão de Santa Catarina no mesmo período.

---

### DataTable (Heatmap de Intensidade) — Quando Choveu

Tabela com colorscale onde cada linha é um dia do mês e as colunas mostram quantos municípios registraram cada intensidade (`seco`, `leve`, `moderado`, `forte`, `extremo`). Dias com muitos municípios em `forte` ou `extremo` sinalizam eventos generalizados. Dias isolados com valores altos revelam eventos localizados.

---

### BarChart — Distribuição por Classe de Precipitação

Barras por categoria de intensidade mostrando o percentual de ocorrências. Um perfil saudável tem predominância de `seco` e `leve`. Uma fatia relevante de `forte` ou `extremo` indica que as chuvas não foram apenas volumosas, mas concentradas em eventos de alta intensidade.

Acompanhado por DataTable com registros e percentual por classe.
