import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Analyse de Maintenance - MTTR/MTBF",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("🔧 Analyse de Maintenance Industrielle")
st.markdown("### Dashboard interactif - MTTR, MTBF et Analyse Pareto")

# Fonction de chargement des données
@st.cache_data
def load_data():
    """Charge et prépare les données d'interventions"""
    try:
        df = pd.read_csv('interventions_2024_cleaned.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        # Remplacer les valeurs manquantes dans Type_Panne
        df['Type_Panne'] = df['Type_Panne'].fillna('Non spécifié')
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return None

# Fonction de calcul MTTR
def calculate_mttr(df):
    """Calcule le MTTR (Mean Time To Repair) par machine"""
    mttr_data = df.groupby('ID_Machine').agg({
        'Duree_Arret_h': ['sum', 'mean', 'count']
    }).reset_index()
    mttr_data.columns = ['ID_Machine', 'Temps_Arret_Total', 'MTTR', 'Nb_Interventions']
    return mttr_data

# Fonction de calcul MTBF
def calculate_mtbf(df):
    """Calcule le MTBF (Mean Time Between Failures) par machine"""
    # Hypothèse: 365 jours en 2024 = 8760 heures disponibles
    heures_disponibles = 8760
    
    mtbf_data = df.groupby('ID_Machine').agg({
        'Duree_Arret_h': 'sum',
        'ID_Intervention': 'count'
    }).reset_index()
    mtbf_data.columns = ['ID_Machine', 'Temps_Arret_Total', 'Nb_Interventions']
    
    # MTBF = (Temps disponible - Temps d'arrêt) / Nombre de pannes
    mtbf_data['MTBF'] = (heures_disponibles - mtbf_data['Temps_Arret_Total']) / mtbf_data['Nb_Interventions']
    
    # Calculer la disponibilité en %
    mtbf_data['Disponibilite_%'] = ((heures_disponibles - mtbf_data['Temps_Arret_Total']) / heures_disponibles) * 100
    
    return mtbf_data

# Fonction d'analyse Pareto
def calculate_pareto(df):
    """Calcule l'analyse Pareto pour identifier les machines critiques"""
    pareto_data = df.groupby('ID_Machine')['Duree_Arret_h'].sum().reset_index()
    pareto_data.columns = ['ID_Machine', 'Temps_Arret_Total']
    
    # Trier par temps d'arrêt décroissant
    pareto_data = pareto_data.sort_values('Temps_Arret_Total', ascending=False)
    
    # Calculer le pourcentage cumulé
    pareto_data['Cumul_Temps_Arret'] = pareto_data['Temps_Arret_Total'].cumsum()
    total_temps_arret = pareto_data['Temps_Arret_Total'].sum()
    pareto_data['Cumul_%'] = (pareto_data['Cumul_Temps_Arret'] / total_temps_arret) * 100
    pareto_data['%_Temps_Arret'] = (pareto_data['Temps_Arret_Total'] / total_temps_arret) * 100
    
    # Identifier les machines dans la zone 80%
    pareto_data['Zone_Critique'] = pareto_data['Cumul_%'] <= 80
    
    return pareto_data

# Fonction de visualisation Pareto
def plot_pareto_chart(pareto_data):
    """Crée le diagramme de Pareto avec courbe cumulative"""
    fig = go.Figure()
    
    # Barres - Temps d'arrêt par machine
    fig.add_trace(go.Bar(
        x=pareto_data['ID_Machine'],
        y=pareto_data['Temps_Arret_Total'],
        name='Temps d\'arrêt (h)',
        marker_color=['#e74c3c' if crit else '#3498db' for crit in pareto_data['Zone_Critique']],
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Temps d\'arrêt: %{y:.1f}h<extra></extra>'
    ))
    
    # Courbe cumulative
    fig.add_trace(go.Scatter(
        x=pareto_data['ID_Machine'],
        y=pareto_data['Cumul_%'],
        name='Cumul %',
        line=dict(color='#2ecc71', width=3),
        yaxis='y2',
        hovertemplate='<b>%{x}</b><br>Cumul: %{y:.1f}%<extra></extra>'
    ))
    
    # Ligne de référence 80%
    fig.add_hline(
        y=80, 
        line_dash="dash", 
        line_color="#f39c12",
        annotation_text="Seuil 80%",
        annotation_position="right",
        yref='y2'
    )
    
    # Configuration des axes
    fig.update_layout(
        title='Analyse Pareto - Machines Critiques (80/20)',
        xaxis=dict(title='ID Machine', tickangle=-45),
        yaxis=dict(title='Temps d\'arrêt (heures)', side='left'),
        yaxis2=dict(title='Pourcentage cumulé (%)', side='right', overlaying='y', range=[0, 105]),
        hovermode='x unified',
        legend=dict(x=0.7, y=1.1, orientation='h'),
        height=500,
        template='plotly_white'
    )
    
    return fig

# Chargement des données
df = load_data()

if df is not None:
    # SIDEBAR - Filtres
    st.sidebar.header("🔍 Filtres")
    
    # Filtre de dates
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    date_range = st.sidebar.date_input(
        "Plage de dates",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Filtre techniciens
    all_technicians = sorted(df['Technicien'].unique())
    selected_technicians = st.sidebar.multiselect(
        "Techniciens",
        options=all_technicians,
        default=all_technicians
    )
    
    # Filtre types de pannes
    all_failure_types = sorted(df['Type_Panne'].unique())
    selected_failure_types = st.sidebar.multiselect(
        "Types de pannes",
        options=all_failure_types,
        default=all_failure_types
    )
    
    # Bouton de réinitialisation
    if st.sidebar.button("🔄 Réinitialiser les filtres"):
        st.rerun()
    
    # Application des filtres
    df_filtered = df.copy()
    
    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['Date'].dt.date >= date_range[0]) &
            (df_filtered['Date'].dt.date <= date_range[1])
        ]
    
    if selected_technicians:
        df_filtered = df_filtered[df_filtered['Technicien'].isin(selected_technicians)]
    
    if selected_failure_types:
        df_filtered = df_filtered[df_filtered['Type_Panne'].isin(selected_failure_types)]
    
    # Vérifier si des données sont disponibles après filtrage
    if len(df_filtered) == 0:
        st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
    else:
        # MÉTRIQUES PRINCIPALES
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Interventions", f"{len(df_filtered):,}")
        
        with col2:
            total_downtime = df_filtered['Duree_Arret_h'].sum()
            st.metric("⏱️ Temps d'arrêt total", f"{total_downtime:,.1f} h")
        
        with col3:
            nb_machines = df_filtered['ID_Machine'].nunique()
            st.metric("🏭 Machines affectées", f"{nb_machines}")
        
        with col4:
            mttr_global = df_filtered['Duree_Arret_h'].mean()
            st.metric("🔧 MTTR moyen", f"{mttr_global:.2f} h")
        
        with col5:
            # MTBF moyen global
            heures_dispo = 8760
            temps_arret_par_machine = df_filtered.groupby('ID_Machine')['Duree_Arret_h'].sum()
            interventions_par_machine = df_filtered.groupby('ID_Machine').size()
            mtbf_machines = (heures_dispo - temps_arret_par_machine) / interventions_par_machine
            mtbf_global = mtbf_machines.mean()
            st.metric("⚡ MTBF moyen", f"{mtbf_global:.1f} h")
        
        st.divider()
        
        # ANALYSE PARETO
        st.header("📈 Analyse Pareto - Machines Critiques")
        
        pareto_data = calculate_pareto(df_filtered)
        
        # Afficher le graphique Pareto
        pareto_chart = plot_pareto_chart(pareto_data)
        st.plotly_chart(pareto_chart, use_container_width=True)
        
        # Tableau des machines critiques (zone 80%)
        critical_machines = pareto_data[pareto_data['Zone_Critique']].copy()
        nb_critical = len(critical_machines)
        pct_critical = (nb_critical / len(pareto_data)) * 100
        
        st.info(f"🎯 **{nb_critical} machines ({pct_critical:.1f}%)** représentent **80% du temps d'arrêt total**")
        
        st.subheader("🚨 Machines Critiques (Zone 80%)")
        critical_display = critical_machines[['ID_Machine', 'Temps_Arret_Total', '%_Temps_Arret', 'Cumul_%']].copy()
        critical_display.columns = ['Machine', 'Temps d\'arrêt (h)', '% du total', 'Cumul %']
        critical_display['Temps d\'arrêt (h)'] = critical_display['Temps d\'arrêt (h)'].round(2)
        critical_display['% du total'] = critical_display['% du total'].round(2)
        critical_display['Cumul %'] = critical_display['Cumul %'].round(2)
        
        st.dataframe(critical_display, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # TABLEAU MTTR/MTBF PAR MACHINE
        st.header("📋 Métriques MTTR/MTBF par Machine")
        
        mttr_data = calculate_mttr(df_filtered)
        mtbf_data = calculate_mtbf(df_filtered)
        
        # Fusionner les données
        metrics_data = pd.merge(mttr_data, mtbf_data[['ID_Machine', 'MTBF', 'Disponibilite_%']], on='ID_Machine')
        
        # Trier par temps d'arrêt total décroissant
        metrics_data = metrics_data.sort_values('Temps_Arret_Total', ascending=False)
        
        # Formater pour l'affichage
        metrics_display = metrics_data.copy()
        metrics_display['MTTR'] = metrics_display['MTTR'].round(2)
        metrics_display['MTBF'] = metrics_display['MTBF'].round(1)
        metrics_display['Disponibilite_%'] = metrics_display['Disponibilite_%'].round(2)
        metrics_display['Temps_Arret_Total'] = metrics_display['Temps_Arret_Total'].round(2)
        
        metrics_display.columns = [
            'Machine', 
            'Temps d\'arrêt total (h)', 
            'MTTR (h)', 
            'Nb interventions',
            'MTBF (h)',
            'Disponibilité (%)'
        ]
        
        st.dataframe(
            metrics_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Disponibilité (%)": st.column_config.ProgressColumn(
                    "Disponibilité (%)",
                    help="Pourcentage de disponibilité de la machine",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100,
                )
            }
        )
        
        # Bouton de téléchargement CSV
        csv = metrics_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les données (CSV)",
            data=csv,
            file_name=f"metriques_maintenance_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.divider()
        
        # VISUALISATIONS COMPLÉMENTAIRES
        st.header("📊 Analyses Complémentaires")
        
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            st.subheader("Distribution des Types de Pannes")
            failure_dist = df_filtered['Type_Panne'].value_counts().reset_index()
            failure_dist.columns = ['Type_Panne', 'Count']
            
            fig_pie = px.pie(
                failure_dist,
                values='Count',
                names='Type_Panne',
                title='Répartition des interventions par type de panne',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_viz2:
            st.subheader("Interventions par Technicien")
            tech_dist = df_filtered['Technicien'].value_counts().reset_index()
            tech_dist.columns = ['Technicien', 'Nb_Interventions']
            
            fig_bar = px.bar(
                tech_dist,
                x='Technicien',
                y='Nb_Interventions',
                title='Nombre d\'interventions par technicien',
                color='Nb_Interventions',
                color_continuous_scale='Blues'
            )
            fig_bar.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Timeline des interventions
        st.subheader("📅 Évolution Temporelle des Interventions")
        
        # Grouper par mois
        df_timeline = df_filtered.copy()
        df_timeline['Mois'] = df_timeline['Date'].dt.to_period('M').astype(str)
        timeline_data = df_timeline.groupby('Mois').agg({
            'ID_Intervention': 'count',
            'Duree_Arret_h': 'sum'
        }).reset_index()
        timeline_data.columns = ['Mois', 'Nb_Interventions', 'Temps_Arret_Total']
        
        fig_timeline = go.Figure()
        
        fig_timeline.add_trace(go.Bar(
            x=timeline_data['Mois'],
            y=timeline_data['Nb_Interventions'],
            name='Nb interventions',
            marker_color='#3498db',
            yaxis='y'
        ))
        
        fig_timeline.add_trace(go.Scatter(
            x=timeline_data['Mois'],
            y=timeline_data['Temps_Arret_Total'],
            name='Temps d\'arrêt (h)',
            line=dict(color='#e74c3c', width=3),
            yaxis='y2'
        ))
        
        fig_timeline.update_layout(
            title='Évolution mensuelle des interventions et temps d\'arrêt',
            xaxis=dict(title='Mois'),
            yaxis=dict(title='Nombre d\'interventions', side='left'),
            yaxis2=dict(title='Temps d\'arrêt (heures)', side='right', overlaying='y'),
            hovermode='x unified',
            legend=dict(x=0.7, y=1.1, orientation='h'),
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Heatmap Technicien vs Type de Panne
        st.subheader("🔥 Heatmap : Interventions par Technicien et Type de Panne")
        
        heatmap_data = df_filtered.pivot_table(
            values='ID_Intervention',
            index='Technicien',
            columns='Type_Panne',
            aggfunc='count',
            fill_value=0
        )
        
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Type de Panne", y="Technicien", color="Nb Interventions"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale='YlOrRd',
            aspect='auto'
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

else:
    st.error("❌ Impossible de charger les données. Assurez-vous que le fichier 'interventions_2024_cleaned.csv' est présent dans le même répertoire.")

# Footer
st.divider()
st.markdown("---")
st.caption("🔧 Dashboard de Maintenance Industrielle - Analyse MTTR/MTBF et Pareto")
