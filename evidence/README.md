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
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Dev\Engenharia-Dados\Weather-Analytics\postgresql\secrets\gcp-service-account.json" -> (Necessário para autenticar)


npm run sources
```

### 4. Iniciar o servidor de desenvolvimento

```bash
npm run dev   
# Acesse: http://localhost:3000
```

## Deploy

### GitHub Pages (gratuito)

```bash
npm run build
```

# O projeto está com o GitHub Actions configurado para publicar as alterações automaticamente.
# Passos executados: 

* No repositório → Settings → Pages → em Source, selecionar "GitHub Actions"

* No repositório → Settings → Secrets and variables → Actions → New repository secret


## Referências

- [Evidence.dev — Documentação](https://docs.evidence.dev)
- [BigQuery connector](https://docs.evidence.dev/core-concepts/data-sources/#bigquery)
- [PostgreSQL connector](https://docs.evidence.dev/core-concepts/data-sources/#postgresql)
- [Rotas dinâmicas](https://docs.evidence.dev/core-concepts/routing/#dynamic-pages)
