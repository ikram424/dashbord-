import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os

# Configuration moderne de la page
st.set_page_config(
    page_title="🚗 CUMIN EV Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personnalisé ultra-moderne avec animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .stMetric {
        background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
        padding: 1.5rem;
        border-radius: 20px;
        backdrop-filter: blur(20px);
        border: 2px solid rgba(255,255,255,0.25);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.5);
        border-color: rgba(255,255,255,0.4);
    }
    
    .stMetric label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.2rem;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
        text-shadow: 0 2px 15px rgba(0,0,0,0.3);
    }
    
    h1 {
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    .stAlert {
        background: linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0.1));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 15px;
        color: white !important;
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(30, 60, 114, 0.95), rgba(126, 34, 206, 0.95));
        backdrop-filter: blur(20px);
        border-right: 2px solid rgba(255,255,255,0.2);
    }
    
    .stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    .stExpander {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
    }
    
    .mode-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 1px;
        margin: 1rem 0;
    }
    
    .mode-public {
        background: linear-gradient(135deg, #43e97b, #38f9d7);
        color: #1a1a1a;
        box-shadow: 0 4px 15px rgba(67, 233, 123, 0.4);
    }
    
    .mode-expert {
        background: linear-gradient(135deg, #fa709a, #fee140);
        color: #1a1a1a;
        box-shadow: 0 4px 15px rgba(250, 112, 154, 0.4);
    }
    
    .section-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
        padding: 2rem;
        border-radius: 20px;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.2);
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]
    
    if not csv_files:
        return pd.DataFrame(), None
    
    csv_file = csv_files[0]
    
    try:
        df = pd.read_csv(csv_file)
        df.columns = df.columns.str.strip()
        
        if 'Time' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Time'], unit='s', origin=datetime.now())
        
        if 'GPSLat' in df.columns and 'GPSLon' in df.columns:
            df = df[(df['GPSLat'] != 0) & (df['GPSLon'] != 0)]
        
        return df, csv_file
        
    except Exception as e:
        return pd.DataFrame(), None

def create_modern_sidebar(df, mode):
    with st.sidebar:
        st.markdown("### 🎛️ Centre de Contrôle")
        st.markdown("---")
        
        # Sélection du mode avec style
        mode = st.radio(
            "**🎯 Mode d'Analyse**", 
            ["👥 Public", "🔧 Expert"],
            help="Public: Interface simplifiée | Expert: Analyse technique complète"
        )
        
        mode_clean = mode.split()[1]  # Extrait "Public" ou "Expert"
        
        st.markdown("---")
        
        if not df.empty and 'Time' in df.columns:
            st.markdown("#### ⏱️ Plage Temporelle")
            min_time = df['Time'].min()
            max_time = df['Time'].max()
            time_range = st.slider(
                "Période d'analyse (secondes)",
                min_value=float(min_time),
                max_value=float(max_time),
                value=(float(min_time), float(max_time)),
                label_visibility="collapsed"
            )
            
            if mode_clean == "Expert":
                st.markdown("---")
                st.markdown("#### 📊 Paramètres Techniques")
                parameters = {
                    'VehSpeed': '🏎️ Vitesse véhicule',
                    'AccelPedal': '⚡ Pédale accélérateur',
                    'MotTorque': '🔧 Couple moteur',
                    'MotSpeed': '🌀 Vitesse moteur',
                    'HVBSOC': '🔋 État de charge',
                    'HVBTemp': '🌡️ Température HV',
                    'HVBVoltage': '⚙️ Tension HV',
                    'HVBCurrent': '🔌 Courant HV',
                    'BrakePedal': '🛑 Pédale frein',
                    'SteerAngle': '🎯 Angle volant',
                    'ExtTemp': '🌤️ Temp. extérieure',
                    'IntTemp': '🏠 Temp. intérieure'
                }
                
                available_params = [k for k in parameters.keys() if k in df.columns]
                
                selected_params = st.multiselect(
                    "Sélectionnez les métriques",
                    options=available_params,
                    default=available_params[:3] if len(available_params) >= 3 else available_params,
                    format_func=lambda x: parameters.get(x, x),
                    label_visibility="collapsed"
                )
            else:
                selected_params = ['VehSpeed', 'AccelPedal', 'HVBSOC']
                
        else:
            time_range = (0, 1)
            selected_params = []
            mode_clean = "Public"
        
        st.markdown("---")
        st.markdown("""
            <div style='text-align: center; padding: 1rem; color: rgba(255,255,255,0.7);'>
                <p style='font-size: 0.8rem;'>
                    ⚡ Powered by CUMIN<br>
                    Plateforme d'analyse VE
                </p>
            </div>
        """, unsafe_allow_html=True)
            
    return time_range, selected_params, mode_clean

