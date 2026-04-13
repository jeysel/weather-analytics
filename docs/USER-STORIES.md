# User Stories: Weather Analytics Platform

Todas User Stories seguem formato:

**Como** [persona],  
**Quero** [ação],  
**Para que** [valor/benefício].

**Acceptance Criteria** em formato BDD (Given/When/Then).

---

## 🌡️ Feature 1: Ingestão Dados Climáticos

### US-001: Coletar Dados Temperatura via API

**Como** engenheiro de dados,  
**Quero** coletar dados temperatura de localidades brasileiras via API Open-Meteo,  
**Para que** eu tenha base confiável para análises climáticas.

#### Acceptance Criteria
```gherkin
Given API Open-Meteo está disponível
And lista de 18 coordenadas brasileiras está configurada
When executar script de coleta diária
Then dados temperatura devem ser coletados para todas localidades
And cada registro deve conter: cidade, data, temp_min, temp_max, temp_avg
And dados devem ser inseridos em PostgreSQL tabela raw_weather
And logs devem registrar timestamp e status (sucesso/falha)
```

**Implementação:** `postgresql/collector/collector.py`

---

### US-002: Coletar Dados Precipitação via API

**Como** engenheiro de dados,  
**Quero** coletar dados precipitação junto com temperatura,  
**Para que** análises considerem múltiplas variáveis climáticas.

#### Acceptance Criteria
```gherkin
Given API Open-Meteo endpoint suporta precipitação
When executar coleta
Then dados precipitação devem ser incluídos no mesmo request
And precipitação deve ser armazenada em mm (milímetros)
And valores null devem ser permitidos (dias sem chuva)
```

**Implementação:** `postgresql/collector/collector.py`

---

### US-003: Replicar Dados PostgreSQL → BigQuery

**Como** analytics engineer,  
**Quero** que dados PostgreSQL sejam replicados para BigQuery automaticamente,  
**Para que** transformações dbt possam processar volumes maiores com performance cloud.

#### Acceptance Criteria
```gherkin
Given Airbyte connector PostgreSQL → BigQuery configurado
When novos dados forem inseridos em PostgreSQL
Then Airbyte deve sincronizar para BigQuery (latência < 1h)
And schema BigQuery deve espelhar PostgreSQL
And sync deve ser incremental (não full refresh)
And logs Airbyte devem registrar sucesso/falha
```

**Implementação:** Airbyte UI config + `airbyte/config.json`  
**Monitoramento:** Airbyte dashboard

---

## 🔄 Feature 2: Pipeline ELT + Data Quality

### US-005: Criar Camada Staging (Limpeza Dados Brutos)

**Como** analytics engineer,  
**Quero** criar modelos staging que limpem e padronizem dados brutos,  
**Para que** camadas downstream tenham dados confiáveis.

#### Acceptance Criteria
```gherkin
Given dados brutos em BigQuery dataset raw
When executar dbt run --models staging
Then modelos stg_* devem ser criados em dataset staging
And colunas devem ter nomes padronizados (snake_case)
And tipos de dados devem ser casting corretos (dates, floats)
And nulls inválidos devem ser tratados (substituir/remover)
And testes unique + not_null devem passar em chaves primárias
```

**Implementação:**
- `models/staging/stg_weather__raw_observations.sql`
- `models/staging/schema.yml` (testes + docs)

---

### US-006: Calcular Médias Móveis Temperatura (30 dias)

**Como** analista climático,  
**Quero** visualizar médias móveis temperatura últimos 30 dias,  
**Para que** eu identifique tendências e sazonalidades.

#### Acceptance Criteria
```gherkin
Given dados temperatura diários em staging
When executar modelo intermediate agregações
Then rolling average 30 dias deve ser calculado para cada localidade
And valores devem considerar apenas registros completos (sem nulls)
And resultado deve incluir: cidade, data, temp_avg, temp_rolling_30d
And testes devem validar rolling_avg <= max(temp) AND >= min(temp)
```

**Implementação:**
- `models/intermediate/int_weather__temperature_aggregates.sql`
- Window function: `AVG(temp_avg) OVER (PARTITION BY city ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)`

**Testes:**
```yaml
- dbt_utils.expression_is_true:
    expression: "temp_rolling_30d <= temp_max_30d"
- dbt_utils.expression_is_true:
    expression: "temp_rolling_30d >= temp_min_30d"
```

---

### US-007: Detectar Anomalias Climáticas

**Como** gestor de riscos,  
**Quero** identificar eventos climáticos anômalos (temperatura fora padrão),  
**Para que** eu antecipe riscos e tome ações preventivas.

#### Acceptance Criteria
```gherkin
Given dados históricos temperatura (mínimo 30 dias)
When valor temperatura > média + 2*desvio-padrão
Then registro deve ser classificado como anomalia
And anomalia deve ter severidade:
  - MÉDIA: 2σ < valor <= 2.5σ
  - ALTA: 2.5σ < valor <= 3σ
  - CRÍTICA: valor > 3σ
And dashboard deve exibir alerta visual (cor + ícone)
And dados devem ser armazenados em marts_weather__climate_alerts
```

