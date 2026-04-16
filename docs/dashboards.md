# Dashboards — Weather Analytics

Documentação do relatório criado no Looker Studio a partir dos marts do dbt (BigQuery).

---

## Visão geral

Os dashboards transformam os dados climáticos coletados de 295 municípios de Santa Catarina em inteligência visual acessível. A audiência inclui analistas de dados, gestores públicos e pesquisadores interessados em padrões climáticos regionais e eventos extremos.

Os dados são atualizados diariamente pelo pipeline Airflow → BigQuery → dbt.

---

## Fontes de dados

| Mart | Granularidade |
|------|---------------|
| `weather_dw.marts.mart_climate__daily_facts` | 1 linha por município × dia |
| `weather_dw.marts.mart_climate__hourly_facts` | 1 linha por município × hora |
| `weather_dw.marts.mart_climate__alerts` | 1 linha por evento extremo |

---

## Páginas do relatório

### Página 01 — Visão Geral Climática

Panorama executivo do clima em SC. O usuário vê em segundos como estão a temperatura e a precipitação no período, se o comportamento está dentro do normal histórico, e quais municípios se destacam espacialmente no mapa.

[dashboard_pagina01_visao_geral.md](dashboard_pagina01_visao_geral.md)

---

### Página 02 — Análise de Precipitação

Foco em chuvas: onde choveu mais, quando choveu, e com que intensidade. A página diferencia meses com eventos pontuais intensos de meses com chuvas regulares distribuídas — mesmo quando o volume total acumulado é similar.

[dashboard_pagina02_precipitacao.md](dashboard_pagina02_precipitacao.md)

---

### Página 03 — Análise de Temperatura

Exploração da distribuição e variação das temperaturas em SC. A narrativa vai do macro (ranking por região) para o micro (evolução diária por município), passando pela amplitude térmica como indicador de heterogeneidade climática interna.

[dashboard_pagina03_temperatura.md](dashboard_pagina03_temperatura.md)

---

### Página 04 — Alertas Climáticos

Monitoramento de eventos extremos com rastreabilidade completa. A página serve tanto para acompanhamento operacional de curto prazo quanto para análise histórica de padrões de risco por tipo de evento e por região.

[dashboard_pagina04_alertas.md](dashboard_pagina04_alertas.md)

---

## Links

- Relatório Looker Studio: ****
- Repositório: [Weather-Analytics](../README.md)
- Arquitetura: [architecture.md](architecture.md)
