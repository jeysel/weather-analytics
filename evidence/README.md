# Evidence.dev — Weather Analytics Dashboard

Camada de visualização do pipeline **Weather Analytics**.
Consome os marts do dbt materializados no BigQuery (prod) ou PostgreSQL (dev)
e gera um site estático com dashboards interativos.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Fonte (prod) | BigQuery — dataset `weather_dw_marts` |
| Fonte (dev)  | PostgreSQL — schema `dbt_dev_marts` |
| Framework    | [Evidence.dev](https://evidence.dev) |
| Deploy       | GitHub Pages / Netlify / Vercel |

## Páginas

| Página | Rota | Descrição |
|--------|------|-----------|
| Visão Geral | `/` | KPIs do pipeline, temperatura nacional, alertas e resumo por região |
| Temperatura | `/temperatura` | Série temporal, anomalias e ranking por cidade |
| Precipitação | `/precipitacao` | Acumulados, classificação e anomalias por região |
| Alertas | `/alertas` | Eventos extremos detectados, evolução e cidades mais afetadas |
| Cidade (dinâmica) | `/cidades/[location_id]` | Drill-down completo para cada localidade |

## Pré-requisitos

- Node.js 18+ instalado
- Pipeline dbt executado (`dbt build`) com dados materializados
- Para prod: Service Account GCP com roles `BigQuery Data Viewer` e `BigQuery Job User`

## Configuração

### 1. Instalar dependências

```bash
cd \Weather-Analytics\evidence
cd evidence
npm install
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com seus valores
```

### 3. Carregar as fontes de dados

```bash
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Dev\Analytics-Engineer\Weather-Analytics\postgresql\secrets\gcp-service-account.json" -> (Necessário para autenticar)


npm run sources
```

### 4. Iniciar o servidor de desenvolvimento

```bash
npm run dev   
# Acesse: http://localhost:3000
```

## Deploy

### GitHub Pages (gratuito)

O deploy é automático via GitHub Actions a cada push na branch `main` que altere arquivos em `Weather-Analytics/evidence/`.

#### Passo 1 — Ativar GitHub Pages

```
Repositório → Settings → Pages → Source → selecionar "GitHub Actions"
```

#### Passo 2 — Cadastrar os Secrets

```
Repositório → Settings → Secrets and variables → Actions → New repository secret
```

Cadastrar os seguintes secrets, um por vez:

| Name | Secret |
|------|--------|
| `EVIDENCE_SOURCE__weather_dw__project_id` | `weather-analytics-490113` |
| `EVIDENCE_SOURCE__weather_dw__dataset` | `marts` |
| `EVIDENCE_SOURCE__weather_dw__location` | `southamerica-east1` |
| `EVIDENCE_SOURCE__weather_dw__client_email` | valor do campo `client_email` do arquivo `gcp-service-account.json` |
| `EVIDENCE_SOURCE__weather_dw__private_key` | valor do campo `private_key` do arquivo `gcp-service-account.json` (incluindo os `\n`) |

> O arquivo `gcp-service-account.json` está em `postgresql/secrets/`.

#### Passo 3 — Disparar o deploy

Faça um push na branch `main` alterando qualquer arquivo em `Weather-Analytics/evidence/`,
ou acesse:

```
Repositório → Actions → Deploy Evidence to GitHub Pages → Run workflow
```

O site ficará disponível em:
```
https://<seu-usuario>.github.io/Analytics-Engineer/
```


## Referências

- [Evidence.dev — Documentação](https://docs.evidence.dev)
- [BigQuery connector](https://docs.evidence.dev/core-concepts/data-sources/#bigquery)
- [PostgreSQL connector](https://docs.evidence.dev/core-concepts/data-sources/#postgresql)
- [Rotas dinâmicas](https://docs.evidence.dev/core-concepts/routing/#dynamic-pages)
