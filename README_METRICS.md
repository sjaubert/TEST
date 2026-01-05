# 📊 Script d'Analyse des Métriques de Maintenance

Ce script calcule les indicateurs clés de performance (KPI) de maintenance pour chaque machine.

## 📋 Prérequis

```bash
pip install pandas
```

## 🚀 Utilisation

### Option 1 : Exécution simple

```bash
python analyze_maintenance_metrics.py
```

Par défaut, analyse le fichier `interventions_2024_cleaned.csv`

### Option 2 : Spécifier un fichier

```bash
python analyze_maintenance_metrics.py interventions_2024_cleaned.csv
```

### Option 3 : Personnaliser le nombre de machines affichées

```bash
python analyze_maintenance_metrics.py interventions_2024_cleaned.csv 20
```

Affiche le top 20 au lieu du top 10

## 📂 Fichiers générés

Après exécution, 2 fichiers sont créés :

1. **interventions_2024_metrics.csv** - Fichier CSV avec toutes les métriques
2. **interventions_2024_metrics_report.txt** - Rapport détaillé avec recommandations

## 📊 Métriques calculées

Pour chaque machine, le script calcule :

### 1. **Nombre d'interventions**

Nombre total d'interventions sur l'année

### 2. **MTTR (Mean Time To Repair)**

- **Définition** : Durée moyenne d'une réparation
- **Formule** : Moyenne des durées d'arrêt
- **Unité** : Heures
- **Objectif** : **Minimiser** (moins de temps d'arrêt)

### 3. **Temps d'arrêt cumulé**

- **Définition** : Somme de toutes les durées d'arrêt sur l'année
- **Formule** : Somme des durées d'arrêt
- **Unité** : Heures
- **Objectif** : **Minimiser**

### 4. **MTBF (Mean Time Between Failures)**

- **Définition** : Temps moyen entre deux pannes
- **Formule** : 365 jours / nombre d'interventions
- **Unité** : Jours
- **Objectif** : **Maximiser** (pannes moins fréquentes)

### 5. **Taux de disponibilité**

- **Définition** : Pourcentage de temps où la machine est opérationnelle
- **Formule** : ((8760h - temps arrêt) / 8760h) × 100
- **Unité** : Pourcentage
- **Objectif** : **Maximiser** (proche de 100%)

## 📈 Exemple de résultats

```
TOP 10 DES MACHINES LES PLUS CRITIQUES
(Triées par temps d'arrêt cumulé décroissant)

#    Machine      Nb Int.    MTTR (h)     Arrêt (h)      MTBF (j)     Dispo %   
--------------------------------------------------------------------------------
1    CNC-009      126        24.55        3093.55        2.90         64.69     
2    CMP-004      113        27.04        3055.00        3.23         65.13     
3    PMP-008      113        26.37        2979.50        3.23         65.99     
```

### Interprétation

**CNC-009** (machine la plus critique) :

- **126 interventions** dans l'année (une panne tous les 2.9 jours)
- **MTTR de 24.55h** : Chaque réparation prend en moyenne presque 1 jour
- **3093.55h d'arrêt** : Machine arrêtée pendant 128 jours sur 365
- **Disponibilité de 64.69%** : Machine opérationnelle seulement 2 jours sur 3

## 🎯 Recommandations automatiques

Le rapport fournit des recommandations basées sur :

### Machines avec MTTR élevé

- Améliorer la logistique des pièces de rechange
- Former les techniciens
- Envisager la maintenance prédictive

### Machines avec MTBF faible

- Renforcer la maintenance préventive
- Analyser les causes racines
- Envisager le remplacement

### Machines avec faible disponibilité

- Priorité absolue pour optimisation
- Audit technique complet
- Plan d'action correctif urgent

## 📁 Structure du fichier CSV de métriques

```csv
ID_Machine,Nb_Interventions,MTTR_heures,Temps_Arret_Cumule_heures,MTBF_jours,Taux_Disponibilite_%
CNC-009,126,24.55,3093.55,2.90,64.69
CMP-004,113,27.04,3055.00,3.23,65.13
...
```

## 💡 Utilisation des résultats

### Pour la direction

- Identifier les machines à grande perte de production
- Prioriser les investissements de modernisation
- Suivre l'évolution de la disponibilité

### Pour la maintenance

- Planifier les actions préventives prioritaires
- Optimiser les stocks de pièces
- Former les équipes sur les machines critiques

### Pour la production

- Anticiper les goulots d'étranglement
- Planifier les capacités
- Améliorer la planification

## ⚠️ Important

- Le MTBF est calculé sur base calendaire (365 jours)
- Pour un MTBF opérationnel, ajustez selon vos heures de production effectives
- Le taux de disponibilité est calculé sur 24h/24, 7j/7 (8760h/an)
