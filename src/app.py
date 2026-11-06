import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(page_title="ONU: Hegemonía y Democracia", layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def load_data():
    # Cargar Asamblea General
    ag = pd.read_csv("data/processed/ag_votes.csv")
    # Mapear votos a numérico para correlaciones (Sí=1, No=-1, Abstención/Ausente=NaN)
    ag['vote_num'] = ag['vote_text'].map({'Sí': 1, 'No': -1, 'Abstención': np.nan, 'Ausente': np.nan})
    
    # Cargar Vetos
    vetos = pd.read_csv("data/processed/sc_vetos.csv")
    return ag, vetos

st.title("🕊️ Hegemonía y Democracia en la ONU")
st.markdown("""
**Hipótesis de Investigación:** La estructura institucional de la ONU y la presión de las potencias hegemónicas moldean la política exterior de los Estados, generando bloques de alineación y un déficit democrático estructural.
""")

try:
    df_ag, df_vetos = load_data()
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌐 Red de Poder (Network)", 
        "⚖️ Alineación Hegemónica", 
        "🛑 El Poder del Veto",
        "📊 Datos Crudos"
    ])

    with tab1:
        st.header("Red de Co-votación (¿Quién vota con quién?)")
        st.markdown("Los nodos representan países. Las líneas conectan a países que votaron igual (Sí o No) en más del 75% de las resoluciones ese año. El color indica su bloque principal.")
        
        year_sel = st.slider("Selecciona un año para analizar la red:", 1992, 2023, 2022)
        
        # Preparar matriz de correlación para el año seleccionado
        df_year = df_ag[df_ag['year'] == year_sel]
        pivot = df_year.pivot_table(index='rcid', columns='Countryname', values='vote_num', aggfunc='first')
        
        # Calcular correlación (solo si hay suficientes votos en común)
        corr = pivot.corr(min_periods=20)
        
        # Crear grafo
        G = nx.Graph()
        paises = corr.columns.tolist()
        G.add_nodes_from(paises)
        
        # Agregar aristas si la correlación es alta (> 0.75)
        for i in range(len(paises)):
            for j in range(i+1, len(paises)):
                if corr.iloc[i, j] > 0.75:
                    G.add_edge(paises[i], paises[j], weight=corr.iloc[i, j])
        
        # Layout del grafo
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        
        # Crear trazos para Plotly
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')
        
        node_x, node_y, text, color = [], [], [], []
        
        # Definir color por bloque (basado en alineación con EE.UU. o Rusia)
        us_votes = pivot.get('United States of America', pd.Series())
        ru_votes = pivot.get('Russian Federation', pd.Series())
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Calcular afinidad con hegemones
            afinidad_us = corr.loc[node, 'United States of America'] if 'United States of America' in corr.columns else 0
            afinidad_ru = corr.loc[node, 'Russian Federation'] if 'Russian Federation' in corr.columns else 0
            
            if afinidad_us > 0.6:
                color.append('#1f77b4') # Azul (EE.UU.)
                text.append(f"{node}<br>Alineación EE.UU.: {afinidad_us:.2f}")
            elif afinidad_ru > 0.6:
                color.append('#d62728') # Rojo (Rusia)
                text.append(f"{node}<br>Alineación Rusia: {afinidad_ru:.2f}")
            else:
                color.append('#7f7f7f') # Gris (No alineado)
                text.append(f"{node}<br>No alineado fuerte")
                
        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers+text', hoverinfo='text', text=text, textposition="top center",
            marker=dict(showscale=False, color=color, size=10, line_width=1)
        )
        
        fig_net = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(
            showlegend=False, hovermode='closest', margin=dict(b=0,l=0,r=0,t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=700
        ))
        st.plotly_chart(fig_net, use_container_width=True)

    with tab2:
        st.header("Pérdida de Soberanía: Alineación con los Hegemones")
        st.markdown("Selecciona un país para ver cómo evoluciona su alineación (coincidencia de votos) con EE.UU. y Rusia/China a lo largo del tiempo. Una línea alta indica que el país renuncia a su propia política para seguir al hegemón.")
        
        pais_sel = st.selectbox("Selecciona un país:", sorted([p for p in df_ag['Countryname'].unique() if pd.notna(p)]), index=0)
        
        # Filtrar datos del país
        df_pais = df_ag[df_ag['Countryname'] == pais_sel]
        
        # Obtener votos de hegemones
        df_hegemones = df_ag[df_ag['Countryname'].isin(['United States of America', 'Russian Federation', 'China'])]
        
        # Unir por rcid
        df_merged = pd.merge(df_pais[['rcid', 'year', 'vote_num']], 
                             df_hegemones[['rcid', 'Countryname', 'vote_num']], 
                             on='rcid', suffixes=('', '_hegemon'))
        
        # Calcular coincidencia por año
        def calc_afinidad(row):
            return row['vote_num'] == row['vote_num_hegemon']
        
        df_merged['coincide'] = df_merged.apply(calc_afinidad, axis=1)
        
        # Agrupar por año y hegemón
        afinidad_tiempo = df_merged.groupby(['year', 'Countryname_hegemon'])['coincide'].mean().reset_index()
        afinidad_tiempo['Porcentaje'] = afinidad_tiempo['coincide'] * 100
        
        fig_afinidad = px.line(afinidad_tiempo, x='year', y='Porcentaje', color='Countryname_hegemon',
                               title=f"Evolución de la alineación de {pais_sel} con las potencias",
                               labels={'year': 'Año', 'Porcentaje': '% de Votos Coincidentes', 'Countryname_hegemon': 'Hegemón'},
                               markers=True)
        fig_afinidad.update_yaxes(range=[0, 100])
        st.plotly_chart(fig_afinidad, use_container_width=True)

    with tab3:
        st.header("El Déficit Democrático: Vetos vs. Mayorías")
        st.markdown("El Consejo de Seguridad tiene 5 miembros permanentes con poder de veto. Esto permite que **un solo país** anule la voluntad de la mayoría global expresada en la Asamblea.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            vetos_pais = df_vetos['Pais'].value_counts().reset_index()
            vetos_pais.columns = ['País', 'Cantidad de Vetos']
            fig_vetos = px.pie(vetos_pais, values='Cantidad de Vetos', names='País', 
                               title="Distribución de Vetos (1992 - Presente)', hole=0.4)
            st.plotly_chart(fig_vetos, use_container_width=True)
            
        with col2:
            st.markdown("### ¿Quién bloquea el cambio?")
            st.dataframe(vetos_pais, hide_index=True, use_container_width=True)
            st.info("Un solo voto negativo en el Consejo bloquea una resolución, incluso si los otros 14 miembros están a favor.")

    with tab4:
        st.header("Explorador de Datos")
        st.write("Filtra y descarga los datos procesados para tu investigación.")
        
        year_filter = st.multiselect("Filtrar por año:", sorted(df_ag['year'].unique()), default=[2020, 2021, 2022])
        if year_filter:
            st.dataframe(df_ag[df_ag['year'].isin(year_filter)][['year', 'Countryname', 'vote_text', 'descr']].head(100))

except Exception as e:
    st.error(f"Error cargando los datos. Detalle: {e}")
