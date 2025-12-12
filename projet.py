import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap, AntPath
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Configuration moderne de la page
st.set_page_config(
    page_title="🚗 EV Telemetry Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personnalisé pour un design moderne
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stMetric {
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        padding: 20px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    .stMetric label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem;
        font-weight: 700;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
    }
    .block-container {
        padding-top: 2rem;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        backdrop-filter: blur(10px);
    }
    .stSelectbox label, .stMultiSelect label, .stSlider label {
        color: #ffffff !important;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('7_l2ep_leaf.ppc_2025_02_07_14_41_42 pn.csv')
    df['Timestamp'] = pd.to_datetime(df['Time'], unit='s', origin=datetime.now())
    df = df[(df['GPSLat'] != 0) & (df['GPSLon'] != 0)]
    
    # Calcul de métriques supplémentaires
    df['Energy_Consumption'] = df['HVBVoltage'] * df['MotTorque'] / 1000
    df['Efficiency'] = df['VehSpeed'] / (df['Energy_Consumption'] + 0.001)
    
    return df

def create_sidebar(df):
    with st.sidebar:
        st.markdown("### 🎛️ Panneau de Contrôle")
        st.markdown("---")
        
        min_time = df['Time'].min()
        max_time = df['Time'].max()
        time_range = st.slider(
            "⏱️ Période d'analyse",
            min_value=float(min_time),
            max_value=float(max_time),
            value=(float(min_time), float(max_time)),
            help="Sélectionnez la plage temporelle à analyser"
        )
        
        st.markdown("---")
        parameters = {
            'VehSpeed': '🏎️ Vitesse',
            'AccelPedal': '⚡ Accélération',
            'MotTorque': '🔧 Couple moteur',
            'HVBSOC': '🔋 État de charge',
            'HVBTemp': '🌡️ Température batterie',
            'HVBVoltage': '⚙️ Voltage'
        }
        
        selected_params = st.multiselect(
            "📊 Métriques à afficher",
            options=list(parameters.keys()),
            default=['VehSpeed', 'HVBSOC'],
            format_func=lambda x: parameters[x]
        )
        
        st.markdown("---")
        view_mode = st.radio(
            "👁️ Mode d'affichage",
            ["Vue synthétique", "Vue détaillée", "Analyse énergétique"],
            help="Choisissez le niveau de détail"
        )
        
    return time_range, selected_params, view_mode

def render_hero_metrics(df):
    st.markdown("### 📈 Vue d'ensemble de la session")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "🏁 Vitesse Max",
            f"{df['VehSpeed'].max():.0f} km/h",
            delta=f"+{df['VehSpeed'].max() - df['VehSpeed'].mean():.0f} vs moy"
        )
    
    with col2:
        st.metric(
            "🔋 SOC Moyen",
            f"{df['HVBSOC'].mean():.1f}%",
            delta=f"{df['HVBSOC'].iloc[-1] - df['HVBSOC'].iloc[0]:.1f}%"
        )
    
    with col3:
        st.metric(
            "🌡️ Temp Max",
            f"{df['HVBTemp'].max():.1f}°C",
            delta="Optimal" if df['HVBTemp'].max() < 45 else "Élevée",
            delta_color="normal" if df['HVBTemp'].max() < 45 else "inverse"
        )
    
    with col4:
        distance = df['VehDistance'].iloc[-1] - df['VehDistance'].iloc[0]
        st.metric(
            "🛣️ Distance",
            f"{distance:.2f} km",
            delta=f"{(distance / (df['Time'].iloc[-1] - df['Time'].iloc[0]) * 3600):.0f} km/h moy"
        )
    
    with col5:
        energy_used = (df['HVBSOC'].iloc[0] - df['HVBSOC'].iloc[-1])
        if distance > 0:
            consumption = (energy_used / distance) * 100
            st.metric(
                "⚡ Consommation",
                f"{consumption:.1f} %/km",
                delta="Économique" if consumption < 15 else "Élevée",
                delta_color="normal" if consumption < 15 else "inverse"
            )

def render_interactive_map(df):
    st.markdown("### 🗺️ Trajectoire du Véhicule")
    
    # Options de personnalisation de la carte
    col_controls = st.columns([2, 1, 1, 1])
    with col_controls[0]:
        map_style = st.selectbox(
            "Style de carte",
            ["OpenStreetMap", "Satellite", "Terrain", "Dark Mode"],
            index=0
        )
    with col_controls[1]:
        show_heatmap = st.checkbox("Heatmap vitesse", value=False)
    with col_controls[2]:
        show_markers = st.checkbox("Marqueurs", value=True)
    with col_controls[3]:
        animate_route = st.checkbox("Animation", value=False)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Calculer le centre et les limites de la carte
        avg_lat = df['GPSLat'].mean()
        avg_lon = df['GPSLon'].mean()
        
        # Calculer les limites pour ajuster le zoom automatiquement
        lat_range = df['GPSLat'].max() - df['GPSLat'].min()
        lon_range = df['GPSLon'].max() - df['GPSLon'].min()
        
        # Déterminer le zoom approprié basé sur l'étendue du trajet
        if lat_range < 0.01 and lon_range < 0.01:
            zoom_level = 15
        elif lat_range < 0.05 and lon_range < 0.05:
            zoom_level = 13
        else:
            zoom_level = 12
        
        # Sélection du style de carte
        tiles_map = {
            "OpenStreetMap": "OpenStreetMap",
            "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Terrain": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            "Dark Mode": "CartoDB dark_matter"
        }
        
        tile_layer = tiles_map[map_style]
        attr = '&copy; OpenStreetMap contributors' if map_style == "OpenStreetMap" else 'Tiles &copy; Esri'
        
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=zoom_level,
            tiles=tile_layer if map_style in ["OpenStreetMap", "Dark Mode"] else None,
            attr=attr
        )
        
        # Ajouter la couche satellite/terrain manuellement si nécessaire
        if map_style in ["Satellite", "Terrain"]:
            folium.TileLayer(
                tiles=tile_layer,
                attr=attr,
                name=map_style
            ).add_to(m)
        
        # Préparer les données de trajectoire avec gradient de couleur
        points = []
        for idx, row in df.iterrows():
            speed = row['VehSpeed']
            soc = row['HVBSOC']
            temp = row['HVBTemp']
            
            # Couleur basée sur la vitesse
            if speed < 20:
                color = '#00ff00'  # Vert
            elif speed < 40:
                color = '#7fff00'  # Vert-jaune
            elif speed < 60:
                color = '#ffff00'  # Jaune
            elif speed < 80:
                color = '#ff8c00'  # Orange
            else:
                color = '#ff0000'  # Rouge
            
            points.append({
                'lat': row['GPSLat'],
                'lon': row['GPSLon'],
                'speed': speed,
                'soc': soc,
                'temp': temp,
                'color': color,
                'time': row['Time'],
                'index': idx
            })
        
        # Dessiner la trajectoire avec segments colorés
        for i in range(len(points) - 1):
            segment = [
                [points[i]['lat'], points[i]['lon']],
                [points[i+1]['lat'], points[i+1]['lon']]
            ]
            
            folium.PolyLine(
                segment,
                color=points[i]['color'],
                weight=5,
                opacity=0.8,
                popup=f"Vitesse: {points[i]['speed']:.1f} km/h<br>SOC: {points[i]['soc']:.1f}%"
            ).add_to(m)
        
        # Heatmap de vitesse
        if show_heatmap:
            heat_data = [[p['lat'], p['lon'], p['speed']/100] for p in points]
            HeatMap(
                heat_data,
                radius=15,
                blur=20,
                gradient={0.4: 'blue', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}
            ).add_to(m)
        
        # Marqueurs de points d'intérêt
        if show_markers:
            # Point de départ
            folium.Marker(
                [points[0]['lat'], points[0]['lon']],
                popup=folium.Popup(f"""
                    <b>🟢 Point de Départ</b><br>
                    Vitesse: {points[0]['speed']:.1f} km/h<br>
                    SOC: {points[0]['soc']:.1f}%<br>
                    Température: {points[0]['temp']:.1f}°C
                """, max_width=250),
                icon=folium.Icon(color="green", icon="play", prefix='fa'),
                tooltip="Point de départ"
            ).add_to(m)
            
            # Point d'arrivée
            folium.Marker(
                [points[-1]['lat'], points[-1]['lon']],
                popup=folium.Popup(f"""
                    <b>🔴 Point d'Arrivée</b><br>
                    Vitesse: {points[-1]['speed']:.1f} km/h<br>
                    SOC: {points[-1]['soc']:.1f}%<br>
                    Température: {points[-1]['temp']:.1f}°C<br>
                    <br>
                    <b>Consommation totale:</b> {points[0]['soc'] - points[-1]['soc']:.1f}%
                """, max_width=250),
                icon=folium.Icon(color="red", icon="stop", prefix='fa'),
                tooltip="Point d'arrivée"
            ).add_to(m)
            
            # Trouver l'index de la vitesse maximale dans la liste de points
            max_speed_value = max(p['speed'] for p in points)
            max_speed_point = next(p for p in points if p['speed'] == max_speed_value)
            
            folium.Marker(
                [max_speed_point['lat'], max_speed_point['lon']],
                popup=folium.Popup(f"""
                    <b>🏎️ Vitesse Maximale</b><br>
                    Vitesse: {max_speed_point['speed']:.1f} km/h<br>
                    SOC: {max_speed_point['soc']:.1f}%
                """, max_width=200),
                icon=folium.Icon(color="orange", icon="bolt", prefix='fa'),
                tooltip=f"Vitesse max: {max_speed_point['speed']:.1f} km/h"
            ).add_to(m)
            
            # Marqueurs de points de recharge (si SOC augmente)
            try:
                for i in range(1, len(points)):
                    if points[i]['soc'] > points[i-1]['soc'] + 5:  # Augmentation significative
                        folium.Marker(
                            [points[i]['lat'], points[i]['lon']],
                            popup=f"⚡ Recharge détectée<br>SOC: {points[i]['soc']:.1f}%",
                            icon=folium.Icon(color="blue", icon="battery-full", prefix='fa'),
                            tooltip="Point de recharge"
                        ).add_to(m)
            except:
                pass  # Ignorer si erreur de détection de recharge
        
        # Animation de la trajectoire
        if animate_route:
            coords = [[p['lat'], p['lon']] for p in points]
            AntPath(
                coords,
                color='#ffffff',
                weight=3,
                opacity=0.8,
                delay=800
            ).add_to(m)
        
        # Ajouter un contrôle de couches
        folium.LayerControl().add_to(m)
        
        # Ajuster automatiquement les limites de la carte pour voir tout le trajet
        bounds = [
            [df['GPSLat'].min(), df['GPSLon'].min()],
            [df['GPSLat'].max(), df['GPSLon'].max()]
        ]
        m.fit_bounds(bounds, padding=(30, 30))
        
        # Légende de vitesse
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; 
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 2px solid grey; 
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 14px;
                    z-index: 9999;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            <p style="margin: 0; font-weight: bold; text-align: center;">Légende Vitesse</p>
            <p style="margin: 5px 0;"><span style="color: #00ff00;">●</span> &lt; 20 km/h</p>
            <p style="margin: 5px 0;"><span style="color: #7fff00;">●</span> 20-40 km/h</p>
            <p style="margin: 5px 0;"><span style="color: #ffff00;">●</span> 40-60 km/h</p>
            <p style="margin: 5px 0;"><span style="color: #ff8c00;">●</span> 60-80 km/h</p>
            <p style="margin: 5px 0;"><span style="color: #ff0000;">●</span> &gt; 80 km/h</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        folium_static(m, width=900, height=600)
    
    with col2:
        st.markdown("#### 📍 Statistiques GPS")
        
        # Calculer la distance totale approximative
        total_distance = df['VehDistance'].iloc[-1] - df['VehDistance'].iloc[0]
        
        st.info(f"""
        **Localisation:** Lille, France 🇫🇷
        
        **Points enregistrés:** {len(df)}
        
        **Distance parcourue:** {total_distance:.2f} km
        
        **Latitude:**
        - Moyenne: {df['GPSLat'].mean():.6f}
        - Écart-type: {df['GPSLat'].std():.6f}
        - Min: {df['GPSLat'].min():.6f}
        - Max: {df['GPSLat'].max():.6f}
        
        **Longitude:**
        - Moyenne: {df['GPSLon'].mean():.6f}
        - Écart-type: {df['GPSLon'].std():.6f}
        - Min: {df['GPSLon'].min():.6f}
        - Max: {df['GPSLon'].max():.6f}
        
        **Zone couverte:**
        - Étendue lat: {(df['GPSLat'].max() - df['GPSLat'].min()) * 111:.2f} km
        - Étendue lon: {(df['GPSLon'].max() - df['GPSLon'].min()) * 111 * np.cos(np.radians(df['GPSLat'].mean())):.2f} km
        """)

