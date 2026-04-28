import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from utils.bigquery import query, tbl, MESOREGIONS

load_dotenv()

st.set_page_config(
    page_title="Weather Analytics SC",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not os.environ.get("GCP_PROJECT_ID"):
    st.error(
        "**Configuração incompleta:** `GCP_PROJECT_ID` não definido.  \n"
        "Crie o arquivo `.env` a partir de `.env.example` e reinicie o serviço."
    )
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    meso = st.selectbox("Mesorregião", ["Todas"] + MESOREGIONS)
    days = st.slider("Período (dias)", 7, 90, 30, step=7)

meso_clause = f"AND mesoregion = '{meso}'" if meso != "Todas" else ""

# ── KPIs (últimos 7 dias) ─────────────────────────────────────────────────────
kpi_df = query(f"""
SELECT
  ROUND(AVG(temp_max_c), 1)  AS avg_max,
  ROUND(AVG(temp_min_c), 1)  AS avg_min,
  ROUND(AVG(temp_avg_c), 1)  AS avg_temp,
  ROUND(
    SUM(precipitation_mm) / NULLIF(COUNT(DISTINCT location_id), 0), 1
  )                           AS avg_precip,
  ROUND(AVG(temp_anomaly_c), 2) AS avg_anomaly
FROM {tbl('mart_climate__daily_facts')}
WHERE date >= DATE_SUB(CURRENT_DATE('America/Sao_Paulo'), INTERVAL 7 DAY)
  {meso_clause}
""")

alerts_df = query(f"""
SELECT COUNT(*) AS total
FROM {tbl('mart_climate__alerts')}
WHERE date >= DATE_SUB(CURRENT_DATE('America/Sao_Paulo'), INTERVAL 7 DAY)
  {meso_clause}
""")

st.title("🌤️ Weather Analytics — Santa Catarina")
st.caption(f"Últimos 7 dias · {meso if meso != 'Todas' else '295 municípios'}")

if not kpi_df.empty:
    r = kpi_df.iloc[0]

    def _v(val, fmt=".1f"):
        return "—" if pd.isna(val) else f"{val:{fmt}}"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Temp Máx Média",   f"{_v(r['avg_max'])} °C")
    c2.metric("Temp Mín Média",   f"{_v(r['avg_min'])} °C")
    c3.metric("Temp Média",       f"{_v(r['avg_temp'])} °C")
    c4.metric("Precip. Média",    f"{_v(r['avg_precip'])} mm")
    delta = float(r["avg_anomaly"] or 0)
    c5.metric(
        "Anomalia Térmica",
        f"{delta:+.1f} °C",
        delta=f"{delta:+.1f} vs média 30d",
        delta_color="inverse",
    )

st.divider()

col_trend, col_map = st.columns([3, 2])

# ── Tendência de temperatura ──────────────────────────────────────────────────
with col_trend:
    trend = query(f"""
    SELECT
      date,
      ROUND(AVG(temp_max_c), 1) AS temp_max,
      ROUND(AVG(temp_min_c), 1) AS temp_min,
      ROUND(AVG(temp_avg_c), 1) AS temp_avg
    FROM {tbl('mart_climate__daily_facts')}
    WHERE date >= DATE_SUB(CURRENT_DATE('America/Sao_Paulo'), INTERVAL {days} DAY)
      {meso_clause}
    GROUP BY date
    ORDER BY date
    """)

    if not trend.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend["date"], y=trend["temp_max"],
            name="Máxima", line=dict(color="#EF5350", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=trend["date"], y=trend["temp_avg"],
            name="Média", line=dict(color="#FFA726", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=trend["date"], y=trend["temp_min"],
            name="Mínima", line=dict(color="#42A5F5", width=2),
            fill="tonexty", fillcolor="rgba(66,165,245,0.08)",
        ))
        fig.update_layout(
            title=f"Tendência de temperatura — últimos {days} dias",
            yaxis_title="°C",
            legend=dict(orientation="h", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=40, b=0),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Mapa de municípios ────────────────────────────────────────────────────────
with col_map:
    mapa = query(f"""
    SELECT city_name, mesoregion, latitude, longitude,
           temp_max_c, precipitation_mm
    FROM {tbl('mart_climate__daily_facts')}
    WHERE date >= DATE_SUB(CURRENT_DATE('America/Sao_Paulo'), INTERVAL 2 DAY)
      {meso_clause}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY location_id ORDER BY date DESC) = 1
    """)

    if not mapa.empty:
        mapa["_size"] = mapa["precipitation_mm"].clip(lower=1)
        fig_m = px.scatter_mapbox(
            mapa,
            lat="latitude", lon="longitude",
            color="temp_max_c", size="_size", size_max=14,
            hover_name="city_name",
            hover_data={
                "mesoregion": True,
                "temp_max_c": ":.1f",
                "precipitation_mm": ":.1f",
                "latitude": False, "longitude": False, "_size": False,
            },
            color_continuous_scale="RdYlBu_r",
            range_color=[-5, 40],
            zoom=5.5,
            center={"lat": -27.2, "lon": -50.5},
            mapbox_style="carto-positron",
            labels={"temp_max_c": "Temp Máx (°C)", "precipitation_mm": "Precip (mm)"},
            height=360,
        )
        fig_m.update_layout(
            title="Temperatura Máxima por Município",
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_colorbar=dict(title="°C", thickness=12),
        )
        st.plotly_chart(fig_m, use_container_width=True)
