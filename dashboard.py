"""
Dashboard - Habitos de consumo por region en Argentina.
Se adapta a los datos disponibles (Trends + INDEC si esta).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from pathlib import Path

st.set_page_config(page_title="Consumo AR", layout="wide")

DB_PATH = Path(__file__).resolve().parent / "data" / "consumo.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


@st.cache_data(ttl=300)
def q(sql):
    try:
        return pd.read_sql(sql, engine)
    except Exception:
        return pd.DataFrame()


REGIONES_LEGIBLES = {
    "Ciudad de Buenos Aires": "CABA",
    "Buenos Aires": "Buenos Aires",
    "Cordoba": "Cordoba",
    "Córdoba": "Córdoba",
    "Santa Fe": "Santa Fe",
    "Mendoza": "Mendoza",
    "Tucuman": "Tucuman",
    "Tucumán": "Tucumán",
    "Entre Rios": "Entre Rios",
    "Entre Ríos": "Entre Ríos",
    "Salta": "Salta",
    "Misiones": "Misiones",
    "Chaco": "Chaco",
    "Corrientes": "Corrientes",
    "Santiago del Estero": "Santiago del Estero",
    "San Juan": "San Juan",
    "Jujuy": "Jujuy",
    "Rio Negro": "Rio Negro",
    "Río Negro": "Río Negro",
    "Neuquen": "Neuquen",
    "Neuquén": "Neuquén",
    "Formosa": "Formosa",
    "Chubut": "Chubut",
    "San Luis": "San Luis",
    "Catamarca": "Catamarca",
    "La Rioja": "La Rioja",
    "La Pampa": "La Pampa",
    "Santa Cruz": "Santa Cruz",
    "Tierra del Fuego": "Tierra del Fuego",
}


def limpiar_region(r):
    if not r:
        return ""
    for k, v in REGIONES_LEGIBLES.items():
        if k.lower() in str(r).lower():
            return v
    return str(r)


st.title("Habitos de consumo por region - Argentina")
st.caption("Datos de Google Trends + INDEC (si esta disponible)")

trends = q("SELECT keyword, region, interes, fecha FROM trends_region")

if trends.empty:
    st.error("No hay datos de Trends. Corre primero: python scrapers/trends_region.py")
    st.stop()

trends["region_limpia"] = trends["region"].apply(limpiar_region)

# KPIs
st.markdown("### Resumen")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Terminos", trends["keyword"].nunique())
c2.metric("Provincias", trends["region_limpia"].nunique())
c3.metric("Registros", len(trends))
c4.metric("Ultima actualizacion", trends["fecha"].max())

st.divider()

# Mapa de calor
st.markdown("### Mapa de calor: que busca cada provincia")
st.caption("Mas rojo = mas se busca ese termino en esa provincia")

pivot = trends.pivot_table(
    index="keyword",
    columns="region_limpia",
    values="interes",
    aggfunc="mean",
).fillna(0)

if not pivot.empty:
    pivot = pivot[pivot.sum().sort_values(ascending=False).index]
    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="YlOrRd",
        labels=dict(x="Provincia", y="Termino", color="Interes"),
        height=500,
    )
    fig.update_xaxes(side="bottom", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Ranking por termino
st.markdown("### Ranking por termino")
terminos = sorted(trends["keyword"].unique())
termino_sel = st.selectbox("Elegi un termino", terminos)

df_sel = trends[trends["keyword"] == termino_sel].copy()
df_sel = df_sel.groupby("region_limpia")["interes"].mean().reset_index()
df_sel = df_sel.sort_values("interes", ascending=False).head(15)

fig = px.bar(
    df_sel,
    x="interes",
    y="region_limpia",
    orientation="h",
    color="interes",
    color_continuous_scale="Reds",
    labels={"interes": "Interes", "region_limpia": "Provincia"},
    height=500,
)
fig.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Comparativa
st.markdown("### Comparar terminos")
terminos_comp = st.multiselect(
    "Elegi 2-5 terminos",
    terminos,
    default=terminos[:3] if len(terminos) >= 3 else terminos,
)

if terminos_comp:
    df_comp = trends[trends["keyword"].isin(terminos_comp)]
    df_comp = df_comp.groupby(["keyword", "region_limpia"])["interes"].mean().reset_index()
    fig = px.bar(
        df_comp,
        x="region_limpia",
        y="interes",
        color="keyword",
        barmode="group",
        labels={"interes": "Interes", "region_limpia": "Provincia", "keyword": "Termino"},
        height=500,
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Oportunidades
st.markdown("### Oportunidades de cobertura")
st.caption("Provincias donde un termino tiene interes MUY por encima del promedio")

oportunidades = []
for termino in terminos:
    df_t = trends[trends["keyword"] == termino].copy()
    df_t = df_t.groupby("region_limpia")["interes"].mean().reset_index()
    if df_t.empty or df_t["interes"].std() == 0:
        continue
    media = df_t["interes"].mean()
    std = df_t["interes"].std()
    df_t["z_score"] = (df_t["interes"] - media) / std
    top = df_t[df_t["z_score"] > 1.5].sort_values("z_score", ascending=False)
    for _, row in top.iterrows():
        oportunidades.append({
            "Termino": termino,
            "Provincia": row["region_limpia"],
            "Interes": round(row["interes"], 1),
            "Desvio vs media": round(row["z_score"], 2),
        })

if oportunidades:
    df_op = pd.DataFrame(oportunidades).sort_values("Desvio vs media", ascending=False)
    st.dataframe(df_op.head(20), use_container_width=True)
else:
    st.info("Sin oportunidades detectadas. Corre mas Trends.")

st.divider()

# INDEC si hay datos
try:
    cba = q("SELECT region, fecha, valor FROM cba_regional ORDER BY fecha")
    if not cba.empty:
        st.markdown("### INDEC - Canasta Basica Alimentaria")
        fig = px.line(cba, x="fecha", y="valor", color="region",
                      title="Evolucion de la CBA por region")
        st.plotly_chart(fig, use_container_width=True)
except Exception:
    pass

# Datos crudos
with st.expander("Ver datos crudos de Trends"):
    st.dataframe(
        trends.sort_values("fecha", ascending=False).head(200),
        use_container_width=True,
    )