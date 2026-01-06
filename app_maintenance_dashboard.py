"""
Application Streamlit - Tableau de Bord des Interventions de Maintenance
Fonctionnalités:
- Diagramme de Pareto par machine
- Filtres interactifs (dates, type de panne, technicien)
- Indicateurs MTBF et MTTR
- Visualisations complémentaires
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Tableau de Bord Maintenance",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Charge les données nettoyées des interventions"""
    df = pd.read_csv('interventions_2024_clean.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def calculate_mtbf_mttr(df):
    """
    Calcule les indicateurs MTBF et MTTR
    MTBF (Mean Time Between Failures): Temps moyen entre pannes
    MTTR (Mean Time To Repair): Temps moyen de réparation
    """
    
    # MTTR: Moyenne des durées d'arrêt
    mttr = df['Duree_Arret_h'].mean()
    
    # MTBF: Calcul par machine
    # On suppose qu'une machine fonctionne 24h/7j sauf pendant les arrêts
    mtbf_data = []
    
    for machine in df['ID_Machine'].unique():
        machine_df = df[df['ID_Machine'] == machine].sort_values('Date')
        
        if len(machine_df) > 1:
            # Calculer le temps entre interventions
            machine_df['Date_Next'] = machine_df['Date'].shift(-1)
            machine_df['Time_Between'] = (machine_df['Date_Next'] - machine_df['Date']).dt.total_seconds() / 3600
            
            # MTBF moyen pour cette machine
            avg_mtbf = machine_df['Time_Between'].mean()
            mtbf_data.append({
                'Machine': machine,
                'MTBF': avg_mtbf,
                'Nb_Interventions': len(machine_df)
            })
    
    mtbf_df = pd.DataFrame(mtbf_data)
    mtbf_global = mtbf_df['MTBF'].mean() if not mtbf_df.empty else 0
    
    return mttr, mtbf_global, mtbf_df

def create_pareto_chart(df):
    """Crée un diagramme de Pareto des machines"""
    
    # Compter les interventions par machine
    machine_counts = df['ID_Machine'].value_counts().reset_index()
    machine_counts.columns = ['Machine', 'Nb_Interventions']
    
    # Calculer le pourcentage cumulé
    machine_counts['Cumul'] = machine_counts['Nb_Interventions'].cumsum()
    machine_counts['Pourcentage_Cumul'] = (machine_counts['Cumul'] / machine_counts['Nb_Interventions'].sum()) * 100
    
    # Créer le graphique
    fig = go.Figure()
    
    # Barres pour le nombre d'interventions
    fig.add_trace(go.Bar(
        x=machine_counts['Machine'],
        y=machine_counts['Nb_Interventions'],
        name='Nombre d\'interventions',
        marker_color='#1f77b4',
        yaxis='y'
    ))
    
    # Courbe pour le pourcentage cumulé
    fig.add_trace(go.Scatter(
        x=machine_counts['Machine'],
        y=machine_counts['Pourcentage_Cumul'],
        name='Pourcentage cumulé',
        marker_color='#ff7f0e',
        yaxis='y2',
        mode='lines+markers',
        line=dict(width=3)
    ))
    
    # Ligne à 80% (règle de Pareto)
    fig.add_hline(
        y=80, 
        line_dash="dash", 
        line_color="red", 
        annotation_text="80%",
        yref='y2'
    )
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Diagramme de Pareto - Interventions par Machine',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f77b4'}
        },
        xaxis=dict(title='Machine', tickangle=-45),
        yaxis=dict(
            title='Nombre d\'interventions',
            side='left',
            showgrid=True
        ),
        yaxis2=dict(
            title='Pourcentage cumulé (%)',
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        hovermode='x unified',
        legend=dict(x=0.7, y=1.1, orientation='h'),
        height=500
    )
    
    return fig, machine_counts

def create_timeline_chart(df):
    """Crée un graphique temporel des interventions"""
    
    daily_interventions = df.groupby(df['Date'].dt.date).size().reset_index()
    daily_interventions.columns = ['Date', 'Nb_Interventions']
    
    fig = px.line(
        daily_interventions,
        x='Date',
        y='Nb_Interventions',
        title='Évolution temporelle des interventions',
        markers=True
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Nombre d\'interventions',
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_fault_distribution(df):
    """Crée un graphique de distribution des types de pannes"""
    
    fault_counts = df['Type_Panne'].value_counts().reset_index()
    fault_counts.columns = ['Type_Panne', 'Count']
    
    fig = px.pie(
        fault_counts,
        values='Count',
        names='Type_Panne',
        title='Distribution des Types de Pannes',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=450)
    
    return fig

def create_technician_workload(df):
    """Crée un graphique de la charge de travail par technicien"""
    
    tech_stats = df.groupby('Technicien').agg({
        'ID_Intervention': 'count',
        'Duree_Arret_h': 'sum'
    }).reset_index()
    tech_stats.columns = ['Technicien', 'Nb_Interventions', 'Heures_Totales']
    tech_stats = tech_stats.sort_values('Nb_Interventions', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=tech_stats['Technicien'],
        x=tech_stats['Nb_Interventions'],
        name='Nombre d\'interventions',
        orientation='h',
        marker_color='#2ca02c'
    ))
    
    fig.update_layout(
        title='Charge de Travail par Technicien',
        xaxis_title='Nombre d\'interventions',
        yaxis_title='Technicien',
        height=400,
        showlegend=False
    )
    
    return fig