def render_hero_section():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem; 
                       background: linear-gradient(135deg, #ffffff, #a78bfa);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       background-clip: text;'>
                ⚡ CUMIN Dashboard
            </h1>
            <p style='font-size: 1.3rem; color: rgba(255,255,255,0.9); font-weight: 500;'>
                Plateforme d'Analyse de Télémétrie pour Véhicules Électriques
            </p>
            <p style='font-size: 1rem; color: rgba(255,255,255,0.7);'>
                Parcours d'Essai VE - Région Métropolitaine Européenne de Lille
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_advanced_gps_map(df, mode):
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### 🗺️ Cartographie Interactive du Parcours")
    
    # Données des parcours VE
    points_interet = [
        {"nom": "Mons-en-Barœul", "lat": 50.6410, "lon": 3.1105, "type": "ville", "icon": "home"},
        {"nom": "Hem", "lat": 50.6550, "lon": 3.1880, "type": "ville", "icon": "map-marker"},
        {"nom": "Sailly-lez-Lannoy", "lat": 50.6450, "lon": 3.2235, "type": "ville", "icon": "map-marker"},
        {"nom": "Forest-sur-Marque", "lat": 50.6338, "lon": 3.1893, "type": "ville", "icon": "map-marker"},
        {"nom": "Willems", "lat": 50.6320, "lon": 3.2384, "type": "ville", "icon": "map-marker"},
        {"nom": "Villeneuve-d'Ascq", "lat": 50.6224, "lon": 3.1445, "type": "ville", "icon": "map-marker"},
        {"nom": "🔌 Station de recharge", "lat": 50.6220, "lon": 3.1600, "type": "arret", "icon": "bolt"},
        {"nom": "Chéreng", "lat": 50.6110, "lon": 3.2070, "type": "ville", "icon": "map-marker"},
        {"nom": "Baisieux", "lat": 50.6080, "lon": 3.2345, "type": "ville", "icon": "map-marker"},
        {"nom": "Lezennes", "lat": 50.6155, "lon": 3.1130, "type": "ville", "icon": "map-marker"},
        {"nom": "Lesquin", "lat": 50.5890, "lon": 3.1190, "type": "ville", "icon": "map-marker"},
        {"nom": "Anstaing", "lat": 50.6050, "lon": 3.1910, "type": "ville", "icon": "map-marker"},
        {"nom": "Gruson", "lat": 50.5950, "lon": 3.2070, "type": "ville", "icon": "map-marker"},
        {"nom": "Bouvines", "lat": 50.5790, "lon": 3.1880, "type": "ville", "icon": "map-marker"}
    ]

    parcours_initial = [
        [50.6410, 3.1105], [50.6224, 3.1445], [50.6220, 3.1600],
        [50.6110, 3.2070], [50.6080, 3.2345]
    ]

    parcours_autoroute = [
        [50.6410, 3.1105], [50.6224, 3.1445], [50.6050, 3.1910],
        [50.5950, 3.2070], [50.5950, 3.2600], [50.6080, 3.2345]
    ]

    # Carte avec style moderne
    m = folium.Map(
        location=[50.62, 3.18],
        zoom_start=12,
        tiles='CartoDB dark_matter'
    )
    
    # Parcours avec style amélioré
    folium.PolyLine(
        parcours_initial,
        color='#667eea',
        weight=6,
        opacity=0.8,
        popup='<b>Parcours Initial</b>',
        tooltip='Parcours Initial (urbain)'
    ).add_to(m)
    
    folium.PolyLine(
        parcours_autoroute,
        color='#43e97b',
        weight=6,
        opacity=0.8,
        popup='<b>Parcours Autoroute VE</b>',
        tooltip='Parcours Autoroute (haute vitesse)'
    ).add_to(m)
    
    # Points d'intérêt stylisés
    for point in points_interet:
        if point["type"] == "arret":
            icon = folium.Icon(color='red', icon='bolt', prefix='fa')
        else:
            icon = folium.Icon(color='lightblue', icon='map-marker', prefix='fa')
        
        folium.Marker(
            location=[point["lat"], point["lon"]],
            popup=f"<b>{point['nom']}</b>",
            tooltip=point["nom"],
            icon=icon
        ).add_to(m)
    
    # Trajet réel avec gradient de couleur
    if not df.empty and 'GPSLat' in df.columns and 'GPSLon' in df.columns:
        points = list(zip(df['GPSLat'], df['GPSLon']))
        
        # Ligne principale du trajet
        
        # Marqueurs de départ et arrivée
        folium.Marker(
            points[0],
            popup='<b>🟢 Départ</b>',
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(m)
        
        folium.Marker(
            points[-1],
            popup='<b>🔴 Arrivée</b>',
            icon=folium.Icon(color='darkred', icon='flag-checkered', prefix='fa')
        ).add_to(m)
    
    # Légende moderne
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; 
                background: linear-gradient(135deg, rgba(30,60,114,0.95), rgba(126,34,206,0.95));
                backdrop-filter: blur(20px);
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                z-index: 9999; 
                font-size: 13px;
                padding: 20px;
                color: white;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
        <b style="font-size: 15px; text-transform: uppercase; letter-spacing: 1px;">🗺️ Légende</b><br><br>
        <div style="margin: 8px 0;">
            <span style="background: #667eea; width: 20px; height: 4px; display: inline-block; border-radius: 2px;"></span>
            <span style="margin-left: 10px;">Parcours Initial</span>
        </div>
        <div style="margin: 8px 0;">
            <span style="background: #43e97b; width: 20px; height: 4px; display: inline-block; border-radius: 2px;"></span>
            <span style="margin-left: 10px;">Parcours Autoroute</span>
        </div>
        <div style="margin: 8px 0;">
            <span style="background: #fa709a; width: 20px; height: 4px; display: inline-block; border-radius: 2px;"></span>
            <span style="margin-left: 10px;">Trajet Réel</span>
        </div>
        <div style="margin: 8px 0;">
            <i class="fa fa-bolt" style="color: red; width: 20px;"></i>
            <span style="margin-left: 10px;">Borne de recharge</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    folium_static(m, width=1200, height=600 if mode == "Expert" else 500)
    st.markdown("</div>", unsafe_allow_html=True)

def render_metrics_public(df):
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 Indicateurs Clés de Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'VehSpeed' in df.columns:
            avg_speed = df['VehSpeed'].mean()
            max_speed = df['VehSpeed'].max()
            delta = max_speed - avg_speed
            st.metric(
                "🚀 Vitesse",
                f"{avg_speed:.0f} km/h",
                f"Max: {max_speed:.0f} km/h"
            )
    
    with col2:
        if 'HVBSOC' in df.columns:
            soc_start = df['HVBSOC'].iloc[0]
            soc_end = df['HVBSOC'].iloc[-1]
            soc_used = soc_start - soc_end
            st.metric(
                "🔋 Batterie",
                f"{soc_end:.1f}%",
                f"-{soc_used:.1f}% utilisé",
                delta_color="inverse"
            )
    
    with col3:
        if 'VehDistance' in df.columns:
            distance = df['VehDistance'].iloc[-1] - df['VehDistance'].iloc[0]
            st.metric(
                "📏 Distance",
                f"{distance:.2f} km",
                "Parcourue"
            )
    
    with col4:
        if 'Time' in df.columns:
            duration_sec = df['Time'].iloc[-1] - df['Time'].iloc[0]
            duration_min = duration_sec / 60
            st.metric(
                "⏱️ Durée",
                f"{duration_min:.1f} min",
                f"{duration_sec:.0f}s total"
            )
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_metrics_expert(df):
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### 🔬 Métriques Techniques Avancées")
    
    # Première ligne
    cols1 = st.columns(4)
    
    metrics_row1 = []
    if 'MotTorque' in df.columns:
        metrics_row1.append(("⚙️ Couple moteur", f"{df['MotTorque'].mean():.1f} Nm", f"Max: {df['MotTorque'].max():.1f}"))
    if 'MotSpeed' in df.columns:
        metrics_row1.append(("🌀 Vitesse moteur", f"{df['MotSpeed'].mean():.0f} RPM", f"Max: {df['MotSpeed'].max():.0f}"))
    if 'HVBVoltage' in df.columns:
        metrics_row1.append(("⚡ Tension HV", f"{df['HVBVoltage'].mean():.1f} V", f"±{df['HVBVoltage'].std():.1f}V"))
    if 'HVBCurrent' in df.columns:
        metrics_row1.append(("🔌 Courant HV", f"{df['HVBCurrent'].mean():.1f} A", f"Max: {df['HVBCurrent'].max():.1f}"))
    
    for i, (label, value, delta) in enumerate(metrics_row1[:4]):
        with cols1[i]:
            st.metric(label, value, delta)
    
    # Deuxième ligne
    cols2 = st.columns(4)
    
    metrics_row2 = []
    if 'HVBTemp' in df.columns:
        temp_status = "Optimal" if df['HVBTemp'].max() < 45 else "Élevé"
        metrics_row2.append(("🌡️ Temp batterie", f"{df['HVBTemp'].mean():.1f}°C", temp_status))
    if 'ExtTemp' in df.columns:
        metrics_row2.append(("🌤️ Temp extérieure", f"{df['ExtTemp'].mean():.1f}°C", "Ambient"))
    if 'BrakePedal' in df.columns:
        brake_usage = (df['BrakePedal'] > 0).mean() * 100
        metrics_row2.append(("🛑 Usage frein", f"{brake_usage:.1f}%", "du temps"))
    if 'AccelPedal' in df.columns:
        accel_usage = (df['AccelPedal'] > 0).mean() * 100
        metrics_row2.append(("🚦 Accélération", f"{accel_usage:.1f}%", "du temps"))
    
    for i, (label, value, delta) in enumerate(metrics_row2[:4]):
        with cols2[i]:
            st.metric(label, value, delta)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_interactive_charts(df, selected_params, mode):
    if not selected_params:
        return
    
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### 📈 Analyse Temporelle des Paramètres")
    
    if mode == "Expert":
        # Mode expert: graphiques détaillés séparés
        cols = st.columns(2)
        for idx, param in enumerate(selected_params):
            if param in df.columns:
                with cols[idx % 2]:
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=df['Time'],
                        y=df[param],
                        name=param,
                        mode='lines',
                        line=dict(
                            color='#667eea' if idx % 2 == 0 else '#43e97b',
                            width=3
                        ),
                        fill='tozeroy',
                        fillcolor=f'rgba(102, 126, 234, 0.2)' if idx % 2 == 0 else 'rgba(67, 233, 123, 0.2)'
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text=f"<b>{param}</b>",
                            font=dict(size=16, color='white')
                        ),
                        xaxis_title="Temps (s)",
                        yaxis_title="Valeur",
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(255,255,255,0.05)',
                        font=dict(color='white', size=12),
                        height=350,
                        margin=dict(l=60, r=30, t=50, b=50),
                        xaxis=dict(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='rgba(255,255,255,0.1)'
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    else:
        # Mode public: graphique combiné normalisé
        fig = go.Figure()
        colors = ['#667eea', '#43e97b', '#fa709a', '#4facfe', '#f093fb']
        
        for idx, param in enumerate(selected_params):
            if param in df.columns:
                normalized = (df[param] - df[param].min()) / (df[param].max() - df[param].min() + 1e-10)
                fig.add_trace(go.Scatter(
                    x=df['Time'],
                    y=normalized,
                    name=param,
                    mode='lines',
                    line=dict(color=colors[idx % len(colors)], width=3)
                ))
        
        fig.update_layout(
            title=dict(
                text="<b>Évolution Comparative (Normalisée)</b>",
                font=dict(size=18, color='white')
            ),
            xaxis_title="Temps (s)",
            yaxis_title="Valeur Normalisée (0-1)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,0.05)',
            font=dict(color='white', size=12),
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.1)',
                bordercolor='rgba(255,255,255,0.3)',
                borderwidth=1
            ),
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_correlation_matrix(df):
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### 🔗 Matrice de Corrélation des Variables Clés")
    
    # Sélection des variables clés pour la corrélation
    key_variables = ['VehSpeed', 'AccelPedal', 'BrakePedal', 'MotTorque', 
                     'MotSpeed', 'HVBSOC', 'HVBTemp', 'HVBVoltage', 'HVBCurrent']
    
    # Filtrer uniquement les colonnes qui existent dans le dataframe
    available_vars = [var for var in key_variables if var in df.columns]
    
    if len(available_vars) < 2:
        st.warning("⚠️ Pas assez de variables disponibles pour calculer la corrélation.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Nettoyer les données : supprimer les colonnes avec variance nulle ou trop de NaN
    df_clean = df[available_vars].copy()
    
    # Supprimer les colonnes avec variance nulle (valeurs constantes)
    valid_cols = []
    for col in df_clean.columns:
        if df_clean[col].std() > 0 and df_clean[col].notna().sum() > 10:
            valid_cols.append(col)
    
    if len(valid_cols) < 2:
        st.warning("⚠️ Pas assez de variables avec des données valides pour calculer la corrélation.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    df_clean = df_clean[valid_cols]
    
    # Calculer la matrice de corrélation en ignorant les NaN
    corr_matrix = df_clean.corr(method='pearson', min_periods=10)
    
    # Remplacer les NaN restants par 0 pour l'affichage
    corr_matrix_display = corr_matrix.fillna(0)
    
    # Créer la heatmap avec Plotly
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_display.values,
        x=corr_matrix_display.columns,
        y=corr_matrix_display.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(corr_matrix_display.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(
            title=dict(text="Corrélation", side="right"),
            tickmode="linear",
            tick0=-1,
            dtick=0.5
        ),
        hovertemplate='%{x} ↔ %{y}<br>Corrélation: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Matrice de Corrélation de Pearson</b>",
            font=dict(size=18, color='white')
        ),
        xaxis_title="Variables",
        yaxis_title="Variables",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=11),
        height=600,
        width=800,
        xaxis=dict(tickangle=-45),
        yaxis=dict(autorange='reversed')
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Interprétation")
        st.markdown("""
        **Échelle de corrélation :**
        - 🔴 **1.0** : Corrélation positive parfaite
        - ⚪ **0.0** : Aucune corrélation
        - 🔵 **-1.0** : Corrélation négative parfaite
        
        **Relations clés à observer :**
        - 🏎️ Vitesse ↔ État de charge
        - ⚡ Accélération ↔ Couple moteur
        - 🔋 SOC ↔ Courant HV
        - 🌡️ Température ↔ Performance
        """)
        
        # Trouver les corrélations les plus fortes
        st.markdown("#### 🔍 Corrélations Significatives")
        
        # Récupérer les corrélations en excluant la diagonale
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                # Ignorer les NaN
                if not np.isnan(corr_val):
                    corr_pairs.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'corr': corr_val
                    })
        
        # Trier par valeur absolue de corrélation
        corr_pairs_sorted = sorted(corr_pairs, key=lambda x: abs(x['corr']), reverse=True)
        
        # Afficher les 5 plus fortes corrélations
        if corr_pairs_sorted:
            for pair in corr_pairs_sorted[:5]:
                emoji = "🔴" if pair['corr'] > 0 else "🔵"
                st.markdown(f"{emoji} **{pair['var1']}** ↔ **{pair['var2']}**: {pair['corr']:.2f}")
        else:
            st.info("Aucune corrélation significative détectée")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_data_table_expert(df):
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    
    with st.expander("📋 **Données Brutes & Statistiques**", expanded=False):
        tab1, tab2 = st.tabs(["📊 Données Complètes", "📈 Statistiques"])
        
        with tab1:
            st.info("💡 Affichage des données brutes du fichier de télémétrie")
            st.dataframe(df, use_container_width=True, height=400)
        
        with tab2:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            stats_df = df[numeric_cols].describe()
            st.info("📊 Statistiques descriptives des paramètres numériques")
            st.dataframe(stats_df, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Chargement des données
    df, csv_file = load_data()
    
    # Hero section
    render_hero_section()
    
    if df.empty:
        st.error("❌ Aucun fichier CSV trouvé. Veuillez placer un fichier de télémétrie dans le dossier.")
        st.info("💡 Le système attend un fichier CSV contenant les données de télémétrie.")
        return
    
    # Sidebar
    time_range, selected_params, mode = create_modern_sidebar(df, "Public")
    
    # Badge de mode
    mode_class = "mode-public" if mode == "Public" else "mode-expert"
    mode_icon = "👥" if mode == "Public" else "🔧"
    st.markdown(f"""
        <div style='text-align: center;'>
            <span class='mode-badge {mode_class}'>
                {mode_icon} MODE {mode.upper()}
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    # Filtrage des données
    if 'Time' in df.columns:
        filtered_df = df[(df['Time'] >= time_range[0]) & (df['Time'] <= time_range[1])]
    else:
        filtered_df = df
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Affichage des sections
    render_metrics_public(filtered_df)
    
    if mode == "Expert":
        render_metrics_expert(filtered_df)
    
    render_advanced_gps_map(filtered_df, mode)
    render_interactive_charts(filtered_df, selected_params, mode)
    
    if mode == "Expert":
        render_correlation_matrix(filtered_df)
        render_data_table_expert(filtered_df)
    
    # Footer élégant
    st.markdown("---")
    if csv_file and 'Time' in df.columns:
        st.markdown(f"""
            <div style='text-align: center; padding: 2rem 1rem; color: rgba(255,255,255,0.7);'>
                <div style='display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-bottom: 1rem;'>
                    <div>📁 <b>Fichier:</b> {csv_file}</div>
                    <div>📊 <b>Points:</b> {len(df):,}</div>
                    <div>⏰ <b>Durée:</b> {(df['Time'].iloc[-1] - df['Time'].iloc[0]) / 60:.1f} min</div>
                </div>
                <p style='font-size: 0.9rem; margin-top: 1rem;'>
                    Développé avec ❤️ pour l'analyse de véhicules électriques | 
                    Powered by CUMIN Analytics
                </p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()