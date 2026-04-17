# Página 03 — Análise de Temperatura

**Ferramenta:** Evidence.dev
**Rota:** `/temperatura`
**Fonte:** `weather_dw.mart_climate__daily_facts`

---

## Storytelling

> "A temperatura é o indicador climático mais intuitivo — ela define o conforto térmico, o risco à saúde, a produção agrícola e o consumo de energia. Mas entendê-la exige mais do que saber o máximo do dia: é preciso ver *onde está quente*, *quanto varia* e *como cada município se comporta ao longo do tempo*."

Esta página conduz o usuário por três níveis de profundidade analítica, partindo do macro para o micro. Primeiro as mesorregiões de SC, depois a amplitude térmica como indicador de heterogeneidade climática, e por fim a evolução temporal de municípios específicos comparados entre si.

Santa Catarina é um caso especialmente relevante: concentra ao mesmo tempo alguns dos municípios mais frios do Brasil — como São Joaquim e Urupema — e regiões com calor intenso no Oeste e no Vale do Itajaí. Essa heterogeneidade torna a análise de amplitude térmica aqui especialmente informativa.

---

## Filtros

| Filtro | Comportamento padrão |
|--------|----------------------|
| Mesorregião | Todas as Mesorregiões |
| Mês/Ano | Mês mais recente disponível |
| Município A | Florianópolis |
| Município B | Lages |
| Município C (opcional) | Chapecó |

Os três seletores de município alimentam o comparativo de série temporal. O filtro de mesorregião limita as opções disponíveis nos três dropdowns.

---

## Componentes

### Scorecards — Resumo do Período

Cinco BigValues: temperatura máxima absoluta, mínima absoluta, média, maior amplitude do período e número de municípios que superaram 38°C.

---

### BarChart — Temperaturas Máximas por Mesorregião

Barras horizontais agrupadas com três séries por mesorregião: temperatura máxima, média e mínima. O ranking vai da mesorregião mais quente à mais fria. A distância entre a máxima e a média revela se o calor foi pontual (pico isolado) ou sustentado.

---

### BarChart + DataTable — Amplitude Térmica por Mesorregião

Barras horizontais com a amplitude térmica média de cada mesorregião. Alta amplitude indica clima mais continental — noites frias e dias quentes — com impacto direto na agricultura (risco de geada), saúde pública e infraestrutura.

A DataTable abaixo das barras exibe mínima, média, máxima e amplitude de cada mesorregião para análise exata.

---

### LineChart Duplo — Temperatura Máxima Diária por Município

Dois gráficos de linha sobrepostos no layout:

1. **Comparativo entre municípios selecionados** — até três séries com a temperatura máxima diária de cada município escolhido, permitindo identificar divergências e episódios de calor localizados.

2. **Média geral de Santa Catarina** — série cinza de referência mostrando a temperatura máxima média de todos os municípios do estado no mesmo período.
