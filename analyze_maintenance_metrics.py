#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse des métriques de maintenance
Calcule MTTR, MTBF et autres indicateurs par machine
À partir du fichier interventions_2024_cleaned.csv
"""

import pandas as pd
import sys
import os
from datetime import datetime


class MaintenanceMetricsAnalyzer:
    """Classe pour analyser les métriques de maintenance"""
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.output_file = input_file.replace('_cleaned.csv', '_metrics.csv')
        self.report_file = input_file.replace('_cleaned.csv', '_metrics_report.txt')
        self.df = None
        self.metrics_df = None
        
    def load_data(self):
        """Charge les données du fichier CSV nettoyé"""
        print(f"[INFO] Chargement du fichier : {self.input_file}")
        try:
            self.df = pd.read_csv(self.input_file, encoding='utf-8')
            print(f"[OK] {len(self.df)} interventions chargees")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors du chargement : {e}")
            return False
    
    def calculate_metrics(self):
        """Calcule les métriques de maintenance par machine"""
        print("\n[*] Calcul des metriques de maintenance...")
        
        # Grouper par machine
        grouped = self.df.groupby('ID_Machine')
        
        metrics = []
        
        for machine_id, group in grouped:
            # 1. Nombre total d'interventions
            nb_interventions = len(group)
            
            # 2. MTTR : durée moyenne des arrêts (en heures)
            mttr = group['Duree_Arret_h'].mean()
            
            # 3. Temps d'arrêt cumulé sur l'année (en heures)
            temps_arret_cumule = group['Duree_Arret_h'].sum()
            
            # 4. MTBF : temps moyen entre pannes (en jours)
            # MTBF = nombre de jours dans l'année / nombre d'interventions
            mtbf = 365.0 / nb_interventions
            
            # Calculs complémentaires utiles
            # Taux de disponibilité = (365*24 - temps_arret_cumule) / (365*24) * 100
            heures_annee = 365 * 24  # 8760 heures
            taux_disponibilite = ((heures_annee - temps_arret_cumule) / heures_annee) * 100
            
            metrics.append({
                'ID_Machine': machine_id,
                'Nb_Interventions': nb_interventions,
                'MTTR_heures': round(mttr, 2),
                'Temps_Arret_Cumule_heures': round(temps_arret_cumule, 2),
                'MTBF_jours': round(mtbf, 2),
                'Taux_Disponibilite_%': round(taux_disponibilite, 2)
            })
        
        # Créer le DataFrame des métriques
        self.metrics_df = pd.DataFrame(metrics)
        
        # Trier par temps d'arrêt cumulé décroissant
        self.metrics_df = self.metrics_df.sort_values(
            by='Temps_Arret_Cumule_heures', 
            ascending=False
        ).reset_index(drop=True)
        
        print(f"[OK] Metriques calculees pour {len(self.metrics_df)} machines")
        return self.metrics_df
    
    def display_top_machines(self, top_n=10):
        """Affiche le top N des machines les plus critiques"""
        print(f"\n{'=' * 80}")
        print(f"TOP {top_n} DES MACHINES LES PLUS CRITIQUES")
        print(f"(Triees par temps d'arret cumule decroissant)")
        print(f"{'=' * 80}\n")
        
        top_machines = self.metrics_df.head(top_n)
        
        # Affichage formaté
        print(f"{'#':<4} {'Machine':<12} {'Nb Int.':<10} {'MTTR (h)':<12} "
              f"{'Arret (h)':<14} {'MTBF (j)':<12} {'Dispo %':<10}")
        print(f"{'-' * 80}")
        
        for idx, row in top_machines.iterrows():
            rank = idx + 1
            print(f"{rank:<4} {row['ID_Machine']:<12} {row['Nb_Interventions']:<10} "
                  f"{row['MTTR_heures']:<12.2f} {row['Temps_Arret_Cumule_heures']:<14.2f} "
                  f"{row['MTBF_jours']:<12.2f} {row['Taux_Disponibilite_%']:<10.2f}")
        
        return top_machines
    
    def save_metrics(self):
        """Sauvegarde les métriques dans un fichier CSV"""
        print(f"\n[*] Sauvegarde des metriques : {self.output_file}")
        try:
            self.metrics_df.to_csv(self.output_file, index=False, encoding='utf-8')
            print(f"[OK] Fichier de metriques sauvegarde avec succes")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la sauvegarde : {e}")
            return False
    
    def generate_report(self, top_n=10):
        """Génère un rapport détaillé des métriques"""
        print(f"\n[*] Generation du rapport : {self.report_file}")
        
        top_machines = self.metrics_df.head(top_n)
        total_machines = len(self.metrics_df)
        total_interventions = self.df['ID_Intervention'].count()
        
        # Statistiques globales
        avg_mttr = self.metrics_df['MTTR_heures'].mean()
        avg_mtbf = self.metrics_df['MTBF_jours'].mean()
        avg_dispo = self.metrics_df['Taux_Disponibilite_%'].mean()
        total_downtime = self.metrics_df['Temps_Arret_Cumule_heures'].sum()
        
        report = f"""
{'=' * 80}
        RAPPORT D'ANALYSE DES METRIQUES DE MAINTENANCE
{'=' * 80}

