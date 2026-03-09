import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
import warnings

# Ignora os avisos de cálculo de centroide do GeoPandas para manter o log limpo
warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS')

# Configuração da página
st.set_page_config(page_title="Dashboard Geoespacial", layout="wide", page_icon="🌍")

st.title("🌍 Monitorização Territorial e Ambiental")
st.markdown("Selecione um município no **mapa** OU na **tabela** abaixo para aproximar a visão e analisar os dados.")

@st.cache_data
def carregar_dados_espaciais():
    gdf = gpd.read_file('mt_municipios.geojson')
    np.random.seed(42)
    gdf['reserva_legal_perc'] = np.random.uniform(15, 85, size=len(gdf))
    gdf['creditos_carbono'] = np.random.uniform(5000, 150000, size=len(gdf))
    if 'name_muni' in gdf.columns:
        gdf = gdf.set_index('name_muni')
    return gdf

with st.spinner('A carregar a malha municipal...'):
    gdf_mt = carregar_dados_espaciais()

# --- Barra Lateral ---
st.sidebar.header("Filtros de Análise")
variavel_mapa = st.sidebar.selectbox(
    "Selecione a variável para o mapa:",
    options=["reserva_legal_perc", "creditos_carbono"],
    format_func=lambda x: "Cobertura de Reserva Legal (%)" if x == "reserva_legal_perc" else "Potencial de Créditos de Carbono"
)

# 1. Preparamos a tabela de exibição
df_exibicao = gdf_mt.drop(columns=['geometry']).sort_values(by=variavel_mapa, ascending=False)

# 2. Lógica Unificada de Captura (Lê a sessão do Mapa e da Tabela antes de tudo)
municipios_selecionados = []

# Verifica se o utilizador clicou na tabela
if "tabela_interativa" in st.session_state:
    linhas_selecionadas = st.session_state.tabela_interativa.get("selection", {}).get("rows", [])
    if linhas_selecionadas:
        municipios_selecionados.extend(df_exibicao.iloc[linhas_selecionadas].index.tolist())

# Verifica se o utilizador clicou diretamente no mapa
if "mapa_interativo" in st.session_state:
    pontos_selecionados = st.session_state.mapa_interativo.get("selection", {}).get("points", [])
    if pontos_selecionados:
        municipios_selecionados.extend([p["location"] for p in pontos_selecionados])

# Remove duplicações caso o clique venha dos dois lados
municipios_selecionados = list(set(municipios_selecionados))

# 3. Define os dados filtrados e a CENTRALIZAÇÃO DINÂMICA
if municipios_selecionados:
    gdf_plot = gdf_mt.loc[municipios_selecionados]
    st.subheader(f"📍 Destacando: {', '.join(municipios_selecionados)}")
    
    # Calcula a média do centro (latitude e longitude) das cidades selecionadas
    centro_lat = float(gdf_plot.geometry.centroid.y.mean())
    centro_lon = float(gdf_plot.geometry.centroid.x.mean())
    nivel_zoom = 6.5 # Zoom mais aproximado
else:
    gdf_plot = gdf_mt
    st.subheader("📍 Dados Gerais do Estado")
    
    # Centro padrão de Mato Grosso
    centro_lat = -12.64
    centro_lon = -55.42
    nivel_zoom = 4.5 # Zoom afastado mostrando o estado todo

# --- Construção do Mapa ---
fig = px.choropleth_mapbox(
    gdf_plot,
    geojson=gdf_plot.geometry,
    locations=gdf_plot.index,
    color=variavel_mapa,
    color_continuous_scale="Viridis" if variavel_mapa == "reserva_legal_perc" else "YlOrRd",
    mapbox_style="carto-positron",
    center={"lat": centro_lat, "lon": centro_lon}, # Usa as coordenadas dinâmicas
    zoom=nivel_zoom,                               # Usa o zoom dinâmico
    opacity=0.7,
    labels={'reserva_legal_perc': 'Reserva Legal (%)', 'creditos_carbono': 'Créditos'}
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# Renderiza o mapa com a chave ligada à sessão
st.plotly_chart(
    fig, 
    width="stretch", 
    on_select="rerun", 
    selection_mode="points", 
    key="mapa_interativo"
)

# --- Métricas ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.metric("Média de Reserva Legal", f"{gdf_plot['reserva_legal_perc'].mean():.2f}%")
with col2:
    st.metric("Total de Créditos de Carbono", f"{gdf_plot['creditos_carbono'].sum():,.0f}")

# --- Tabela Interativa ---
st.markdown("### Base de Dados (Selecione as linhas na lateral esquerda para filtrar o mapa)")
st.dataframe(
    df_exibicao, 
    width=1000,
    on_select="rerun",
    selection_mode="multi-row",
    key="tabela_interativa"
)