def render_statistical_analysis(df):
    st.markdown("### 📊 Analyse Statistique Descriptive")
    
    # Sélection des paramètres principaux à analyser
    params_to_analyze = {
        'VehSpeed': 'Vitesse (km/h)',
        'HVBSOC': 'État de charge (%)',
        'HVBTemp': 'Température batterie (°C)',
        'HVBVoltage': 'Voltage (V)',
        'MotTorque': 'Couple moteur (Nm)',
        'AccelPedal': 'Pédale accélération (%)',
        'HVBCurrent': 'Courant batterie (A)'
    }
    
    # Calcul des statistiques descriptives
    stats_data = []
    for param, label in params_to_analyze.items():
        if param in df.columns:
            stats_data.append({
                'Paramètre': label,
                'Moyenne': f"{df[param].mean():.2f}",
                'Médiane': f"{df[param].median():.2f}",
                'Écart-type': f"{df[param].std():.2f}",
                'Min': f"{df[param].min():.2f}",
                'Max': f"{df[param].max():.2f}",
                'Q1 (25%)': f"{df[param].quantile(0.25):.2f}",
                'Q3 (75%)': f"{df[param].quantile(0.75):.2f}",
                'Variance': f"{df[param].var():.2f}"
            })
    
    stats_df = pd.DataFrame(stats_data)
    
    # Affichage du tableau
    st.dataframe(
        stats_df,
        use_container_width=True,
        height=400
    )
    
    # Visualisations statistiques
    col1, col2 = st.columns(2)
    
    with col1:
        # Box plots pour visualiser la distribution
        st.markdown("#### 📦 Distribution des Variables")
        
        selected_var = st.selectbox(
            "Choisir une variable",
            options=list(params_to_analyze.keys()),
            format_func=lambda x: params_to_analyze[x],
            key="boxplot_selector"
        )
        
        if selected_var in df.columns:
            fig_box = go.Figure()
            fig_box.add_trace(go.Box(
                y=df[selected_var],
                name=params_to_analyze[selected_var],
                marker_color='#667eea',
                boxmean='sd'
            ))
            
            fig_box.update_layout(
                title=f"Distribution: {params_to_analyze[selected_var]}",
                yaxis_title=params_to_analyze[selected_var],
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_box, use_container_width=True)
    
    with col2:
        # Histogramme avec courbe de densité
        st.markdown("#### 📈 Histogramme & Densité")
        
        selected_var_hist = st.selectbox(
            "Choisir une variable",
            options=list(params_to_analyze.keys()),
            format_func=lambda x: params_to_analyze[x],
            key="hist_selector"
        )
        
        if selected_var_hist in df.columns:
            fig_hist = go.Figure()
            
            fig_hist.add_trace(go.Histogram(
                x=df[selected_var_hist],
                name='Fréquence',
                marker_color='#764ba2',
                opacity=0.7,
                nbinsx=30
            ))
            
            fig_hist.update_layout(
                title=f"Histogramme: {params_to_analyze[selected_var_hist]}",
                xaxis_title=params_to_analyze[selected_var_hist],
                yaxis_title="Fréquence",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
    
    # Matrice de corrélation
    st.markdown("#### 🔗 Matrice de Corrélation")
    
    # Sélection des colonnes numériques pour la corrélation
    numeric_cols = [col for col in params_to_analyze.keys() if col in df.columns]
    corr_matrix = df[numeric_cols].corr()
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=[params_to_analyze[col] for col in corr_matrix.columns],
        y=[params_to_analyze[col] for col in corr_matrix.index],
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Corrélation")
    ))
    
    fig_corr.update_layout(
        title="Matrice de Corrélation entre Variables",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500,
        xaxis=dict(tickangle=-45)
    )
    
    st.plotly_chart(fig_corr, use_container_width=True)