Date de generation : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Fichier source     : {self.input_file}
Fichier metriques  : {self.output_file}

{'-' * 80}
STATISTIQUES GLOBALES
{'-' * 80}

Nombre total de machines      : {total_machines}
Nombre total d'interventions  : {total_interventions}
Temps d'arret cumule total    : {total_downtime:.2f} heures ({total_downtime/24:.2f} jours)

MTTR moyen (toutes machines)  : {avg_mttr:.2f} heures
MTBF moyen (toutes machines)  : {avg_mtbf:.2f} jours
Taux de disponibilite moyen   : {avg_dispo:.2f} %

{'-' * 80}
TOP {top_n} DES MACHINES LES PLUS CRITIQUES
{'-' * 80}
(Triees par temps d'arret cumule decroissant)

{'#':<4} {'Machine':<12} {'Nb Int.':<10} {'MTTR (h)':<12} {'Arret (h)':<14} {'MTBF (j)':<12} {'Dispo %':<10}
{'-' * 80}
"""
        
        for idx, row in top_machines.iterrows():
            rank = idx + 1
            report += f"{rank:<4} {row['ID_Machine']:<12} {row['Nb_Interventions']:<10} "
            report += f"{row['MTTR_heures']:<12.2f} {row['Temps_Arret_Cumule_heures']:<14.2f} "
            report += f"{row['MTBF_jours']:<12.2f} {row['Taux_Disponibilite_%']:<10.2f}\n"
        
        report += f"""
{'-' * 80}
INTERPRETATION DES INDICATEURS
{'-' * 80}

MTTR (Mean Time To Repair)
  > Duree moyenne d'une intervention de reparation
  > Plus le MTTR est faible, meilleure est la reparabilite
  > Objectif : Minimiser le MTTR

MTBF (Mean Time Between Failures)
  > Temps moyen entre deux pannes consecutives
  > Plus le MTBF est eleve, meilleure est la fiabilite
  > Objectif : Maximiser le MTBF
  > Formule : 365 jours / nombre d'interventions

Taux de Disponibilite
  > Pourcentage de temps ou la machine est operationnelle
  > Objectif : Maximiser (proche de 100%)
  > Formule : ((8760h - temps arret) / 8760h) * 100

{'-' * 80}
RECOMMANDATIONS POUR LES MACHINES CRITIQUES
{'-' * 80}

Les machines du Top {top_n} necessitent une attention particuliere :

1. Machines avec MTTR eleve (> {avg_mttr:.1f}h)
   > Ameliorer la logistique des pieces de rechange
   > Former les techniciens sur ces equipements
   > Envisager la maintenance predictive

2. Machines avec MTBF faible (< {avg_mtbf:.1f} jours)
   > Renforcer la maintenance preventive
   > Analyser les causes racines des pannes recurrentes
   > Envisager le remplacement si obsolescence

3. Machines avec faible disponibilite (< {avg_dispo:.1f}%)
   > Priorite absolue pour optimisation
   > Audit technique complet recommande
   > Plan d'action correctif urgent

{'=' * 80}
                    FIN DU RAPPORT
{'=' * 80}
"""
        
        # Sauvegarder le rapport
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        return report
    
    def run(self, top_n=10):
        """Lance l'analyse complète"""
        print("=" * 80)
        print("    ANALYSE DES METRIQUES DE MAINTENANCE")
        print("=" * 80)
        
        # 1. Charger les données
        if not self.load_data():
            return False
        
        # 2. Calculer les métriques
        self.calculate_metrics()
        
        # 3. Afficher le top N
        self.display_top_machines(top_n)
        
        # 4. Sauvegarder les métriques
        if not self.save_metrics():
            return False
        
        # 5. Générer le rapport
        self.generate_report(top_n)
        
        print(f"\n[OK] Analyse terminee avec succes !")
        print(f"[+] Fichier de metriques : {self.output_file}")
        print(f"[+] Rapport d'analyse : {self.report_file}")
        
        return True


def main():
    """Fonction principale"""
    
    # Déterminer le fichier à analyser
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "interventions_2024_cleaned.csv"
    
    # Vérifier que le fichier existe
    if not os.path.exists(input_file):
        print(f"[ERREUR] Le fichier {input_file} n'existe pas !")
        print(f"Usage: python {sys.argv[0]} [chemin_vers_fichier_cleaned.csv]")
        return 1
    
    # Top N des machines (par défaut 10, modifiable)
    top_n = 10
    if len(sys.argv) > 2:
        try:
            top_n = int(sys.argv[2])
        except ValueError:
            print("[ATTENTION] Le parametre top_n doit etre un entier, utilisation de 10 par defaut")
    
    # Lancer l'analyse
    analyzer = MaintenanceMetricsAnalyzer(input_file)
    success = analyzer.run(top_n)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
