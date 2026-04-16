# Página 02 — Análise de Precipitação

**Relatório:** Weather Analytics — Looker Studio
**Fonte:** `weather_dw.marts.mart_climate__daily_facts`

---

## Storytelling

> "A chuva é o fenômeno climático com maior impacto direto na vida da população catarinense — das enchentes no Vale do Itajaí ao déficit hídrico no Oeste. Esta página responde: *onde choveu, quanto choveu, e qual foi a intensidade?*"

O usuário que navega para esta página já viu o resumo geral e quer aprofundar a análise de precipitação. A jornada analítica percorre três perguntas em sequência: onde choveu mais, quando choveu, e com que intensidade. A resposta a essas três perguntas juntas revela algo que nenhuma delas isolada consegue — o *perfil* da chuva no período.

A narrativa conecta volume (mm) com intensidade (classe), permitindo distinguir um mês com chuvas concentradas em poucos dias intensos de um mês com chuvas regulares e distribuídas. Ambos podem ter o mesmo total acumulado, mas consequências completamente diferentes para drenagem, agricultura e risco de desastre.

---

### Barras — Precipitação por Município

O gráfico de barras ordenado por volume revela rapidamente quais municípios foram mais afetados pela chuva no período. A linha de referência da média estadual contextualiza cada barra: estar acima ou abaixo dela indica se o município teve um comportamento extraordinário ou dentro do padrão de Santa Catarina naquele período.

---

### Heatmap Calendário — Distribuição Temporal da Intensidade

O heatmap responde a pergunta "quando choveu?". Cada linha é um dia; as cores indicam quantos municípios registraram cada intensidade naquele dia. Um dia com muitos municípios em `heavy` ou `extreme` sinaliza um evento de precipitação generalizada — o tipo de situação que sobrecarrega sistemas de drenagem e eleva o risco de alagamentos no estado.

Dias isolados com cores intensas revelam eventos localizados; sequências de dias coloridos revelam períodos prolongados de chuva — padrões com impactos e riscos distintos.

---

### Donut — Distribuição por Classe de Precipitação

O gráfico de rosca fecha a análise respondendo: qual foi o *perfil dominante* do período? Um mês típico do litoral catarinense tem predominância de dias `light` e `moderate`. Um mês com fatia relevante de `heavy` ou `extreme` merece atenção — indica que as chuvas não foram apenas volumosas, mas também concentradas em eventos de alta intensidade.
