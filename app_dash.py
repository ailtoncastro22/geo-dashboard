import dash
from dash import dcc, html, dash_table, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
import warnings

warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS')

# Carregamento de Dados (Executado apenas uma vez no arranque do servidor)
gdf = gpd.read_file('mt_municipios.geojson')
np.random.seed(42)
gdf['reserva_legal_perc'] = np.random.uniform(15, 85, size=len(gdf))
gdf['creditos_carbono'] = np.random.uniform(5000, 150000, size=len(gdf))
if 'name_muni' in gdf.columns:
    gdf = gdf.set_index('name_muni')

df_exibicao = gdf.drop(columns=['geometry']).reset_index()

# Dicionário de Traduções
textos = {
    "PT": {
        "titulo": "🌍 Monitorização Territorial e Ambiental",
        "lbl_var": "Selecione a variável:",
        "opt_rl": "Cobertura de Reserva Legal (%)",
        "opt_creditos": "Potencial de Créditos de Carbono",
        "metrica_rl": "Média de Reserva Legal:",
        "metrica_creditos": "Total de Créditos:"
    },
    "EN": {
        "titulo": "🌍 Territorial and Environmental Monitoring",
        "lbl_var": "Select the variable:",
        "opt_rl": "Legal Reserve Coverage (%)",
        "opt_creditos": "Carbon Credits Potential",
        "metrica_rl": "Average Legal Reserve:",
        "metrica_creditos": "Total Credits:"
    }
}

# Inicialização da App com tema Bootstrap moderno
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# --- Layout da Aplicação ---
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2(id="titulo-header", className="mt-4"), width=9),
        dbc.Col(
            dcc.RadioItems(
                id='seletor-idioma',
                options=[{'label': ' PT 🇧🇷', 'value': 'PT'}, {'label': ' EN 🇺🇸', 'value': 'EN'}],
                value='PT',
                inline=True,
                className="mt-4 float-end"
            ), width=3
        )
    ]),
    
    html.Hr(),
    
    dbc.Row([
        dbc.Col([
            html.Label(id="label-variavel", className="fw-bold"),
            dcc.Dropdown(
                id='seletor-variavel',
                options=[
                    {'label': 'Cobertura de Reserva Legal (%)', 'value': 'reserva_legal_perc'},
                    {'label': 'Potencial de Créditos de Carbono', 'value': 'creditos_carbono'}
                ],
                value='reserva_legal_perc',
                clearable=False
            ),
            html.Div(id="painel-metricas", className="mt-4 p-3 bg-light rounded")
        ], width=3),
        
        dbc.Col([
            dcc.Graph(id='mapa-interativo', style={'height': '50vh'})
        ], width=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Br(),
            dash_table.DataTable(
                id='tabela-interativa',
                columns=[{"name": i, "id": i} for i in df_exibicao.columns],
                data=df_exibicao.to_dict('records'),
                row_selectable="multi",
                selected_rows=[],
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
            )
        ])
    ])
], fluid=True)

# --- Callbacks (A "Magia" Reativa do Dash) ---
@app.callback(
    [Output('titulo-header', 'children'),
     Output('label-variavel', 'children'),
     Output('seletor-variavel', 'options'),
     Output('mapa-interativo', 'figure'),
     Output('painel-metricas', 'children'),
     Output('tabela-interativa', 'selected_rows')],
    [Input('seletor-idioma', 'value'),
     Input('seletor-variavel', 'value'),
     Input('mapa-interativo', 'clickData'),
     Input('tabela-interativa', 'selected_rows')],
    prevent_initial_call=False
)
def atualizar_dashboard(idioma, variavel, clique_mapa, linhas_tabela):
    t = textos[idioma]
    
    # Atualiza as opções do Dropdown com o idioma
    opcoes_drop = [
        {'label': t["opt_rl"], 'value': 'reserva_legal_perc'},
        {'label': t["opt_creditos"], 'value': 'creditos_carbono'}
    ]
    
    # Lógica de seleção cruzada (Mapa <-> Tabela)
    trigger = ctx.triggered_id
    municipios_selecionados = []
    linhas_selecionadas = linhas_tabela if linhas_tabela else []
    
    if trigger == 'mapa-interativo' and clique_mapa:
        nome_muni = clique_mapa['points'][0]['location']
        idx = df_exibicao[df_exibicao['name_muni'] == nome_muni].index[0]
        if idx not in linhas_selecionadas:
            linhas_selecionadas.append(idx)
        else:
            linhas_selecionadas.remove(idx) # Permite desselecionar ao clicar novamente
            
    if linhas_selecionadas:
        municipios_selecionados = df_exibicao.iloc[linhas_selecionadas]['name_muni'].tolist()

    # Filtra dados para as métricas e centralização
    if municipios_selecionados:
        gdf_plot = gdf.loc[municipios_selecionados]
        centro_lat = float(gdf_plot.geometry.centroid.y.mean())
        centro_lon = float(gdf_plot.geometry.centroid.x.mean())
        zoom = 6.5
    else:
        gdf_plot = gdf
        centro_lat, centro_lon = -12.64, -55.42
        zoom = 4.5

    # Constrói o Mapa
    fig = px.choropleth_mapbox(
        gdf, # Mostramos o estado todo sempre como fundo
        geojson=gdf.geometry,
        locations=gdf.index,
        color=variavel,
        color_continuous_scale="Viridis" if variavel == "reserva_legal_perc" else "YlOrRd",
        mapbox_style="carto-positron",
        center={"lat": centro_lat, "lon": centro_lon},
        zoom=zoom,
        opacity=0.7
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select')
    
    # Destaca as bordas dos selecionados
    if municipios_selecionados:
        fig.update_traces(selectedpoints=[gdf.index.get_loc(m) for m in municipios_selecionados])

    # Constrói as Métricas
    html_metricas = html.Div([
        html.H5(f"{t['metrica_rl']} {gdf_plot['reserva_legal_perc'].mean():.2f}%", className="text-success"),
        html.H5(f"{t['metrica_creditos']} {gdf_plot['creditos_carbono'].sum():,.0f}", className="text-info")
    ])

    return t["titulo"], t["lbl_var"], opcoes_drop, fig, html_metricas, linhas_selecionadas

if __name__ == '__main__':
    # Roda o servidor na porta 8050
    app.run_server(debug=True)
