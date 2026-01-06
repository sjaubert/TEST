"""
Script de nettoyage du fichier interventions_2024.csv
Ce script :
1. Charge le fichier CSV
2. Normalise tous les champs (dates, noms, types de pannes, etc.)
3. Gère les valeurs manquantes
4. Sauvegarde le fichier nettoyé
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime


def normalize_date(date_str):
    """
    Normalise les dates dans différents formats vers le format YYYY-MM-DD
    Formats supportés: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
    """
    if pd.isna(date_str):
        return np.nan
    
    date_str = str(date_str).strip()
    
    # Essayer différents formats de date
    formats = [
        '%Y-%m-%d',  # 2024-01-15
        '%d-%m-%Y',  # 15-01-2024
        '%d/%m/%Y',  # 15/01/2024
        '%d.%m.%Y',  # 15.01.2024
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Si aucun format ne fonctionne, retourner NaN
    return np.nan


def normalize_duration(duration_str):
    """
    Normalise la durée d'arrêt en heures (format décimal)
    Gère: heures décimales, "Xh", "X heures Y min", "X:Y", erreurs de format
    """
    if pd.isna(duration_str):
        return np.nan
    
    duration_str = str(duration_str).strip()
    
    # Erreurs de format avec plusieurs points (ex: 33.0.25)
    if duration_str.count('.') > 1:
        # Garder seulement le premier point
        parts = duration_str.split('.')
        duration_str = parts[0] + '.' + ''.join(parts[1:])
        try:
            return float(duration_str)
        except:
            return np.nan
    
    # Format décimal simple (ex: 14.00, 33.25)
    try:
        return float(duration_str)
    except:
        pass
    
    # Format "Xh" ou "XhY" (ex: 41h45, 31h30)
    match = re.match(r'(\d+)h(\d*)', duration_str)
    if match:
        hours = float(match.group(1))
        minutes = float(match.group(2)) if match.group(2) else 0
        return hours + (minutes / 60)
    
    # Format "X heures Y min" (ex: "13 heures 30 min", "24 heures 0 min")
    match = re.match(r'(\d+)\s*heures?\s*(\d+)\s*min', duration_str)
    if match:
        hours = float(match.group(1))
        minutes = float(match.group(2))
        return hours + (minutes / 60)
    
    # Format "X:Y" (ex: 41:30, 9:45)
    match = re.match(r'(\d+):(\d+)', duration_str)
    if match:
        hours = float(match.group(1))
        minutes = float(match.group(2))
        return hours + (minutes / 60)
    
    return np.nan


def normalize_technician(name):
    """
    Normalise les noms de techniciens
    Gère les différents formats: Nom complet, Initiales, P. Nom, etc.
    """
    if pd.isna(name):
        return np.nan
    
    name = str(name).strip()
    
    # Remplacer les variations courantes
    replacements = {
        'A. PETIT': 'Alexandre Petit',
        'M. Dupont': 'Martin Dupont',
        'T.Laurent': 'Thomas Laurent',
        'S.Bernard': 'Sophie Bernard',
        'I. Garcia': 'Isabelle Garcia',
        'N.Michel': 'Nicolas Michel',
        'RODRIGUEZ': 'Pierre Rodriguez',
        'Celine Lefebvre': 'Céline Lefebvre',  # Correction accent
    }
    
    # Vérifier les remplacements directs
    if name in replacements:
        return replacements[name]
    
    # Normaliser la casse (mettre en titre)
    # Sauf pour les noms déjà bien formatés
    if name.isupper() or name.islower():
        name = name.title()
    
    # Gérer le format "Prénom.Nom" ou "P.Nom"
    if '.' in name and ' ' not in name:
        parts = name.split('.')
        if len(parts) == 2:
            # Si la première partie est une seule lettre, on cherche le nom complet
            if len(parts[0]) == 1:
                # Mapping des initiales vers noms complets
                initial_map = {
                    'A': 'Alexandre',
                    'M': 'Martin',
                    'T': 'Thomas',
                    'S': 'Sophie',
                    'I': 'Isabelle',
                    'N': 'Nicolas',
                }
                first = initial_map.get(parts[0].upper(), parts[0])
                last = parts[1].title()
                name = f"{first} {last}"
    
    return name


def normalize_fault_type(fault):
    """
    Normalise les types de pannes
    Uniformise la casse et les variations
    """
    if pd.isna(fault):
        return np.nan
    
    fault = str(fault).strip()
    
    # Mapping des variations vers la forme standard
    fault_map = {
        'surchauffe': 'Surchauffe',
        'PANNE HYDRAULIQUE': 'Panne Hydraulique',
        'panne pneumatique': 'Panne Pneumatique',
        'Défaut capteur': 'Défaut Capteur',
        'Def. Lubrification': 'Défaut Lubrification',
        'Fuites': 'Fuite',
        'Panne Mecanique': 'Panne Mécanique',
        'Panne Electrique': 'Panne Électrique',
        'Vibration Anormale': 'Vibrations Anormales',
        'Usure normale': 'Usure Normale',
    }
    
    # Recherche dans le mapping (insensible à la casse)
    for key, value in fault_map.items():
        if fault.lower() == key.lower():
            return value
    
    # Si pas trouvé, normaliser la casse (première lettre majuscule)
    if fault.islower() or fault.isupper():
        return fault.title()
    
    return fault


def normalize_parts(parts_str):
    """
    Normalise le champ Pieces_Changees
    Gère les valeurs manquantes avec différentes représentations
    """
    if pd.isna(parts_str):
        return 'Aucune'
    
    parts_str = str(parts_str).strip()
    
    # Valeurs indiquant "aucune pièce"
    no_parts = ['', '-', 'N/A', 'Aucune', 'aucune']
    
    if parts_str in no_parts:
        return 'Aucune'
    
    # Normaliser les séparateurs
    # Remplacer / et | par des virgules
    parts_str = parts_str.replace(' / ', ', ')
    parts_str = parts_str.replace(' | ', ', ')
    parts_str = parts_str.replace('; ', ', ')
    parts_str = parts_str.replace(' - ', ', ')
    
    return parts_str


def clean_interventions_data(input_file, output_file):
    """
    Fonction principale de nettoyage du fichier interventions
    """
    print(f"Chargement du fichier: {input_file}")
    
    # Charger le CSV
    df = pd.read_csv(input_file, encoding='utf-8')
    
    print(f"Nombre de lignes chargées: {len(df)}")
    print(f"Nombre de colonnes: {len(df.columns)}")
    print(f"\nColonnes: {list(df.columns)}")
    
    # Afficher les statistiques avant nettoyage
    print("\n" + "="*60)
    print("STATISTIQUES AVANT NETTOYAGE")
    print("="*60)
    print(f"Valeurs manquantes par colonne:")
    print(df.isnull().sum())
    
    # Créer une copie pour le nettoyage
    df_clean = df.copy()
    
    # 1. Normaliser les dates
    print("\n1. Normalisation des dates...")
    df_clean['Date'] = df_clean['Date'].apply(normalize_date)
    print(f"   Dates normalisées: {df_clean['Date'].notna().sum()}/{len(df_clean)}")
    
    # 2. Normaliser la durée d'arrêt
    print("\n2. Normalisation des durées d'arrêt...")
    df_clean['Duree_Arret_h'] = df_clean['Duree_Arret_h'].apply(normalize_duration)
    print(f"   Durées normalisées: {df_clean['Duree_Arret_h'].notna().sum()}/{len(df_clean)}")
    
    # 3. Normaliser les noms de techniciens
    print("\n3. Normalisation des noms de techniciens...")
    df_clean['Technicien'] = df_clean['Technicien'].apply(normalize_technician)
    print(f"   Techniciens normalisés: {df_clean['Technicien'].notna().sum()}/{len(df_clean)}")
    
    # 4. Normaliser les types de pannes
    print("\n4. Normalisation des types de pannes...")
    df_clean['Type_Panne'] = df_clean['Type_Panne'].apply(normalize_fault_type)
    print(f"   Types de pannes normalisés: {df_clean['Type_Panne'].notna().sum()}/{len(df_clean)}")
    
    # 5. Normaliser les pièces changées
    print("\n5. Normalisation des pièces changées...")
    df_clean['Pieces_Changees'] = df_clean['Pieces_Changees'].apply(normalize_parts)
    print(f"   Pièces normalisées: {df_clean['Pieces_Changees'].notna().sum()}/{len(df_clean)}")
    
    # 6. Gérer les valeurs manquantes restantes
    print("\n6. Gestion des valeurs manquantes...")
    
    # Pour les champs critiques, on peut décider de supprimer les lignes
    # ou de les marquer pour révision manuelle
    critical_cols = ['ID_Intervention', 'ID_Machine']
    
    # Vérifier s'il y a des valeurs manquantes dans les colonnes critiques
    critical_missing = df_clean[critical_cols].isnull().any(axis=1)
    if critical_missing.sum() > 0:
        print(f"   ATTENTION: {critical_missing.sum()} lignes avec des valeurs manquantes dans les colonnes critiques")
    
    # Statistiques après nettoyage
    print("\n" + "="*60)
    print("STATISTIQUES APRÈS NETTOYAGE")
    print("="*60)
    print(f"Valeurs manquantes par colonne:")
    print(df_clean.isnull().sum())
    
    print(f"\nTypes de données:")
    print(df_clean.dtypes)
    
    # Sauvegarder le fichier nettoyé
    print(f"\n7. Sauvegarde du fichier nettoyé: {output_file}")
    df_clean.to_csv(output_file, index=False, encoding='utf-8')
    print(f"   [OK] Fichier sauvegarde avec succes!")
    
    # Résumé final
    print("\n" + "="*60)
    print("RESUME DU NETTOYAGE")
    print("="*60)
    print(f"Lignes traitees: {len(df_clean)}")
    print(f"Colonnes: {len(df_clean.columns)}")
    
    # Afficher quelques exemples de techniciens uniques
    print(f"\nTechniciens uniques ({df_clean['Technicien'].nunique()}):")
    print(df_clean['Technicien'].value_counts().head(10))
    
    print(f"\nTypes de pannes uniques ({df_clean['Type_Panne'].nunique()}):")
    print(df_clean['Type_Panne'].value_counts())
    
    return df_clean


if __name__ == "__main__":
    # Fichiers d'entrée et de sortie
    input_file = "interventions_2024.csv"
    output_file = "interventions_2024_clean.csv"
    
    # Exécuter le nettoyage
    try:
        df_cleaned = clean_interventions_data(input_file, output_file)
        print("\n[OK] Nettoyage termine avec succes!")
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors du nettoyage: {e}")
        import traceback
        traceback.print_exc()