**Implementação:**
- `models/marts/marts_weather__climate_alerts.sql`
- Cálculo: `(temp - AVG(temp)) / STDDEV(temp) > 2`

**Testes:**
```yaml
- accepted_values:
    column_name: severity
    values: ['MÉDIA', 'ALTA', 'CRÍTICA']
```

---

### US-008: Implementar 40+ Testes Data Quality

**Como** analytics engineer,  
**Quero** que pipeline tenha 40+ testes automatizados,  
**Para que** dados sejam confiáveis para tomada decisão.

#### Acceptance Criteria
```gherkin
Given todos modelos dbt criados
When executar `dbt test`
Then no mínimo 40 testes devem existir
And testes devem cobrir:
  - Unique keys (15+ testes)
  - Not null em colunas críticas (12+ testes)
  - Accepted values em enums (8+ testes)
  - Ranges válidos (5+ testes)
And 100% testes devem passar
And relatório html deve ser gerado
```

**Implementação:** `schema.yml` em cada camada  
**Tipos testes:**
- `unique`
- `not_null`
- `accepted_values`
- `dbt_utils.expression_is_true`
- `dbt_expectations.expect_column_values_to_be_between`

---

## 📊 Feature 3: Dashboard Interativo

### US-009: Visualizar Temperatura por Localidade

**Como** analista,  
**Quero** ver gráfico temperatura ao longo do tempo por localidade,  
**Para que** eu compare padrões climáticos entre regiões.

#### Acceptance Criteria
```gherkin
Given dashboard Evidence.dev publicado
When acessar página "Análise de Temperatura"
Then gráfico linha deve exibir temperatura diária
And filtro dropdown deve permitir selecionar localidade
And gráfico deve incluir:
  - Temperatura média (linha principal)
  - Média móvel 30d (linha tracejada)
  - Faixa min-max (área sombreada)
And gráfico deve carregar em < 3 segundos
```

**Implementação:**
- `pages/temperatura.md`
- Evidence chart component: `LineChart`

---

### US-010: Exibir Alertas Climáticos

**Como** gestor,  
**Quero** ver página dedicada a alertas climáticos,  
**Para que** eu identifique rapidamente eventos anômalos.

#### Acceptance Criteria
```gherkin
Given anomalias detectadas em marts_weather__climate_alerts
When acessar página "Alertas Climáticos"
Then tabela deve listar alertas últimos 7 dias
And cada alerta deve mostrar: data, cidade, tipo, severidade, valor
And alertas devem ter código cor:
  - MÉDIA: amarelo
  - ALTA: laranja
  - CRÍTICA: vermelho
And se nenhum alerta: exibir mensagem "Nenhum alerta nos últimos 7 dias"
```

**Implementação:**
- `pages/alertas.md`
- Evidence component: `DataTable` com conditional formatting

---

### US-012: Deploy Automático via CI/CD

**Como** desenvolvedor,  
**Quero** que dashboard seja publicado automaticamente após commit,  
**Para que** mudanças cheguem produção sem intervenção manual.

#### Acceptance Criteria
```gherkin
Given GitHub Actions workflow configurado
When fazer push para branch main
Then workflow deve executar:
  1. Install dependencies (npm install)
  2. Build Evidence (npm run build)
  3. Deploy para GitHub Pages
And deploy deve completar em < 10 minutos
And em caso de erro, workflow deve falhar (não deploy quebrado)
And URL público deve refletir mudanças em < 3min após success
```

**Implementação:**
- `.github/workflows/deploy.yml`
- GitHub Pages config

**Monitoramento:**
- GitHub Actions logs
- Uptime check (manual/script)

---

## 📋 Backlog User Stories (Futuras)

### US-013: Previsão Temperatura 7 Dias (ML)

**Como** analista,  
**Quero** ver previsão temperatura próximos 7 dias,  
**Para que** eu antecipe condições climáticas futuras.

**Acceptance Criteria:** [A definir quando priorizado]

---

### US-014: Notificações Email Alertas Críticos

**Como** gestor,  
**Quero** receber email quando alerta CRÍTICO for detectado,  
**Para que** eu tome ação imediata sem precisar acessar dashboard.

**Acceptance Criteria:** [A definir quando priorizado]

---

## 📊 Rastreabilidade

| User Story | Feature | Epic | Status |
|------------|---------|------|--------|
| US-001 | Feature 1 | Weather Analytics | ✅ |
| US-002 | Feature 1 | Weather Analytics | ✅ |
| US-003 | Feature 1 | Weather Analytics | ✅ |
| US-005 | Feature 2 | Weather Analytics | ✅ |
| US-006 | Feature 2 | Weather Analytics | ✅ |
| US-007 | Feature 2 | Weather Analytics | ✅ |
| US-008 | Feature 2 | Weather Analytics | ✅ |
| US-009 | Feature 3 | Weather Analytics | ✅ |
| US-010 | Feature 3 | Weather Analytics | ✅ |
| US-012 | Feature 3 | Weather Analytics | ✅ |
| US-013 | [Backlog] | Weather Analytics | 📋 |
| US-014 | [Backlog] | Weather Analytics | 📋 |

---

**Última atualização:** Abril 2026  
**User Stories implementadas:** 10/12 (83%)