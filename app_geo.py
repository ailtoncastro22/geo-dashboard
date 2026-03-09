import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Geoespacial", layout="wide", page_icon="🌍")

st.title("🌍 Monitorização Territorial e Ambiental")
st.markdown("Selecione um município no **mapa** OU na **tabela** abaixo para analisar os dados específicos.")

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

# 1. Preparamos a tabela de exibição ANTES do mapa para sabermos a ordem exata das linhas
df_exibicao = gdf_mt.drop(columns=['geometry']).sort_values(by=variavel_mapa, ascending=False)

# 2. Lógica de Captura da Tabela (Lê o clique da tabela antes de desenhar o mapa)
municipios_selecionados = []
if "tabela_interativa" in st.session_state:
    linhas_selecionadas = st.session_state.tabela_interativa["selection"]["rows"]
    if linhas_selecionadas:
        # Pega os nomes dos municípios baseados no número da linha que foi clicada
        municipios_selecionados = df_exibicao.iloc[linhas_selecionadas].index.tolist()

# 3. Define quais dados o mapa e as métricas vão usar
if municipios_selecionados:
    gdf_plot = gdf_mt.loc[municipios_selecionados]
    st.subheader(f"📍 Destacando: {', '.join(municipios_selecionados)}")
else:
    gdf_plot = gdf_mt
    st.subheader("📍 Dados Gerais do Estado")

# --- Construção do Mapa ---
fig = px.choropleth_mapbox(
    gdf_plot,
    geojson=gdf_plot.geometry,
    locations=gdf_plot.index,
    color=variavel_mapa,
    color_continuous_scale="Viridis" if variavel_mapa == "reserva_legal_perc" else "YlOrRd",
    mapbox_style="carto-positron",
    center={"lat": -12.64, "lon": -55.42},
    zoom=4.5 if not municipios_selecionados else 5.5, # Aplica um pequeno zoom se houver seleção
    opacity=0.7,
    labels={'reserva_legal_perc': 'Reserva Legal (%)', 'creditos_carbono': 'Créditos'}
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# Renderiza o mapa (ainda permite o clique direto nele)
mapa_evento = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="mapa_interativo")

# Se o utilizador clicar no mapa em vez da tabela, ajustamos os dados para mostrar as métricas corretas
if mapa_evento and len(mapa_evento.selection.points) > 0:
    municipios_clicados_mapa = [ponto["location"] for ponto in mapa_evento.selection.points]
    gdf_plot = gdf_mt.loc[municipios_clicados_mapa]

# --- Métricas ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.metric("Média de Reserva Legal", f"{gdf_plot['reserva_legal_perc'].mean():.2f}%")
with col2:
    st.metric("Total de Créditos de Carbono", f"{gdf_plot['creditos_carbono'].sum():,.0f}")

# --- Tabela Interativa ---
st.markdown("### Base de Dados (Selecione as linhas na lateral esquerda para filtrar o mapa)")

# Adicionamos os parâmetros on_select e a key para vincular ao Session State
st.dataframe(
    df_exibicao, 
    width=1000,
    on_select="rerun",          # Faz a página recarregar ao selecionar a linha
    selection_mode="multi-row", # Permite selecionar múltiplas cidades segurando Shift/Ctrl
    key="tabela_interativa"     # O nome da variável que lemos lá no topo do código
)
