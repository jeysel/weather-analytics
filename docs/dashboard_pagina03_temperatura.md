# Página 03 — Análise de Temperatura

**Relatório:** Weather Analytics — Looker Studio
**Fonte:** `weather_dw.marts.mart_climate__daily_facts`

---

## Storytelling

> "A temperatura é o indicador climático mais intuitivo — ela define o conforto térmico, o risco à saúde, a produção agrícola e o consumo de energia. Mas entendê-la exige mais do que saber o máximo do dia: é preciso ver *onde está quente*, *quanto varia* e *como cada município se comporta ao longo do tempo*."

Esta página conduz o usuário por três níveis de profundidade analítica, partindo do macro para o micro. Primeiro o estado e a região, depois a variação interna entre municípios, e por fim a evolução temporal de localidades específicas. Cada nível responde uma pergunta diferente e acrescenta uma camada de contexto sobre a anterior.

Santa Catarina é um caso especialmente interessante para análise de temperatura: o estado concentra ao mesmo tempo alguns dos municípios mais frios do Brasil — como São Joaquim e Urupema — e regiões com calor intenso no Oeste e no Vale do Itajaí. Essa heterogeneidade é o que torna a análise de amplitude térmica tão relevante aqui.

---

### Ranking de Temperaturas Máximas por Região

O ranking por região ou mesorregio é o ponto de partida: quais áreas de Santa Catarina registraram os maiores picos de calor? A distância entre a temperatura máxima e a média de cada região revela se o calor foi pontual — um dia de pico isolado — ou se representou um período sustentado de temperaturas elevadas.

---

### Amplitude Térmica por Região

A amplitude térmica — diferença entre máxima e mínima no período — é o indicador de heterogeneidade climática interna. Regiões com alta amplitude possuem clima mais continental: noites frias e dias quentes, com grande variação ao longo das horas. A Serra Catarinense, por exemplo, costuma apresentar as maiores amplitudes do estado.

Essa informação tem impacto direto na agricultura (risco de geada em noites frias mesmo após dias quentes), na saúde pública (estresse térmico) e no planejamento de infraestrutura urbana.

---

### Série Temporal Comparativa por Município

A série temporal comparativa é o nível mais detalhado da página. Com ela, o usuário pode selecionar municípios específicos e comparar lado a lado como a temperatura máxima diária evoluiu ao longo do período. É possível identificar divergências entre municípios próximos, detectar episódios de calor intenso localizados, e acompanhar se a tendência de um município está subindo ou caindo em relação aos seus vizinhos e à média geral do estado.
