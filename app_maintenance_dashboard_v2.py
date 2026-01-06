"""
Application Streamlit - Tableau de Bord Avancé des Interventions de Maintenance
Version 2.0 - Pôle Formation UIMM-CVDL

Fonctionnalités:
- Analyse complète des pièces de rechange
- Taux de disponibilité et OEE
- Analyse de récurrence des pannes
- Performance des techniciens
- Analyse temporelle avancée (heatmap, saisonnalité)
- Export et impression des graphiques
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import calendar

# Configuration de la page
st.set_page_config(
    page_title="Tableau de Bord Maintenance - UIMM",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        margin: 0;
    }
    .sub-title {
        font-size: 1.1rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 24px;
        background-color: #f0f2f6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    .download-btn {
        background-color: #2ca02c;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        text-decoration: none;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Charge les données nettoyées des interventions"""
    df = pd.read_csv('interventions_2024_clean.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def parse_pieces(pieces_str):
    """Parse le champ Pieces_Changees pour extraire les pièces individuelles"""
    if pd.isna(pieces_str) or pieces_str == 'Aucune':
        return []
    
    # Séparer par virgules
    pieces = [p.strip() for p in str(pieces_str).split(',')]
    return pieces

def analyze_pieces(df):
    """Analyse complète des pièces changées"""
    pieces_list = []
    
    for idx, row in df.iterrows():
        pieces = parse_pieces(row['Pieces_Changees'])
        for piece in pieces:
            if piece:
                pieces_list.append({
                    'Piece': piece,
                    'Machine': row['ID_Machine'],
                    'Type_Panne': row['Type_Panne'],
                    'Date': row['Date'],
                    'Technicien': row['Technicien']
                })
    
    pieces_df = pd.DataFrame(pieces_list)
    return pieces_df

def calculate_availability(df, periode_jours=365):
    """
    Calcule le taux de disponibilité par machine
    Disponibilité = (Temps total - Temps d'arrêt) / Temps total × 100
    """
    # Temps total disponible (24h/jour)
    temps_total = periode_jours * 24
    
    availability_data = []
    
    for machine in df['ID_Machine'].unique():
        machine_df = df[df['ID_Machine'] == machine]
        temps_arret = machine_df['Duree_Arret_h'].sum()
        disponibilite = ((temps_total - temps_arret) / temps_total) * 100
        
        # Catégorie de la machine (CMP, MOT, CVY, etc.)
        categorie = machine.split('-')[0]
        
        availability_data.append({
            'Machine': machine,
            'Categorie': categorie,
            'Temps_Arret_h': temps_arret,
            'Disponibilite_%': disponibilite,
            'Nb_Interventions': len(machine_df)
        })
    
    return pd.DataFrame(availability_data)

def calculate_oee(df):
    """
    Calcule un OEE simplifié
    OEE = Disponibilité × Performance × Qualité
    Ici simplifié: OEE ≈ Disponibilité (en supposant performance et qualité = 100%)
    """
    availability_df = calculate_availability(df)
    availability_df['OEE_%'] = availability_df['Disponibilite_%']  # Simplifié
    return availability_df

def analyze_recurrence(df):
    """Analyse la récurrence des pannes"""
    recurrence_data = []
    
    for machine in df['ID_Machine'].unique():
        machine_df = df[df['ID_Machine'] == machine].sort_values('Date')
        
        # Analyser chaque type de panne
        for panne_type in machine_df['Type_Panne'].dropna().unique():
            panne_df = machine_df[machine_df['Type_Panne'] == panne_type].copy()
            
            if len(panne_df) > 1:
                # Calculer les délais entre récurrences
                panne_df['Date_Next'] = panne_df['Date'].shift(-1)
                panne_df['Delai_Recurrence_jours'] = (panne_df['Date_Next'] - panne_df['Date']).dt.days
                
                delai_moyen = panne_df['Delai_Recurrence_jours'].mean()
                
                recurrence_data.append({
                    'Machine': machine,
                    'Type_Panne': panne_type,
                    'Nb_Occurrences': len(panne_df),
                    'Delai_Moyen_jours': delai_moyen,
                    'Score_Recurrence': len(panne_df) / (delai_moyen + 1) if delai_moyen > 0 else len(panne_df)
                })
    
    recurrence_df = pd.DataFrame(recurrence_data)
    return recurrence_df.sort_values('Score_Recurrence', ascending=False)

def analyze_technician_performance(df):
    """Analyse de la performance des techniciens"""
    tech_stats = []
    
    for tech in df['Technicien'].unique():
        tech_df = df[df['Technicien'] == tech]
        
        # Temps moyen d'intervention
        temps_moyen = tech_df['Duree_Arret_h'].mean()
        
        # Spécialisation (type de panne le plus fréquent)
        specialisation = tech_df['Type_Panne'].value_counts().index[0] if len(tech_df['Type_Panne'].value_counts()) > 0 else 'N/A'
        
        # Nombre d'interventions
        nb_interventions = len(tech_df)
        
        # Répartition temporelle (écart-type des dates)
        tech_df_sorted = tech_df.sort_values('Date')
        if len(tech_df_sorted) > 1:
            tech_df_sorted['Days_Between'] = tech_df_sorted['Date'].diff().dt.days
            regularite = tech_df_sorted['Days_Between'].std()
        else:
            regularite = 0
        
        tech_stats.append({
            'Technicien': tech,
            'Nb_Interventions': nb_interventions,
            'Temps_Moyen_h': temps_moyen,
            'Specialisation': specialisation,
            'Regularite': regularite,
            'Temps_Total_h': tech_df['Duree_Arret_h'].sum()
        })
    
    return pd.DataFrame(tech_stats).sort_values('Nb_Interventions', ascending=False)

def create_heatmap_calendar(df):
    """Crée une heatmap calendaire des interventions"""
    # Ajouter colonnes jour de semaine, semaine, mois
    df_temp = df.copy()
    df_temp['Jour_Semaine'] = df_temp['Date'].dt.day_name()
    df_temp['Semaine'] = df_temp['Date'].dt.isocalendar().week
    df_temp['Mois'] = df_temp['Date'].dt.month_name()
    
    # Compter interventions par jour de la semaine
    jour_semaine_ordre = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    jour_semaine_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    
    day_counts = df_temp['Jour_Semaine'].value_counts().reindex(jour_semaine_ordre, fill_value=0)
    
    fig = go.Figure(data=[go.Bar(
        x=jour_semaine_fr,
        y=day_counts.values,
        marker_color=['#d62728' if i in [5, 6] else '#1f77b4' for i in range(7)],
        text=day_counts.values,
        textposition='auto'
    )])
    
    fig.update_layout(
        title='Répartition des Interventions par Jour de la Semaine',
        xaxis_title='Jour',
        yaxis_title='Nombre d\'interventions',
        showlegend=False,
        height=400
    )
    
    return fig

def create_seasonal_analysis(df):
    """Analyse saisonnière des interventions"""
    df_temp = df.copy()
    df_temp['Mois'] = df_temp['Date'].dt.month
    df_temp['Mois_Nom'] = df_temp['Date'].dt.month_name()
    
    monthly_counts = df_temp.groupby('Mois').size().reset_index(name='Nb_Interventions')
    monthly_counts['Mois_Nom'] = monthly_counts['Mois'].apply(lambda x: calendar.month_name[x])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_counts['Mois_Nom'],
        y=monthly_counts['Nb_Interventions'],
        mode='lines+markers',
        marker=dict(size=12, color='#1f77b4'),
        line=dict(width=3, color='#1f77b4'),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)'
    ))
    
    fig.update_layout(
        title='Évolution Saisonnière des Interventions',
        xaxis_title='Mois',
        yaxis_title='Nombre d\'interventions',
        hovermode='x unified',
        height=400
    )
    
    return fig

