# Página 04 — Alertas Climáticos

**Relatório:** Weather Analytics — Looker Studio
**Fonte:** `weather_dw.marts.mart_climate__alerts`

---

## Storytelling

> "Eventos climáticos extremos não são anomalias raras em Santa Catarina — geadas na Serra, chuvas torrenciais no Vale do Itajaí e ondas de calor no Oeste fazem parte do calendário. Esta página responde: *quais eventos aconteceram, onde, com que severidade, e quais valores os causaram?*"

A diferença entre dados climáticos e alertas climáticos é a **ação**. Enquanto as páginas anteriores descrevem o clima, esta página identifica situações que exigem atenção. Cada registro aqui não é apenas uma observação meteorológica — é um evento que ultrapassou um limiar definido de risco.

A página tem duplo uso: **monitoramento operacional** para acompanhar eventos recentes nas últimas horas ou dias, e **análise histórica** para identificar padrões de risco por tipo de evento, por região e por sazonalidade. O mesmo dashboard serve ao analista que quer entender o passado e ao gestor que precisa agir no presente.

---

### Scorecards — Visão Rápida dos Alertas

Os cartões de total de alertas, alertas críticos, alertas de alta severidade e municípios afetados são a primeira leitura da página. Eles respondem em segundos se o período foi calmo ou crítico — e se os eventos concentraram-se em poucos municípios ou se espalharam pelo estado.

---

### Barras — Frequência por Tipo de Alerta

O gráfico de barras por tipo de alerta revela qual fenômeno extremo é mais frequente no período analisado. Em Santa Catarina, a distribuição entre `frost`, `heavy_rain` e `heat_anomaly` costuma variar bastante conforme a estação — esse gráfico torna essa sazonalidade visível e comparável entre períodos.

---

### Barras Empilhadas — Alertas por Região e Severidade

A distribuição geográfica dos alertas, segmentada por severidade, responde onde os eventos são mais perigosos. Algumas regiões podem ter muitos alertas de baixa severidade; outras, poucos alertas mas predominantemente críticos. Essa distinção é essencial para priorização de recursos e atenção.

---

### Tabela — Rastreabilidade dos Eventos

A tabela é a camada de auditoria da página. Cada linha é um evento climático extremo com os valores exatos que acionaram o alerta — temperatura, precipitação, vento, UV e anomalia. Ela permite ao analista verificar a origem de cada alerta, investigar casos específicos e validar se os limiares configurados no pipeline estão gerando alertas coerentes com a realidade observada.
