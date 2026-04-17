# Página 05 — Análise Horária

**Ferramenta:** Evidence.dev
**Rota:** `/horario`
**Fonte:** `weather_dw.mart_climate__hourly_facts`

---

## Storytelling

> "Os dados diários mostram o que aconteceu num dia. Os dados horários mostram *como* aconteceu — o pico de calor foi às 14h ou às 16h? A umidade cai com o vento? A chuva foi pela manhã ou à noite?"

Esta página revela os padrões intradiários que ficam invisíveis nas médias diárias. Ela opera em dois níveis simultâneos: o **padrão regional** (como a temperatura e a umidade variam ao longo do dia em toda a mesorregião, baseado nos últimos 30 dias) e o **detalhamento de um dia específico** em um município concreto.

---

## Filtros

| Filtro | Tipo | Comportamento padrão |
|--------|------|----------------------|
| Mesorregião | Dropdown | Todas as Mesorregiões |
| Município | Dropdown | Florianópolis (cascateado da mesorregião) |
| Dia de referência | Dropdown | Dia mais recente disponível |

---

## Componentes

### LineChart — Perfil de Temperatura por Hora do Dia

Três séries (máxima, média, mínima) calculadas sobre os últimos 30 dias para a mesorregião selecionada. Mostra o envelope típico de temperatura em cada hora do dia — a banda entre máxima e mínima revela a amplitude horária típica, que costuma ser estreita de madrugada e larga no início da tarde.

---

### LineChart — Umidade Média por Hora do Dia

Série única de umidade relativa média por hora, também sobre os últimos 30 dias. A umidade segue padrão inverso à temperatura — cai no período mais quente do dia e sobe à noite. Regiões costeiras mantêm umidade alta mesmo durante o dia; o Oeste e o Planalto apresentam as maiores quedas diurnas.

---

### LineChart + BarChart + LineChart — Detalhamento do Dia

Três gráficos sequenciais para o município e dia selecionados:

1. **Temperatura e umidade hora a hora** — duas séries sobrepostas mostrando a curva de temperatura (°C) e umidade relativa (%) ao longo das 24 horas do dia de referência.

2. **Precipitação por hora** — barras com o volume de chuva registrado em cada hora, permitindo identificar se a chuva foi matinal, vespertina ou noturna.

3. **Vento e nebulosidade** — velocidade do vento (km/h) e cobertura de nuvens (%) hora a hora.

---

### LineChart — Dia de Referência vs Média dos 30 dias

Duas séries de temperatura para o município selecionado:
- **Vermelho:** temperatura real do dia de referência hora a hora
- **Cinza:** média das mesmas horas nos últimos 30 dias

Permite identificar se o dia foi atipicamente quente, frio ou dentro do padrão esperado para cada período do dia.

---

### DataTable — Condições Climáticas mais Frequentes

Top 10 condições atmosféricas (código WMO traduzido) registradas nos últimos 30 dias para o município selecionado, com temperatura média e umidade média associadas a cada condição. Revela o perfil climático dominante do município no período.

---

### BubbleMap — Temperatura por Município no Dia Selecionado

Mapa de bolhas cobrindo os 295 municípios (filtrado pela mesorregião, se selecionada). O **valor da cor** representa a temperatura média do dia de referência; o **tamanho da bolha** representa a velocidade média do vento. Permite identificar rapidamente quais regiões foram mais quentes ou frias naquele dia específico.