# ========== APPLICATION PRINCIPALE ==========

def main():
    # En-tête
    st.markdown('<div class="main-header">🔧 Tableau de Bord - Maintenance 2024</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Chargement des données
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        st.stop()
    
    # ========== BARRE LATÉRALE - FILTRES ==========
    st.sidebar.header("🎯 Filtres")
    
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
    all_fault_types = ['Tous'] + sorted(df['Type_Panne'].dropna().unique().tolist())
    selected_fault = st.sidebar.selectbox(
        "Type de panne",
        all_fault_types
    )
    
    # Filtre Technicien
    st.sidebar.subheader("👨‍🔧 Technicien")
    all_technicians = ['Tous'] + sorted(df['Technicien'].unique().tolist())
    selected_tech = st.sidebar.selectbox(
        "Technicien",
        all_technicians
    )
    
    # Application des filtres
    df_filtered = df.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df_filtered[
            (df_filtered['Date'].dt.date >= start_date) &
            (df_filtered['Date'].dt.date <= end_date)
        ]
    
    if selected_fault != 'Tous':
        df_filtered = df_filtered[df_filtered['Type_Panne'] == selected_fault]
    
    if selected_tech != 'Tous':
        df_filtered = df_filtered[df_filtered['Technicien'] == selected_tech]
    
    # Affichage du nombre de résultats
    st.sidebar.markdown("---")
    st.sidebar.metric("📊 Interventions filtrées", len(df_filtered))
    st.sidebar.metric("📊 Total interventions", len(df))
    
    # ========== INDICATEURS PRINCIPAUX ==========
    st.header("📊 Indicateurs Clés")
    
    # Calcul des indicateurs
    mttr, mtbf, mtbf_df = calculate_mtbf_mttr(df_filtered)
    
    total_interventions = len(df_filtered)
    total_downtime = df_filtered['Duree_Arret_h'].sum()
    nb_machines = df_filtered['ID_Machine'].nunique()
    
    # Affichage en colonnes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔧 MTTR (heures)",
            value=f"{mttr:.2f}h",
            help="Mean Time To Repair - Temps moyen de réparation"
        )
    
    with col2:
        st.metric(
            label="⏱️ MTBF (heures)",
            value=f"{mtbf:.1f}h" if mtbf > 0 else "N/A",
            help="Mean Time Between Failures - Temps moyen entre pannes"
        )
    
    with col3:
        st.metric(
            label="📈 Total Interventions",
            value=total_interventions
        )
    
    with col4:
        st.metric(
            label="⏰ Temps d'arrêt total",
            value=f"{total_downtime:.1f}h"
        )
    
    st.markdown("---")
    
    # ========== DIAGRAMME DE PARETO ==========
    st.header("📊 Analyse de Pareto - Machines")
    
    if len(df_filtered) > 0:
        pareto_fig, pareto_data = create_pareto_chart(df_filtered)
        st.plotly_chart(pareto_fig, use_container_width=True)
        
        # Affichage du tableau récapitulatif
        with st.expander("📋 Tableau détaillé"):
            st.dataframe(
                pareto_data.style.format({
                    'Nb_Interventions': '{:.0f}',
                    'Pourcentage_Cumul': '{:.1f}%'
                }),
                use_container_width=True
            )
    else:
        st.warning("Aucune donnée à afficher avec les filtres sélectionnés.")
    
    st.markdown("---")
    
    # ========== VISUALISATIONS COMPLÉMENTAIRES ==========
    st.header("📈 Analyses Complémentaires")
    
    tab1, tab2, tab3 = st.tabs(["📅 Évolution Temporelle", "⚠️ Types de Pannes", "👨‍🔧 Techniciens"])
    
    with tab1:
        if len(df_filtered) > 0:
            timeline_fig = create_timeline_chart(df_filtered)
            st.plotly_chart(timeline_fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
    
    with tab2:
        if len(df_filtered) > 0 and df_filtered['Type_Panne'].notna().any():
            fault_fig = create_fault_distribution(df_filtered)
            st.plotly_chart(fault_fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
    
    with tab3:
        if len(df_filtered) > 0:
            tech_fig = create_technician_workload(df_filtered)
            st.plotly_chart(tech_fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
    
    st.markdown("---")
    
    # ========== TABLEAU DES DONNÉES ==========
    st.header("📋 Données Détaillées")
    
    with st.expander("Voir les données brutes"):
        st.dataframe(
            df_filtered.style.format({
                'Duree_Arret_h': '{:.2f}h'
            }),
            use_container_width=True
        )
        
        # Bouton de téléchargement
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger les données filtrées (CSV)",
            data=csv,
            file_name=f"interventions_filtrees_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