def get_image_base64(image_path):
    """Convertit une image en base64 pour l'affichage dans Streamlit"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def create_parts_frequency_chart(pieces_df):
    """Top 10 des pièces les plus remplacées"""
    piece_counts = pieces_df['Piece'].value_counts().head(10).reset_index()
    piece_counts.columns = ['Piece', 'Frequence']
    
    fig = px.bar(
        piece_counts,
        x='Frequence',
        y='Piece',
        orientation='h',
        title='Top 10 des Pièces les Plus Remplacées',
        color='Frequence',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=500,
        showlegend=False
    )
    
    return fig

def create_parts_crossanalysis(pieces_df):
    """Analyse croisée pièces / types de pannes"""
    if len(pieces_df) == 0:
        return None
    
    # Top 5 pièces
    top_pieces = pieces_df['Piece'].value_counts().head(5).index.tolist()
    
    # Filtrer sur les top pièces
    pieces_top = pieces_df[pieces_df['Piece'].isin(top_pieces)]
    
    # Compter par pièce et type de panne
    cross_data = pieces_top.groupby(['Piece', 'Type_Panne']).size().reset_index(name='Count')
    
    fig = px.sunburst(
        cross_data,
        path=['Piece', 'Type_Panne'],
        values='Count',
        title='Analyse Croisée: Pièces et Types de Pannes'
    )
    
    fig.update_layout(height=600)
    
    return fig

# ========== APPLICATION PRINCIPALE ==========

def main():
    # En-tête avec logo
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        try:
            logo = Image.open('logo_uimm_placeholder.jpg')
            st.image(logo, width=150)
        except:
            st.write("🏭")
    
    with col_title:
        st.markdown("""
            <div class="main-header">
                <div class="main-title">🔧 Tableau de Bord Maintenance Industrielle</div>
                <div class="sub-title">Pôle Formation UIMM-CVDL</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Chargement des données
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {e}")
        st.stop()
    
    # ========== BARRE LATÉRALE - FILTRES ==========
    st.sidebar.header("🎯 Filtres de Données")
    
    # Filtre de dates
    st.sidebar.subheader("📅 Période")
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Sélectionnez la période",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Filtre Type de panne
    st.sidebar.subheader("⚠️ Type de Panne")
    all_fault_types = sorted(df['Type_Panne'].dropna().unique().tolist())
    selected_faults = st.sidebar.multiselect(
        "Type de panne (sélection multiple)",
        all_fault_types,
        default=all_fault_types
    )
    
    # Filtre Technicien
    st.sidebar.subheader("👨‍🔧 Technicien")
    all_technicians = sorted(df['Technicien'].unique().tolist())
    selected_techs = st.sidebar.multiselect(
        "Technicien (sélection multiple)",
        all_technicians,
        default=all_technicians
    )
    
    # Filtre Machine
    st.sidebar.subheader("🏭 Machine")
    all_machines = sorted(df['ID_Machine'].unique().tolist())
    selected_machines = st.sidebar.multiselect(
        "Machine (sélection multiple)",
        all_machines,
        default=all_machines
    )
    
    # Application des filtres
    df_filtered = df.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df_filtered[
            (df_filtered['Date'].dt.date >= start_date) &
            (df_filtered['Date'].dt.date <= end_date)
        ]
    
    if selected_faults:
        df_filtered = df_filtered[df_filtered['Type_Panne'].isin(selected_faults)]
    
    if selected_techs:
        df_filtered = df_filtered[df_filtered['Technicien'].isin(selected_techs)]
    
    if selected_machines:
        df_filtered = df_filtered[df_filtered['ID_Machine'].isin(selected_machines)]
    
    # Affichage du nombre de résultats
    st.sidebar.markdown("---")
    st.sidebar.metric("📊 Interventions filtrées", len(df_filtered))
    st.sidebar.metric("📊 Total interventions", len(df))
    
    # ========== ONGLETS PRINCIPAUX ==========
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Vue d'ensemble",
        "🔩 Analyse des Pièces",
        "📈 Disponibilité & OEE",
        "🔄 Récurrence des Pannes",
        "👨‍🔧 Performance Techniciens",
        "📅 Analyse Temporelle"
    ])
    
    # ========== ONGLET 1: VUE D'ENSEMBLE ==========
    with tab1:
        st.header("📊 Indicateurs Clés de Performance")
        
        # Calcul des indicateurs
        mttr = df_filtered['Duree_Arret_h'].mean()
        total_interventions = len(df_filtered)
        total_downtime = df_filtered['Duree_Arret_h'].sum()
        nb_machines = df_filtered['ID_Machine'].nunique()
        
        # Calcul MTBF
        mtbf_list = []
        for machine in df_filtered['ID_Machine'].unique():
            machine_df = df_filtered[df_filtered['ID_Machine'] == machine].sort_values('Date')
            if len(machine_df) > 1:
                machine_df = machine_df.copy()
                machine_df['Date_Next'] = machine_df['Date'].shift(-1)
                machine_df['Time_Between'] = (machine_df['Date_Next'] - machine_df['Date']).dt.total_seconds() / 3600
                mtbf_list.append(machine_df['Time_Between'].mean())
        
        mtbf = np.mean(mtbf_list) if mtbf_list else 0
        
        # Affichage en colonnes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="⏱️ MTTR (Temps Moyen de Réparation)",
                value=f"{mttr:.2f}h",
                help="Mean Time To Repair"
            )
        
        with col2:
            st.metric(
                label="🔄 MTBF (Temps Entre Pannes)",
                value=f"{mtbf:.1f}h" if mtbf > 0 else "N/A",
                help="Mean Time Between Failures"
            )
        
        with col3:
            st.metric(
                label="📈 Total Interventions",
                value=total_interventions
            )
        
        with col4:
            st.metric(
                label="⏰ Temps d'Arrêt Total",
                value=f"{total_downtime:.1f}h"
            )
        
        st.markdown("---")
        
        # Diagramme de Pareto
        st.subheader("📊 Diagramme de Pareto - Machines Critiques")
        
        if len(df_filtered) > 0:
            machine_counts = df_filtered['ID_Machine'].value_counts().reset_index()
            machine_counts.columns = ['Machine', 'Nb_Interventions']
            machine_counts['Cumul'] = machine_counts['Nb_Interventions'].cumsum()
            machine_counts['Pourcentage_Cumul'] = (machine_counts['Cumul'] / machine_counts['Nb_Interventions'].sum()) * 100
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=machine_counts['Machine'],
                y=machine_counts['Nb_Interventions'],
                name='Nombre d\'interventions',
                marker_color='#1f77b4',
                yaxis='y'
            ))
            
            fig.add_trace(go.Scatter(
                x=machine_counts['Machine'],
                y=machine_counts['Pourcentage_Cumul'],
                name='Pourcentage cumulé',
                marker_color='#ff7f0e',
                yaxis='y2',
                mode='lines+markers',
                line=dict(width=3)
            ))
            
            fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%", yref='y2')
            
            fig.update_layout(
                xaxis=dict(title='Machine', tickangle=-45),
                yaxis=dict(title='Nombre d\'interventions', side='left'),
                yaxis2=dict(title='Pourcentage cumulé (%)', overlaying='y', side='right', range=[0, 100]),
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== ONGLET 2: ANALYSE DES PIÈCES ==========
    with tab2:
        st.header("🔩 Analyse des Pièces de Rechange")
        
        pieces_df = analyze_pieces(df_filtered)
        
        if len(pieces_df) > 0:
            # KPIs pièces
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🔧 Pièces Uniques", pieces_df['Piece'].nunique())
            
            with col2:
                st.metric("📦 Total Remplacements", len(pieces_df))
            
            with col3:
                piece_la_plus_changee = pieces_df['Piece'].value_counts().index[0]
                st.metric("🏆 Pièce la Plus Changée", piece_la_plus_changee[:30] + "..." if len(piece_la_plus_changee) > 30 else piece_la_plus_changee)
            
            st.markdown("---")
            
            # Top 10 pièces
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Top 10 des Pièces les Plus Remplacées")
                fig_freq = create_parts_frequency_chart(pieces_df)
                st.plotly_chart(fig_freq, use_container_width=True)
            
            with col2:
                st.subheader("🎯 Stock Critique - Pièces Prioritaires")
                
                # Identification stock critique (>= 5 remplacements)
                piece_counts = pieces_df['Piece'].value_counts().reset_index()
                piece_counts.columns = ['Piece', 'Frequence']
                stock_critique = piece_counts[piece_counts['Frequence'] >= 5]
                
                st.dataframe(
                    stock_critique.style.background_gradient(subset=['Frequence'], cmap='Reds'),
                    use_container_width=True,
                    height=400
                )
            
            # Analyse croisée
            st.markdown("---")
            st.subheader("🔀 Analyse Croisée: Pièces × Types de Pannes")
            
            fig_cross = create_parts_crossanalysis(pieces_df)
            if fig_cross:
                st.plotly_chart(fig_cross, use_container_width=True)
            
            # Taux de remplacement
            st.markdown("---")
            st.subheader("📈 Taux de Remplacement par Période")
            
            pieces_df_temp = pieces_df.copy()
            pieces_df_temp['Mois'] = pieces_df_temp['Date'].dt.to_period('M').astype(str)
            monthly_replacements = pieces_df_temp.groupby('Mois').size().reset_index(name='Nb_Remplacements')
            
            fig = px.line(
                monthly_replacements,
                x='Mois',
                y='Nb_Remplacements',
                markers=True,
                title='Évolution Mensuelle des Remplacements de Pièces'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune pièce changée dans la période sélectionnée")
    
    # ========== ONGLET 3: DISPONIBILITÉ & OEE ==========
    with tab3:
        st.header("📈 Taux de Disponibilité et OEE")
        
        availability_df = calculate_availability(df_filtered)
        oee_df = calculate_oee(df_filtered)
        
        # KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_disponibilite = availability_df['Disponibilite_%'].mean()
            st.metric("📊 Disponibilité Moyenne", f"{avg_disponibilite:.2f}%")
        
        with col2:
            avg_oee = oee_df['OEE_%'].mean()
            st.metric("⚙️ OEE Moyen", f"{avg_oee:.2f}%")
        
        with col3:
            worst_machine = availability_df.loc[availability_df['Disponibilite_%'].idxmin(), 'Machine']
            st.metric("⚠️ Machine la Moins Disponible", worst_machine)
        
        st.markdown("---")
        
        # Graphique disponibilité par machine
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏭 Disponibilité par Machine")
            
            fig = px.bar(
                availability_df.sort_values('Disponibilite_%'),
                x='Disponibilite_%',
                y='Machine',
                orientation='h',
                color='Disponibilite_%',
                color_continuous_scale=['red', 'yellow', 'green'],
                range_color=[0, 100]
            )
            
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Disponibilité par Catégorie")
            
            category_avail = availability_df.groupby('Categorie')['Disponibilite_%'].mean().reset_index()
            
            fig = px.bar(
                category_avail,
                x='Categorie',
                y='Disponibilite_%',
                color='Disponibilite_%',
                color_continuous_scale=['red', 'yellow', 'green'],
                range_color=[0, 100]
            )
            
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tableau détaillé
        st.markdown("---")
        st.subheader("📋 Tableau Détaillé - Disponibilité et OEE")
        
        st.dataframe(
            oee_df.style.background_gradient(subset=['Disponibilite_%', 'OEE_%'], cmap='RdYlGn', vmin=0, vmax=100)
                        .format({'Disponibilite_%': '{:.2f}%', 'OEE_%': '{:.2f}%', 'Temps_Arret_h': '{:.1f}h'}),
            use_container_width=True
        )
    
    # ========== ONGLET 4: RÉCURRENCE DES PANNES ==========
    with tab4:
        st.header("🔄 Analyse de Récurrence des Pannes")
        
        recurrence_df = analyze_recurrence(df_filtered)
        
        if len(recurrence_df) > 0:
            # KPIs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nb_recurrences = len(recurrence_df[recurrence_df['Nb_Occurrences'] >= 3])
                st.metric("⚠️ Pannes Récurrentes (≥3)", nb_recurrences)
            
            with col2:
                delai_moyen_global = recurrence_df['Delai_Moyen_jours'].mean()
                st.metric("📅 Délai Moyen de Récurrence", f"{delai_moyen_global:.1f} jours")
            
            with col3:
                pire_recurrence = recurrence_df.iloc[0]
                st.metric("🔴 Machine la Plus Problématique", pire_recurrence['Machine'])
            
            st.markdown("---")
            
            # Top 15 pannes récurrentes
            st.subheader("🔝 Top 15 Pannes Récurrentes")
            
            top_recurrence = recurrence_df.head(15)
            
            fig = px.scatter(
                top_recurrence,
                x='Delai_Moyen_jours',
                y='Nb_Occurrences',
                size='Score_Recurrence',
                color='Machine',
                hover_data=['Type_Panne'],
                title='Score de Récurrence: Fréquence vs Délai',
                labels={'Delai_Moyen_jours': 'Délai Moyen (jours)', 'Nb_Occurrences': 'Nombre d\'Occurrences'}
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé
            st.markdown("---")
            st.subheader("📋 Détail des Pannes Récurrentes")
            
            st.dataframe(
                recurrence_df.head(20).style.background_gradient(subset=['Score_Recurrence'], cmap='Reds')
                                            .format({'Delai_Moyen_jours': '{:.1f}', 'Score_Recurrence': '{:.2f}'}),
                use_container_width=True
            )
            
            # Efficacité des réparations
            st.markdown("---")
            st.subheader("🔧 Efficacité des Réparations")
            
            st.info("""
            **Interprétation:**
            - ✅ Délai > 90 jours: Réparation efficace
            - ⚠️ Délai 30-90 jours: Réparation moyennement efficace  
            - ❌ Délai < 30 jours: Réparation peu efficace - Problème récurrent
            """)
            
            efficacite = recurrence_df.copy()
            efficacite['Efficacite'] = efficacite['Delai_Moyen_jours'].apply(
                lambda x: '✅ Efficace' if x > 90 else ('⚠️ Moyenne' if x > 30 else '❌ Faible')
            )
            
            fig = px.histogram(
                efficacite,
                x='Efficacite',
                color='Efficacite',
                title='Distribution de l\'Efficacité des Réparations',
                color_discrete_map={'✅ Efficace': 'green', '⚠️ Moyenne': 'orange', '❌ Faible': 'red'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune panne récurrente détectée dans la période sélectionnée")
    
    # ========== ONGLET 5: PERFORMANCE TECHNICIENS ==========
    with tab5:
        st.header("👨‍🔧 Performance et Analyse des Techniciens")
        
        tech_perf_df = analyze_technician_performance(df_filtered)
        
        if len(tech_perf_df) > 0:
            # KPIs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                technicien_le_plus_rapide = tech_perf_df.loc[tech_perf_df['Temps_Moyen_h'].idxmin(), 'Technicien']
                st.metric("⚡ Technicien le Plus Rapide", technicien_le_plus_rapide)
            
            with col2:
                charge_moyenne = tech_perf_df['Nb_Interventions'].mean()
                st.metric("⚖️ Charge Moyenne", f"{charge_moyenne:.1f} interventions")
            
            with col3:
                temps_moyen_global = tech_perf_df['Temps_Moyen_h'].mean()
                st.metric("⏱️ Temps Moyen Global", f"{temps_moyen_global:.2f}h")
            
            st.markdown("---")
            
            # Temps moyen par technicien
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("⏱️ Temps Moyen d'Intervention")
                
                fig = px.bar(
                    tech_perf_df.sort_values('Temps_Moyen_h'),
                    x='Temps_Moyen_h',
                    y='Technicien',
                    orientation='h',
                    color='Temps_Moyen_h',
                    color_continuous_scale='RdYlGn_r'
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📊 Charge de Travail")
                
                fig = px.bar(
                    tech_perf_df.sort_values('Nb_Interventions', ascending=True),
                    x='Nb_Interventions',
                    y='Technicien',
                    orientation='h',
                    color='Nb_Interventions',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Spécialisation
            st.markdown("---")
            st.subheader("🎯 Spécialisation des Techniciens")
            
            # Créer une matrice technicien × type de panne
            tech_panne_matrix = df_filtered.groupby(['Technicien', 'Type_Panne']).size().reset_index(name='Count')
            
            fig = px.density_heatmap(
                tech_panne_matrix,
                x='Type_Panne',
                y='Technicien',
                z='Count',
                color_continuous_scale='Blues',
                title='Matrice de Spécialisation: Techniciens × Types de Pannes'
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau récapitulatif
            st.markdown("---")
            st.subheader("📋 Tableau Récapitulatif Performance")
            
            st.dataframe(
                tech_perf_df.style.background_gradient(subset=['Temps_Moyen_h'], cmap='RdYlGn_r')
                                  .background_gradient(subset=['Nb_Interventions'], cmap='Blues')
                                  .format({
                                      'Temps_Moyen_h': '{:.2f}h',
                                      'Temps_Total_h': '{:.1f}h',
                                      'Regularite': '{:.1f}'
                                  }),
                use_container_width=True
            )
        else:
            st.info("Aucune données technicien dans la période sélectionnée")
    
    # ========== ONGLET 6: ANALYSE TEMPORELLE ==========
    with tab6:
        st.header("📅 Analyse Temporelle Avancée")
        
        # Heatmap jour de la semaine
        st.subheader("📊 Répartition par Jour de la Semaine")
        fig_heatmap = create_heatmap_calendar(df_filtered)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        st.markdown("---")
        
        # Analyse saisonnière
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌡️ Tendance Saisonnière")
            fig_seasonal = create_seasonal_analysis(df_filtered)
            st.plotly_chart(fig_seasonal, use_container_width=True)
        
        with col2:
            st.subheader("📈 Évolution Temporelle")
            
            daily_interventions = df_filtered.groupby(df_filtered['Date'].dt.date).size().reset_index()
            daily_interventions.columns = ['Date', 'Nb_Interventions']
            
            fig = px.area(
                daily_interventions,
                x='Date',
                y='Nb_Interventions',
                title='Évolution Quotidienne'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Analyse détaillée
        st.markdown("---")
        st.subheader("📊 Analyse par Période")
        
        df_temp = df_filtered.copy()
        df_temp['Jour_Semaine'] = df_temp['Date'].dt.day_name()
        df_temp['Mois'] = df_temp['Date'].dt.month_name()
        df_temp['Heure'] = df_temp['Date'].dt.hour
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top 3 Jours de la Semaine**")
            top_jours = df_temp['Jour_Semaine'].value_counts().head(3)
            for jour, count in top_jours.items():
                st.metric(jour, count)
        
        with col2:
            st.write("**Top 3 Mois de l'Année**")
            top_mois = df_temp['Mois'].value_counts().head(3)
            for mois, count in top_mois.items():
                st.metric(mois, count)
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: gray; padding: 1rem;'>
            <p>📊 Tableau de Bord Maintenance - Pôle Formation UIMM-CVDL</p>
            <p style='font-size: 0.8rem;'>Version 2.0 - Données 2024</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