def render_advanced_charts(df, selected_params):
    st.markdown("### 📊 Analyse Multi-Paramètres")
    
    # Graphique principal combiné
    fig = make_subplots(
        rows=len(selected_params),
        cols=1,
        subplot_titles=[param for param in selected_params],
        vertical_spacing=0.08
    )
    
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
    
    for idx, param in enumerate(selected_params):
        fig.add_trace(
            go.Scatter(
                x=df['Time'],
                y=df[param],
                name=param,
                mode='lines',
                line=dict(color=colors[idx % len(colors)], width=3),
                fill='tozeroy',
                fillcolor=f'rgba({int(colors[idx % len(colors)][1:3], 16)}, {int(colors[idx % len(colors)][3:5], 16)}, {int(colors[idx % len(colors)][5:7], 16)}, 0.2)'
            ),
            row=idx+1,
            col=1
        )
    
    fig.update_layout(
        height=300 * len(selected_params),
        showlegend=False,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    
    st.plotly_chart(fig, use_container_width=True)

def render_energy_analysis(df):
    st.markdown("### ⚡ Analyse Énergétique Avancée")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique de consommation d'énergie
        fig_energy = go.Figure()
        
        fig_energy.add_trace(go.Scatter(
            x=df['Time'],
            y=df['HVBSOC'],
            name='État de charge',
            mode='lines',
            line=dict(color='#43e97b', width=3),
            fill='tozeroy'
        ))
        
        fig_energy.update_layout(
            title="Évolution de l'État de Charge",
            xaxis_title="Temps (s)",
            yaxis_title="SOC (%)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig_energy, use_container_width=True)
    
    with col2:
        # Graphique température vs voltage
        fig_temp = go.Figure()
        
        fig_temp.add_trace(go.Scatter(
            x=df['Time'],
            y=df['HVBTemp'],
            name='Température',
            yaxis='y',
            line=dict(color='#fa709a', width=3)
        ))
        
        fig_temp.add_trace(go.Scatter(
            x=df['Time'],
            y=df['HVBVoltage'],
            name='Voltage',
            yaxis='y2',
            line=dict(color='#4facfe', width=3)
        ))
        
        fig_temp.update_layout(
            title="Température & Voltage Batterie",
            xaxis_title="Temps (s)",
            yaxis=dict(title="Température (°C)", titlefont=dict(color='#fa709a')),
            yaxis2=dict(title="Voltage (V)", overlaying='y', side='right', titlefont=dict(color='#4facfe')),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig_temp, use_container_width=True)

def main():
    # En-tête stylisé
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>
                ⚡ Electric Vehicle Telemetry
            </h1>
            <p style='font-size: 1.2rem; color: rgba(255,255,255,0.8);'>
                Analyse en temps réel des performances du véhicule électrique
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Chargement des données
    with st.spinner('🔄 Chargement des données de télémétrie...'):
        df = load_data()
    
    # Sidebar avec filtres
    time_range, selected_params, view_mode = create_sidebar(df)
    
    # Filtrage des données
    filtered_df = df[(df['Time'] >= time_range[0]) & (df['Time'] <= time_range[1])]
    
    # Métriques principales
    render_hero_metrics(filtered_df)
    
    st.markdown("---")
    
    # Carte interactive
    render_interactive_map(filtered_df)
    
    st.markdown("---")
    
    # Analyse statistique descriptive
    render_statistical_analysis(filtered_df)
    
    st.markdown("---")
    
    # Graphiques selon le mode sélectionné
    if view_mode == "Vue synthétique" or view_mode == "Vue détaillée":
        if selected_params:
            render_advanced_charts(filtered_df, selected_params)
        else:
            st.warning("⚠️ Veuillez sélectionner au moins un paramètre à visualiser")
    
    if view_mode == "Analyse énergétique":
        render_energy_analysis(filtered_df)
    
    # Données brutes (optionnel)
    with st.expander("🔍 Afficher les données brutes"):
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; padding: 1rem; color: rgba(255,255,255,0.6);'>
            <p>Développé avec ❤️ pour l'analyse de véhicules électriques | 
            Powered by Streamlit & Plotly</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
