# 🧹 Script de Nettoyage - interventions_2024.csv

Ce script Python nettoie et normalise automatiquement le fichier `interventions_2024.csv`.

## 📋 Prérequis

```bash
pip install pandas
```

## 🚀 Utilisation

### Option 1 : Exécution simple

```bash
python clean_interventions.py
```

Par défaut, cherche le fichier `interventions_2024.csv` dans le répertoire courant.

### Option 2 : Spécifier un fichier

```bash
python clean_interventions.py chemin/vers/interventions_2024.csv
```

## 📂 Fichiers générés

Après exécution, 3 fichiers sont créés/conservés :

1. **interventions_2024.csv** - ✅ Fichier original (PRÉSERVÉ)
2. **interventions_2024_cleaned.csv** - 🆕 Fichier nettoyé
3. **interventions_2024_cleaning_report.txt** - 📊 Rapport détaillé

## 🔧 Corrections appliquées

### 1. Dates

- ✅ Conversion au format ISO 8601 : `YYYY-MM-DD`
- Gère : `DD-MM-YYYY`, `DD/MM/YYYY`, `DD.MM.YYYY`

### 2. Durées d'arrêt

- ✅ Format décimal : `14.50` heures
- Convertit :
  - `13 heures 30 min` → `13.50`
  - `41h45` → `41.75`
  - `9:45` → `9.75`
  - `33.0.25` → `33.25` (correction valeurs invalides)

### 3. Noms de techniciens

- ✅ Format standardisé : `Prénom Nom`
- Élimine abréviations : `S.Bernard` → `Sophie Bernard`
- Uniformise casse : `marie SIMON` → `Marie Simon`

### 4. Types de pannes

- ✅ Format Title Case avec accents corrects
- Exemples :
  - `surchauffe` → `Surchauffe`
  - `PANNE HYDRAULIQUE` → `Panne Hydraulique`
  - `Def. Lubrification` → `Défaut Lubrification`

### 5. Pièces changées

- ✅ Séparateur unique : virgule
- ✅ Valeurs vides → `Aucune`
- Normalise : `;`, `/`, `-`, `|` → `,`

## 📊 Exemple de rapport

```
═══════════════════════════════════════════════════════════════
        RAPPORT DE NETTOYAGE - interventions_2024.csv
═══════════════════════════════════════════════════════════════

Total d'enregistrements : 5000
Total de modifications  : 2847

DÉTAILS DES MODIFICATIONS :

  📅 Dates normalisées          : 342 
  ⏱️  Durées corrigées          : 876
  👤 Techniciens standardisés   : 523
  🔧 Types de pannes normalisés : 691
  ⚙️  Pièces normalisées         : 415
```

## ⚠️ Important

- Le fichier original est **toujours préservé**
- Vérifiez le rapport avant d'utiliser le fichier nettoyé
- En cas de doute, comparez les deux fichiers

## 🐛 Support

En cas de problème, vérifiez :

1. Que pandas est installé : `pip install pandas`
2. Que le fichier CSV existe
3. Que vous avez les droits d'écriture dans le dossier
