# Dashboards — Weather Analytics

Documentação dos dashboards interativos construídos em Evidence.dev a partir dos marts do dbt (BigQuery). Publicados automaticamente via GitHub Actions no GitHub Pages.

---

## Visão geral

Os dashboards transformam os dados climáticos coletados de 295 municípios de Santa Catarina em inteligência visual acessível. A audiência inclui analistas de dados, gestores públicos e pesquisadores interessados em padrões climáticos regionais e eventos extremos.

Os dados são atualizados diariamente pelo pipeline Airflow → BigQuery → dbt → Evidence.dev.

---

## Fontes de dados

| Mart | Granularidade | Período |
|------|---------------|---------|
| `weather_dw.mart_climate__daily_facts` | 1 linha por município × dia | Últimos 12 meses |
| `weather_dw.mart_climate__hourly_facts` | 1 linha por município × hora | Últimos 30 dias |
| `weather_dw.mart_climate__alerts` | 1 linha por evento extremo | Histórico completo |

---

## Páginas do relatório

### Página 01 — Visão Geral Climática (`/`)

Panorama executivo do clima em SC. Scorecards de temperatura e precipitação, série temporal com anomalia histórica e mapa de bolhas por município.

[dashboard_pagina01_visao_geral.md](dashboard_pagina01_visao_geral.md)

---

### Página 02 — Análise de Precipitação (`/precipitacao`)

Foco em chuvas: onde choveu mais, quando choveu, e com que intensidade. Diferencia meses com eventos pontuais intensos de meses com chuvas regulares distribuídas.

[dashboard_pagina02_precipitacao.md](dashboard_pagina02_precipitacao.md)

---

### Página 03 — Análise de Temperatura (`/temperatura`)

Exploração da distribuição e variação das temperaturas em SC. Ranking por mesorregião, amplitude térmica e comparativo diário entre até três municípios.

[dashboard_pagina03_temperatura.md](dashboard_pagina03_temperatura.md)

---

### Página 04 — Alertas Climáticos (`/alertas`)

Monitoramento de eventos extremos com rastreabilidade completa. Frequência por tipo, distribuição por mesorregião e tabela detalhada de cada ocorrência.

[dashboard_pagina04_alertas.md](dashboard_pagina04_alertas.md)

---

### Página 05 — Análise Horária (`/horario`)

Padrões intradiários de temperatura, umidade, vento e precipitação hora a hora. Perfil médio das 24h por mesorregião e detalhamento de um dia específico por município.

[dashboard_pagina05_horario.md](dashboard_pagina05_horario.md)

---

### Página de Detalhe — Cidade (`/cidades/[cidade]`)

Drill-down completo por município: série temporal mensal, precipitação diária, anomalia de temperatura, risco UV e alertas do período.

---

## Filtros e interatividade

Todas as páginas são interativas via filtros encadeados:

| Filtro | Tipo | Comportamento |
|--------|------|---------------|
| Mesorregião | Dropdown | Filtra municípios disponíveis na sequência |
| Município | Dropdown | Cascateado da mesorregião |
| Mês/Ano | Dropdown | Seleção do período; padrão = mês mais recente |
| Severidade / Intensidade | ButtonGroup | Filtragem por categoria |

---

## Links

- Dashboard ao vivo: [GitHub Pages](https://jeysel.github.io/Analytics-Engineer/Weather-Analytics/)
- Repositório: [Weather-Analytics](../README.md)
- Arquitetura: [architecture.md](architecture.md)
