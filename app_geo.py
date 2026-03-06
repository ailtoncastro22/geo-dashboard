import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
from geobr import read_municipality
import json

st.set_page_config(page_title="Dashboard Geoespacial", layout="wide", page_icon="🌍")

st.title("🌍 Monitoramento Territorial e Ambiental")
st.markdown("Clique em um ou mais municípios no mapa para atualizar os dados abaixo.")

@st.cache_data
def carregar_dados_espaciais():
    # 1. Baixa os limites municipais do Mato Grosso usando geobr
    gdf = read_municipality(code_muni="MT", year=2020)
    gdf = gdf.to_crs(epsg=4326)
    
    # 2. Gerando dados fictícios para a simulação do dashboard
    np.random.seed(42)
    gdf['reserva_legal_perc'] = np.random.uniform(15, 85, size=len(gdf))
    gdf['creditos_carbono'] = np.random.uniform(5000, 150000, size=len(gdf))
    
    # Define o nome do município como index
    gdf = gdf.set_index('name_muni')
    return gdf

with st.spinner('Baixando malha municipal e processando geometrias...'):
    gdf_mt = carregar_dados_espaciais()

geojson = json.loads(gdf_mt.to_json())

# --- Barra Lateral ---
st.sidebar.header("Filtros de Análise")
variavel_mapa = st.sidebar.selectbox(
    "Selecione a variável para o mapa coroplético:",
    options=["reserva_legal_perc", "creditos_carbono"],
    format_func=lambda x: "Cobertura de Reserva Legal (%)" if x == "reserva_legal_perc" else "Potencial de Créditos de Carbono"
)

# --- Construção do Mapa com Plotly Express ---
st.subheader("Mapa Coroplético Interativo")

fig = px.choropleth_mapbox(
    gdf_mt,
    geojson=geojson,
    locations=gdf_mt.index,
    color=variavel_mapa,
    color_continuous_scale="Viridis" if variavel_mapa == "reserva_legal_perc" else "YlOrRd",
    mapbox_style="carto-positron",
    center={"lat": -12.64, "lon": -55.42},
    zoom=4.5,
    opacity=0.7,
    featureidkey="properties.name_muni",
    labels={'reserva_legal_perc': 'Reserva Legal (%)', 'creditos_carbono': 'Créditos'}
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# Renderiza o mapa e CAPTURA O CLIQUE usando on_select="rerun"
mapa_evento = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points")

# --- Lógica de Atualização Baseada no Clique ---
st.markdown("---")

# Verifica se o usuário clicou em algum ponto do mapa
municipios_clicados = []
if mapa_evento and "selection" in mapa_evento and len(mapa_evento["selection"]["points"]) > 0:
    # Extrai os nomes dos municípios clicados (que estão no 'location' do Plotly)
    municipios_clicados = [ponto["location"] for ponto in mapa_evento["selection"]["points"]]

# Filtra o dataframe com base no clique, ou mostra tudo se nada foi clicado
if municipios_clicados:
    st.subheader(f"📍 Dados Atualizados: {', '.join(municipios_clicados)}")
    gdf_plot = gdf_mt.loc[municipios_clicados]
else:
    st.subheader("📍 Dados Gerais do Estado (Clique no mapa para filtrar)")
    gdf_plot = gdf_mt

# Exibe métricas rápidas dos municípios filtrados
col1, col2 = st.columns(2)
with col1:
    st.metric("Média de Reserva Legal", f"{gdf_plot['reserva_legal_perc'].mean():.2f}%")
with col2:
    st.metric("Total de Créditos de Carbono", f"{gdf_plot['creditos_carbono'].sum():,.0f}")

# Exibe os dados tabulares
st.dataframe(gdf_plot.drop(columns=['geometry']).sort_values(by=variavel_mapa, ascending=False), width=1000)