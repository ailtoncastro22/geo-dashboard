import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
import warnings

warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS')

# Configuração da página
st.set_page_config(page_title="Dashboard Geoespacial", layout="wide", page_icon="🌍")

# --- Botão de Idioma no Topo Direito ---
# Criamos uma coluna grande vazia na esquerda (proporção 8) e uma pequena na direita (proporção 2)
col_vazia, col_idioma = st.columns([8, 2])

with col_idioma:
    # Usamos um radio horizontal sem label para imitar um botão de alternância
    idioma = st.radio(
        "Idioma", 
        ["Português 🇧🇷", "English 🇺🇸"], 
        horizontal=True, 
        label_visibility="collapsed"
    )

# --- Dicionário de Traduções ---
textos = {
    "Português 🇧🇷": {
        "titulo": "🌍 Monitorização Territorial e Ambiental",
        "subtitulo": "Selecione um município no **mapa** OU na **tabela** abaixo para aproximar a visão e analisar os dados.",
        "loading": "A carregar a malha municipal...",
        "filtros": "Filtros de Análise",
        # ... (restante do seu dicionário em português)
    },
    "English 🇺🇸": {
        "titulo": "🌍 Territorial and Environmental Monitoring",
        "subtitulo": "Select a municipality on the **map** OR in the **table** below to zoom in and analyze the data.",
        "loading": "Loading municipal grid...",
        "filtros": "Analysis Filters",
        # ... (restante do seu dicionário em inglês)
    }
}

t = textos[idioma]

# --- Interface Principal ---
st.title(t["titulo"])
st.markdown(t["subtitulo"])

# ... (restante do código continua exatamente igual, a partir do @st.cache_data)
