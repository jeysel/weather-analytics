# Página 01 — Visão Geral Climática

**Ferramenta:** Evidence.dev
**Rota:** `/`
**Fonte:** `weather_dw.mart_climate__daily_facts`

---

## Storytelling

> "Santa Catarina possui um dos climas mais variados do Brasil — serras frias, litoral úmido e planaltos com amplitudes extremas coexistem no mesmo estado. Esta página responde uma pergunta simples: *como está o clima no mês selecionado, comparado ao que é esperado para esta época?*"

O usuário chega nesta página buscando um resumo rápido. Em segundos, ele deve conseguir identificar se a temperatura atual está dentro ou fora do padrão histórico recente, se o mês está mais chuvoso ou mais seco que o normal, e quais regiões ou municípios estão com comportamento atípico.

A narrativa evolui do **geral para o específico**: primeiro os números agregados nos scorecards, depois a tendência no tempo pela série temporal, e por fim a distribuição espacial no mapa.

---

## Filtros

| Filtro | Comportamento padrão |
|--------|----------------------|
| Mesorregião | Todas as Mesorregiões |
| Município | Todos os Municípios (cascateado da mesorregião) |
| Mês/Ano | Mês mais recente disponível |

---

## Componentes

### Scorecards — Resumo do Período

Cinco BigValues exibem temperatura máxima, mínima, média, precipitação acumulada e anomalia média do mês. São o ponto de entrada da página — antes de qualquer gráfico, o usuário calibra sua leitura com os números absolutos do período.

---

### LineChart — Temperatura Média Diária e Desvio Histórico

Gráfico de linhas duplas com duas séries:
- **Azul:** temperatura média diária (`temp_avg_c`)
- **Laranja:** anomalia em relação à média dos últimos 30 dias (`temp_anomaly_c`)

Valores positivos de anomalia indicam dias acima do normal histórico recente; negativos, abaixo. Essa leitura paralela transforma um número bruto em contexto — não apenas "qual foi a temperatura" mas "foi um dia comum ou excepcional?".

---

### BubbleMap — Temperatura Média por Município

Mapa de bolhas cobrindo os 295 municípios de Santa Catarina. O **valor da cor** representa a temperatura média do período; o **tamanho da bolha** representa a amplitude térmica (diferença entre máxima e mínima). Municípios com bolhas maiores têm clima mais continental — dias quentes e noites frias.

A Serra Catarinense e o Planalto Serrano costumam apresentar as maiores amplitudes; o litoral, as menores.
