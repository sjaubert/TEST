#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage du fichier interventions_2024.csv
Normalise les dates, durées, noms, types de pannes et pièces changées.
Préserve le fichier original et crée un fichier nettoyé.
"""

import pandas as pd
import re
from datetime import datetime
import os
from typing import Dict, List, Tuple

class InterventionCleaner:
    """Classe pour nettoyer les données d'interventions"""
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.output_file = input_file.replace('.csv', '_cleaned.csv')
        self.report_file = input_file.replace('.csv', '_cleaning_report.txt')
        self.df = None
        self.changes_log = []
        
        # Tables de normalisation
        self.technician_mapping = {
            'marie simon': 'Marie Simon',
            'marie SIMON': 'Marie Simon',
            'sophie bernard': 'Sophie Bernard',
            's.bernard': 'Sophie Bernard',
            'S.Bernard': 'Sophie Bernard',
            'alexandre petit': 'Alexandre Petit',
            'a. petit': 'Alexandre Petit',
            'A. PETIT': 'Alexandre Petit',
            'pierre rodriguez': 'Pierre Rodriguez',
            'rodriguez': 'Pierre Rodriguez',
            'RODRIGUEZ': 'Pierre Rodriguez',
            'nicolas michel': 'Nicolas Michel',
            'n.michel': 'Nicolas Michel',
            'N.Michel': 'Nicolas Michel',
            'thomas laurent': 'Thomas Laurent',
            't.laurent': 'Thomas Laurent',
            'T.Laurent': 'Thomas Laurent',
            'julie moreau': 'Julie Moreau',
            'julie MOREAU': 'Julie Moreau',
            'martin dupont': 'Martin Dupont',
            'm. dupont': 'Martin Dupont',
            'M. Dupont': 'Martin Dupont',
            'isabelle garcia': 'Isabelle Garcia',
            'i. garcia': 'Isabelle Garcia',
            'I. Garcia': 'Isabelle Garcia',
            'céline lefebvre': 'Céline Lefebvre',
            'celine lefebvre': 'Céline Lefebvre',
            'Celine Lefebvre': 'Céline Lefebvre',
        }
        
    def load_data(self):
        """Charge les données du fichier CSV"""
        print(f"[INFO] Chargement du fichier : {self.input_file}")
        try:
            self.df = pd.read_csv(self.input_file, encoding='utf-8')
            print(f"[OK] {len(self.df)} lignes chargees")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors du chargement : {e}")
            return False
    
    def normalize_date(self, date_str: str) -> str:
        """Normalise une date au format ISO 8601 (YYYY-MM-DD)"""
        if pd.isna(date_str):
            return date_str
        
        date_str = str(date_str).strip()
        
        # Liste des formats à tester
        formats = [
            '%Y-%m-%d',      # 2024-02-12
            '%d-%m-%Y',      # 17-11-2024
            '%d/%m/%Y',      # 27/04/2024
            '%d.%m.%Y',      # 25.12.2024
            '%Y/%m/%d',      # 2024/04/27
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str  # Retourne la valeur originale si aucun format ne marche
    
    def normalize_duration(self, duration_str: str) -> float:
        """Normalise une durée en format décimal (heures avec 2 décimales)"""
        if pd.isna(duration_str):
            return 0.0
        
        duration_str = str(duration_str).strip()
        
        # Déjà au bon format (nombre décimal)
        try:
            # Correction des valeurs invalides avec double point (33.0.25 -> 33.25)
            if duration_str.count('.') > 1:
                # Prendre le premier et dernier nombre
                parts = duration_str.split('.')
                if len(parts) == 3 and parts[1] == '0':
                    duration_str = f"{parts[0]}.{parts[2]}"
                    self.changes_log.append(f"Correction durée invalide : {duration_str}")
            
            return round(float(duration_str), 2)
        except ValueError:
            pass
        
        # Format "41h45" ou "34h00"
        match = re.match(r'(\d+)h(\d+)', duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return round(hours + minutes / 60, 2)
        
        # Format "13 heures 30 min"
        match = re.match(r'(\d+)\s*heures?\s*(\d+)\s*min', duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return round(hours + minutes / 60, 2)
        
        # Format "41:30" ou "9:45"
        match = re.match(r'(\d+):(\d+)', duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return round(hours + minutes / 60, 2)
        
        # Format "8h00"
        match = re.match(r'(\d+)h(\d+)', duration_str.replace('h', 'h'))
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            return round(hours + minutes / 60, 2)
        
        # Si rien ne marche, essayer de convertir comme nombre
        try:
            return round(float(duration_str.replace(',', '.')), 2)
        except:
            self.changes_log.append(f"[WARNING] Duree non reconnue : {duration_str}")
            return 0.0
    
    def normalize_technician(self, name: str) -> str:
        """Normalise le nom d'un technicien"""
        if pd.isna(name):
            return name
        
        name = str(name).strip()
        name_lower = name.lower()
        
        # Vérifier dans la table de correspondance
        if name_lower in self.technician_mapping:
            return self.technician_mapping[name_lower]
        
        # Si pas dans la table, normaliser en Title Case
        return name.title()
    
    def normalize_fault_type(self, fault_type: str) -> str:
        """Normalise le type de panne"""
        if pd.isna(fault_type) or fault_type == '':
            return ''
        
        fault_type = str(fault_type).strip()
        
        # Normalisation des types courants
        fault_mapping = {
            'surchauffe': 'Surchauffe',
            'SURCHAUFFE': 'Surchauffe',
            'défaut capteur': 'Défaut Capteur',
            'defaut capteur': 'Défaut Capteur',
            'Défaut capteur': 'Défaut Capteur',
            'panne electrique': 'Panne Électrique',
            'panne électrique': 'Panne Électrique',
            'Panne Electrique': 'Panne Électrique',
            'PANNE ELECTRIQUE': 'Panne Électrique',
            'panne hydraulique': 'Panne Hydraulique',
            'PANNE HYDRAULIQUE': 'Panne Hydraulique',
            'panne pneumatique': 'Panne Pneumatique',
            'PANNE PNEUMATIQUE': 'Panne Pneumatique',
            'panne mécanique': 'Panne Mécanique',
            'panne mecanique': 'Panne Mécanique',
            'Panne Mecanique': 'Panne Mécanique',
            'vibration anormale': 'Vibrations Anormales',
            'vibrations anormales': 'Vibrations Anormales',
            'Vibration Anormale': 'Vibrations Anormales',
            'usure normale': 'Usure Normale',
            'Usure normale': 'Usure Normale',
            'usure Normale': 'Usure Normale',
            'fuite': 'Fuite',
            'fuites': 'Fuite',
            'Fuites': 'Fuite',
            'défaut lubrification': 'Défaut Lubrification',
            'defaut lubrification': 'Défaut Lubrification',
            'Def. Lubrification': 'Défaut Lubrification',
            'Défaut Lubrification': 'Défaut Lubrification',
        }
        
        # Normaliser en minuscule pour la recherche
        fault_lower = fault_type.lower()
        if fault_lower in fault_mapping:
            return fault_mapping[fault_lower]
        
        # Sinon, mettre en Title Case
        return fault_type.title()
    
    def normalize_parts(self, parts_str: str) -> str:
        """Normalise la liste des pièces changées"""
        if pd.isna(parts_str):
            return 'Aucune'
        
        parts_str = str(parts_str).strip()
        
        # Valeurs vides/nulles
        if parts_str in ['', 'N/A', '-', 'n/a', 'NA']:
            return 'Aucune'
        
        # Remplacer les séparateurs non standards par des virgules
        parts_str = parts_str.replace(';', ',')
        parts_str = parts_str.replace(' / ', ', ')
        parts_str = parts_str.replace(' - ', ', ')
        parts_str = parts_str.replace(' | ', ', ')
        
        # Nettoyer les espaces multiples
        parts_str = re.sub(r'\s+', ' ', parts_str)
        
        return parts_str
    
    def clean_data(self):
        """Applique toutes les normalisations"""
        print("\n[*] Nettoyage des donnees en cours...")
        
        changes_count = {
            'dates': 0,
            'durations': 0,
            'technicians': 0,
            'fault_types': 0,
            'parts': 0,
        }
        
        # 1. Normaliser les dates
        print("[1/5] Normalisation des dates...")
        original_dates = self.df['Date'].copy()
        self.df['Date'] = self.df['Date'].apply(self.normalize_date)
        changes_count['dates'] = (original_dates != self.df['Date']).sum()
        
        # 2. Normaliser les durées
        print("[2/5] Normalisation des durees...")
        original_durations = self.df['Duree_Arret_h'].copy()
        self.df['Duree_Arret_h'] = self.df['Duree_Arret_h'].apply(self.normalize_duration)
        changes_count['durations'] = (original_durations.astype(str) != self.df['Duree_Arret_h'].astype(str)).sum()
        
        # 3. Normaliser les techniciens
        print("[3/5] Normalisation des noms de techniciens...")
        original_techs = self.df['Technicien'].copy()
        self.df['Technicien'] = self.df['Technicien'].apply(self.normalize_technician)
        changes_count['technicians'] = (original_techs != self.df['Technicien']).sum()
        
        # 4. Normaliser les types de pannes
        print("[4/5] Normalisation des types de pannes...")
        original_faults = self.df['Type_Panne'].copy()
        self.df['Type_Panne'] = self.df['Type_Panne'].apply(self.normalize_fault_type)
        changes_count['fault_types'] = (original_faults != self.df['Type_Panne']).sum()
        
        # 5. Normaliser les pièces
        print("[5/5] Normalisation des pieces changees...")
        original_parts = self.df['Pieces_Changees'].copy()
        self.df['Pieces_Changees'] = self.df['Pieces_Changees'].apply(self.normalize_parts)
        changes_count['parts'] = (original_parts != self.df['Pieces_Changees']).sum()
        
        return changes_count
    
    def save_cleaned_data(self):
        """Sauvegarde les données nettoyées"""
        print(f"\n[*] Sauvegarde du fichier nettoye : {self.output_file}")
        try:
            self.df.to_csv(self.output_file, index=False, encoding='utf-8')
            print(f"[OK] Fichier sauvegarde avec succes")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la sauvegarde : {e}")
            return False
    
    def generate_report(self, changes_count: Dict[str, int]):
        """Génère un rapport de nettoyage"""
        print(f"\n[*] Generation du rapport : {self.report_file}")
        
        total_changes = sum(changes_count.values())
        
        report = f"""
{'=' * 65}
        RAPPORT DE NETTOYAGE - interventions_2024.csv
{'=' * 65}

Date du nettoyage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Fichier source     : {self.input_file}
Fichier nettoye    : {self.output_file}

{'-' * 65}
STATISTIQUES
{'-' * 65}

Total d'enregistrements : {len(self.df)}
Total de modifications  : {total_changes}

DETAILS DES MODIFICATIONS :

  Dates normalisees          : {changes_count['dates']} 
  Durees corrigees           : {changes_count['durations']}
  Techniciens standardises   : {changes_count['technicians']}
  Types de pannes normalises : {changes_count['fault_types']}
  Pieces normalisees         : {changes_count['parts']}

{'-' * 65}
RESUME DES NORMALISATIONS APPLIQUEES
{'-' * 65}

* Format de date : ISO 8601 (YYYY-MM-DD)
* Format de duree : Decimal (heures avec 2 decimales)
* Noms de techniciens : Format "Prenom Nom" standardise
* Types de pannes : Title Case avec accents corrects
* Pieces changees : Virgule comme separateur unique
* Valeurs nulles : "Aucune" pour les pieces non changees

{'-' * 65}
AMELIORATIONS DE LA QUALITE DES DONNEES
{'-' * 65}

> Correction des dates multi-formats (DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY)
> Conversion des durees textuelles ("13 heures 30 min", "41h45")
> Correction des durees invalides (double point decimal)
> Unification des noms de techniciens (abreviations eliminees)
> Standardisation de la casse des types de pannes
> Harmonisation des separateurs de pieces (;, /, -, | -> ,)
> Normalisation des valeurs vides (N/A, -, vide -> Aucune)

{'=' * 65}
                    NETTOYAGE TERMINE
{'=' * 65}
"""
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        return report
    
    def run(self):
        """Lance le processus complet de nettoyage"""
        print("=" * 60)
        print("    NETTOYAGE DU FICHIER interventions_2024.csv")
        print("=" * 60)
        
        # 1. Charger les données
        if not self.load_data():
            return False
        
        # 2. Nettoyer
        changes_count = self.clean_data()
        
        # 3. Sauvegarder
        if not self.save_cleaned_data():
            return False
        
        # 4. Générer le rapport
        self.generate_report(changes_count)
        
        print("\n[OK] Processus de nettoyage termine avec succes !")
        print(f"[+] Fichier original preserve : {self.input_file}")
        print(f"[+] Fichier nettoye cree : {self.output_file}")
        print(f"[+] Rapport genere : {self.report_file}")
        
        return True


def main():
    """Fonction principale"""
    import sys
    
    # Déterminer le fichier à nettoyer
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "interventions_2024.csv"
    
    # Vérifier que le fichier existe
    if not os.path.exists(input_file):
        print(f"[ERREUR] Le fichier {input_file} n'existe pas !")
        print(f"Usage: python {sys.argv[0]} [chemin_vers_fichier.csv]")
        return 1
    
    # Lancer le nettoyage
    cleaner = InterventionCleaner(input_file)
    success = cleaner.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
