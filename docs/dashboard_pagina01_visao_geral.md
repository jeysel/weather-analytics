# Página 01 — Visão Geral Climática

**Relatório:** Weather Analytics — Looker Studio
**Fonte:** `weather_dw.marts.mart_climate__daily_facts`

---

## Storytelling

> "Santa Catarina possui um dos climas mais variados do Brasil — serras frias, litoral úmido e planaltos com amplitudes extremas coexistem no mesmo estado. Esta página responde uma pergunta simples: *como está o clima hoje, comparado ao que é esperado para esta época?*"

O usuário chega nesta página buscando um resumo rápido. Em segundos, ele deve conseguir identificar se a temperatura atual está dentro ou fora do padrão histórico recente, se o mês está mais chuvoso ou mais seco que o normal, e quais regiões ou municípios estão com comportamento atípico.

A narrativa evolui do **geral para o específico**: primeiro os números agregados nos scorecards, depois a tendência no tempo pela série temporal, e por fim a distribuição espacial no mapa.

---

### Scorecards — Resumo do Período

Os cartões de temperatura máxima, mínima, média e precipitação acumulada no mês são o ponto de entrada da página. Antes de qualquer gráfico, o usuário calibra sua leitura com os números absolutos do período. Não há interpretação necessária — os valores falam sozinhos.

---

### Série Temporal — Temperatura Média e Anomalia

O gráfico de linhas duplas é onde a história climática ganha profundidade. A linha de temperatura média diária mostra o que aconteceu; a linha de anomalia mostra o que isso *significa* — se aquele dia foi mais quente ou mais frio do que o esperado com base na média dos últimos 30 dias.

Valores positivos de anomalia indicam dias acima da normalidade histórica; valores negativos, abaixo. Essa leitura paralela transforma um número bruto em contexto, respondendo não só "qual foi a temperatura" mas "foi um dia comum ou excepcional?".

---

### Mapa Coroplético — Distribuição Espacial da Temperatura

O mapa completa o que a série temporal não consegue mostrar: *onde* está mais quente ou está mais frio. Santa Catarina tem contrastes geográficos marcantes — a Serra Catarinense pode registrar temperaturas negativas enquanto o litoral sul permanece ameno. O mapa torna esse contraste imediatamente visível, com o tamanho dos pontos representando a amplitude térmica de cada município — quão diferente foi o dia entre sua temperatura máxima e mínima.
