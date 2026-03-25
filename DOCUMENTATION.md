# Chiffrage HET — Documentation complète

## Table des matières

1. [Présentation générale](#1-présentation-générale)
2. [Installation et lancement](#2-installation-et-lancement)
3. [Architecture logicielle](#3-architecture-logicielle)
4. [Structure des fichiers](#4-structure-des-fichiers)
5. [Modèle de données](#5-modèle-de-données)
6. [Classes de tâches](#6-classes-de-tâches)
7. [Interface utilisateur — Onglets](#7-interface-utilisateur--onglets)
   - 7.8 [Onglet « Recherche machine »](#78-onglet--recherche-machine--tabmachinesearch)
8. [Logique de calcul](#8-logique-de-calcul)
9. [Gestion des coefficients](#9-gestion-des-coefficients)
10. [Flux de données et signaux](#10-flux-de-données-et-signaux)
11. [Sérialisation et format des projets](#11-sérialisation-et-format-des-projets)
12. [Exports Excel](#12-exports-excel)
13. [Fichiers de configuration et de données](#13-fichiers-de-configuration-et-de-données)
14. [Compilation et déploiement](#14-compilation-et-déploiement)
15. [Référence API — Classes et méthodes](#15-référence-api--classes-et-méthodes)
16. [Problèmes connus](#16-problèmes-connus)

---

## 1. Présentation générale

**Chiffrage HET** (Budget HET) est une application de bureau développée en Python avec PyQt6, conçue pour **Jeumont Électrique**. Elle remplace le fichier Excel « BUDGET_HET » et permet d'estimer les heures d'ingénierie nécessaires à la réalisation de projets de machines électriques tournantes (alternateurs, moteurs synchrones/asynchrones, équipements marins militaires).

### Fonctionnalités principales

- **Saisie des métadonnées projet** : numéro CRM, client, type d'affaire, DAS, secteur, type de machine, produit, quantité, etc.
- **Calcul automatique des heures** selon le produit, le type d'affaire et le secteur, avec application de coefficients contextuels.
- **Gestion de 5 types de tâches** : tâches générales, calculs, options, documents LPDC, travaux de laboratoire.
- **Correction manuelle** des heures par tâche avec traçabilité.
- **Calcul multi-machines** avec dégressivité automatique selon la quantité.
- **Coefficient REX** (Retour d'Expérience) applicable au total.
- **Export Excel** au format ORTEMS (distribution sur postes de travail) et au format rapport de chiffrage détaillé.
- **Sauvegarde/chargement de projets** au format JSON (sérialisation par delta).
- **Recherche dans la base REX** : interrogation de la base de machines historiques (fichier Excel `REX_HET.xlsx`) avec filtres textuels, numériques (± tolérance) et par listes déroulantes. Double-clic sur un résultat pour consulter et éditer les machines du projet.

---

## 2. Installation et lancement

### Prérequis

- Python 3.10+
- Dépendances :
  - `PyQt6` — framework d'interface graphique
  - `openpyxl` — lecture/écriture de fichiers Excel
  - `pandas` — manipulation de données (usage mineur)

### Installation des dépendances

```bash
pip install PyQt6 openpyxl pandas
```

### Lancement

```bash
python main.py
```

Le point d'entrée (`main.py`) effectue les opérations suivantes :
1. Chargement des données applicatives via `ApplicationData`
2. Création de l'application PyQt6 avec le thème configuré (Fusion)
3. Instanciation du `Controller` qui orchestre l'ensemble MVC
4. Application de la feuille de style QSS
5. Affichage de la fenêtre principale

---

## 3. Architecture logicielle

L'application suit le patron **Modèle-Vue-Contrôleur (MVC)** avec une communication par **signaux PyQt** :

```
┌─────────────────────────────────────────────────────────────────┐
│                        Controller                               │
│  (src/controller.py)                                            │
│  Orchestre tous les onglets, import/export, signaux globaux     │
├────────────┬────────────┬───────────┬───────────┬───────────────┤
│ TabGeneral │ GeneralTask│  Calculs  │  Options  │  LPDC  │ Labo│
│ Controller │ TabCtrl    │  TabCtrl  │  TabCtrl  │  TabCtrl│TabC│
│            │            │           │           │        │     │
│ (TabSummary│ Controller)│ (MachineSearchController)│     │     │
└─────┬──────┴─────┬──────┴─────┬─────┴─────┬─────┴────┬───┴─────┘
      │            │            │           │          │
      ▼            ▼            ▼           ▼          ▼
┌───────────────────────────────────────────────────────────────┐
│                         Model                                  │
│  (src/model.py)                                                │
│  Project : données, calculs, totaux, sérialisation             │
│  Signaux : project_changed, data_updated                       │
└───────────────────────────────────────────────────────────────┘
      │
      ▼
┌───────────────────────────────────────────────────────────────┐
│                          View                                  │
│  (src/view.py — MainWindow)                                    │
│  Fenêtre principale avec QTabWidget                            │
│  Chaque onglet est un widget autonome                          │
└───────────────────────────────────────────────────────────────┘
```

### Principes de conception

- **Séparation stricte** : le Model ne connaît pas la View, la communication passe par les signaux.
- **Polymorphisme des tâches** : tous les types de tâches partagent l'interface `effective_hours(context)`.
- **Sérialisation par delta** : seules les modifications utilisateur sont sauvegardées (pas de duplication des données de référence).
- **Debouncing** : les opérations lourdes (`apply_defaults`) sont différées de 300 ms via `QTimer`.

---

## 4. Structure des fichiers

```
HET_3/
├── main.py                          # Point d'entrée
├── config.xml                       # Configuration de l'application
├── build.bat                        # Script de compilation PyInstaller
├── requirements.txt                 # Dépendances Python
├── notes.txt                        # Notes et problèmes connus
│
├── src/
│   ├── controller.py                # Contrôleur principal
│   ├── model.py                     # Modèle (Project + Model)
│   ├── view.py                      # Vue principale (MainWindow)
│   ├── styles.qss                   # Feuille de style Qt
│   │
│   ├── tabs/                        # Contrôleurs d'onglets
│   │   ├── TabGeneral.py            # Onglet Général (formulaire projet)
│   │   ├── GeneralTaskTabController.py  # Onglet Tâches
│   │   ├── CalculsTabController.py  # Onglet Calculs
│   │   ├── OptionsTabController.py  # Onglet Options
│   │   ├── LPDCTabController.py     # Onglet LPDC
│   │   ├── LaboTabController.py     # Onglet Labo
│   │   ├── TabMachineSearch.py      # Onglet Recherche machine (vue + contrôleur + dialogue)
│   │   └── TabSummary.py            # Onglet Résumé
│   │
│   └── utils/                       # Utilitaires et classes de base
│       ├── ApplicationData.py       # Chargement config + données JSON
│       ├── BaseTaskTabController.py # Contrôleur de base pour onglets
│       ├── Task.py                  # Hiérarchie des classes de tâches
│       ├── TabTasks.py              # Widget tableau de tâches
│       ├── MachineDatabase.py       # Chargement et interrogation de la base REX
│       ├── widgets.py               # Widgets personnalisés (spinbox)
│       └── exports.py               # Fonctions d'export Excel
│
├── data/                            # Données de référence (JSON)
│   ├── base_data.json               # Personnes, produits, postes
│   ├── general_task_data_new.json   # Tâches générales hiérarchiques
│   ├── calculs.json                 # Définitions de calculs
│   ├── options.json                 # Options techniques
│   ├── LPDC.json                    # Documents plans/spécifications
│   └── labo.json                    # Travaux de laboratoire
│
├── assets/
│   ├── Affaire/                     # Projets sauvegardés
│   │   └── 2025.01.0001_A.json
│   └── Marine ref/                  # Projets de référence marine
│       ├── ANR_Malaisie_crit1.json
│       ├── MEP_Fremm_crit2.json
│       └── ...
│
└── template/                        # Templates Excel
    ├── ortems_template.xlsx          # Template ORTEMS
    └── chiffrage_template.xlsx       # Template rapport de chiffrage
```

---

## 5. Modèle de données

### Classe `Project` (`src/model.py`)

Centre névralgique de l'application. Stocke toutes les données du projet et effectue les calculs.

#### Attributs principaux

| Attribut | Type | Description |
|----------|------|-------------|
| `crm_number` | `str` | Numéro CRM du projet |
| `client` | `str` | Nom du client |
| `affaire` | `str` | Type d'affaire (`NEUF`, `IDENTIQUE_JE`, `REMPLACEMENT`) |
| `das` | `str` | Division d'activité stratégique (`MS`, `NUC`, `MIL`) |
| `secteur` | `str` | Secteur (`INDUS`, `OIL_GAS`, `NUC_QUALIFIE`, etc.) |
| `machine_type` | `str` | Catégorie machine (`SYNCH`, `ASYNCH`, `MIL`) |
| `product` | `str` | Produit spécifique (`ALT_2P`, `ALT_4P_L`, `MEP`, etc.) |
| `designation` | `str` | Désignation libre |
| `quantity` | `int` | Nombre de machines |
| `revision` | `str` | Lettre de révision |
| `date` | `str` | Date du chiffrage |
| `created_by` | `str` | Auteur du chiffrage |
| `validated_by` | `str` | Validateur |
| `description` | `str` | Description libre |
| `divers_percent` | `float` | Pourcentage divers (défaut : 0.05 = 5%) |
| `manual_rex_coeff` | `float` | Coefficient REX (défaut : 1.0) |
| `manual_rex_hours` | `float` | Heures REX manuelles (optionnel, remplace le coeff) |

#### Structures de tâches

| Attribut | Type | Description |
|----------|------|-------------|
| `tasks` | `dict[catégorie][sous-catégorie][list[GeneralTask]]` | Tâches générales hiérarchiques |
| `calculs` | `list[Calcul]` | Liste des calculs |
| `options` | `list[Option]` | Liste des options |
| `lpdc_docs` | `list[LPDCDocument]` | Documents LPDC |
| `labo` | `list[Labo]` | Travaux de laboratoire |

#### Coefficients LPDC et calculs

| Attribut | Type | Description |
|----------|------|-------------|
| `lpdc_secteur_coeff` | `dict` | Coeff LPDC par secteur |
| `lpdc_affaire_coeff` | `dict` | Coeff LPDC par type d'affaire |
| `calcul_coeff_type_affaire` | `dict` | Coeff calculs par catégorie |
| `option_coeff_category` | `dict` | Coeff options par catégorie |

### Classe `Model` (`src/model.py`)

Enveloppe `QObject` autour de `Project` pour l'intégration des signaux PyQt.

#### Signaux

| Signal | Émission | Usage |
|--------|----------|-------|
| `project_changed` | Après `apply_defaults()` | Reconstruction complète des onglets |
| `data_updated` | Après modification mineure | Rafraîchissement léger des affichages |

---

## 6. Classes de tâches

Toutes les classes de tâches résident dans `src/utils/Task.py` et héritent de `AbstractTask`.

### Hiérarchie

```
AbstractTask
├── GeneralTask      (Tâches d'ingénierie générales)
├── Calcul           (Calculs/analyses techniques)
├── Option           (Options techniques sélectionnables)
├── LPDCDocument     (Documents plans/spécifications)
└── Labo             (Travaux de laboratoire)
```

### `AbstractTask` — Classe de base

| Méthode | Description |
|---------|-------------|
| `__init__(label)` | Initialise avec un label et `manual_hours = None` |
| `default_hours(context)` | **Abstraite** — retourne les heures de base calculées |
| `effective_hours(context)` | Retourne `manual_hours` si défini, sinon `default_hours(context)` |

### `GeneralTask` — Tâches générales

Représente les tâches d'ingénierie (réunions, conception, suivi, etc.).

| Attribut | Type | Description |
|----------|------|-------------|
| `index` | `int` | Identifiant unique |
| `label` | `str` | Libellé de la tâche |
| `base_hours_machine` | `dict` | Heures de base par produit |
| `coeff_type_affaire` | `dict` | Coefficients par type d'affaire |
| `coeff_secteur` | `dict` | Coefficients par secteur |
| `is_multiplicative` | `bool` | Applicable au calcul multi-machines |
| `ortems_repartition` | `dict` | Distribution sur postes ORTEMS |

**Formule** : `default_hours = base_hours_machine[product] × coeff_type_affaire[affaire] × coeff_secteur[secteur]`

### `Calcul` — Calculs techniques

Représente les analyses techniques (électromagnétique, bobinage, mécanique, etc.).

| Attribut | Type | Description |
|----------|------|-------------|
| `index` | `int` | Identifiant unique |
| `label` | `str` | Libellé du calcul |
| `category` | `str` | Catégorie (`ELECMAG`, `BOB`, `CONCEPT_MECA`, `MECA_ANSYS`, `AERO_THERMIQUE`) |
| `hours` | `dict` | Heures par type de machine |
| `selection` | `dict` | Mode de sélection par machine (`mandatory` / `optional`) |

**Formule** : `effective_hours = hours[machine_type] × calcul_coeff_type_affaire[category]` (si actif)

Méthodes :
- `is_mandatory(context)` — vérifie si `selection[machine_type] == "mandatory"`
- `is_active(context)` — actif si obligatoire OU (optionnel ET sélectionné)

### `Option` — Options techniques

Représente les options sélectionnables (bagues, ATEX, instrumentation, etc.).

| Attribut | Type | Description |
|----------|------|-------------|
| `index` | `int` | Identifiant unique |
| `label` | `str` | Libellé de l'option |
| `category` | `str` | Catégorie (12 types possibles) |
| `hours` | `float` | Heures fixes |
| `is_selected` | `bool` | État de sélection (défaut : `False`) |

**Formule** : `effective_hours = hours × option_coeff_category[category]` (si sélectionné)

### `LPDCDocument` — Documents plans et spécifications

Représente les documents contractuels (plans, spécifications d'achat, etc.).

| Attribut | Type | Description |
|----------|------|-------------|
| `index` | `int` | Identifiant unique |
| `label` | `str` | Libellé du document |
| `hours` | `float` | Heures fixes |
| `applicable_pour` | `list` | Types de machine applicables |
| `secteur_obligatoire` | `list` | Secteurs rendant le document obligatoire |
| `option_possible` | `bool` | Sélectionnable en option |

**Formule** : `effective_hours = hours × LPDC_affaire_coeff × LPDC_secteur_coeff` (si actif)

Méthode `is_active(context)` : actif si le type de machine est applicable ET (secteur obligatoire OU sélectionné manuellement).

### `Labo` — Travaux de laboratoire

Représente les travaux de test en laboratoire (métallurgie, isolant).

| Attribut | Type | Description |
|----------|------|-------------|
| `index` | `int` | Identifiant unique |
| `label` | `str` | Libellé |
| `hours` | `float` | Heures de base |
| `category` | `str` | Catégorie (`LAB_METAL`, `LAB_ISOL`) |
| `coeff_secteur` | `dict` | Coefficients par secteur |

**Formule** : `effective_hours = hours × coeff_secteur[secteur]` (si actif)

---

## 7. Interface utilisateur — Onglets

L'interface est composée de 8 onglets dans un `QTabWidget` :

### 7.1 Onglet « Général » (`TabGeneral`)

Formulaire de saisie des métadonnées du projet :

| Champ | Type | Criticité* |
|-------|------|-----------|
| Numéro CRM | Texte | 0 |
| Client | Texte | 0 |
| Type d'affaire | ComboBox | 1 |
| DAS | ComboBox | 2 |
| Secteur | ComboBox | 2 |
| Catégorie produit | ComboBox | 2 |
| Produit | ComboBox | 2 |
| Désignation | Texte | 0 |
| Quantité | SpinBox | 1 |
| Révision | Texte | 0 |
| Date | DateEdit | 0 |
| Créé par | ComboBox | 0 |
| Validé par | ComboBox | 0 |
| Description | TextEdit | 0 |

*Criticité des modifications :*
- **0** : simple mise à jour (pas de recalcul)
- **1** : mise à jour des coefficients
- **2** : reconstruction complète (`apply_defaults`)

Contient également un bouton d'import de projet.

### 7.2 Onglet « Tâches » (`GeneralTaskTabController`)

Affiche les tâches d'ingénierie générales dans un ou plusieurs tableaux, organisés par catégorie et sous-catégorie.

**Colonnes** : Référence | Tâche | Heures de base | Heures finales | Correction manuelle

Les tâches sont toujours affichées (pas de case à cocher) — elles sont obligatoires.

### 7.3 Onglet « Calculs » (`CalculsTabController`)

Deux tableaux :
- **Calculs obligatoires** : déterminés automatiquement par le type de machine
- **Calculs optionnels** : sélectionnables avec case à cocher

**Colonnes** : ☑ Choix | Référence | Calcul | Heures de base | Heures finales | Correction

### 7.4 Onglet « Options » (`OptionsTabController`)

Un tableau avec toutes les options techniques, regroupées par catégorie (BAGUES, ATEX, ENV, INSTRUM, ESSAIS, NORME, etc.).

**Colonnes** : ☑ Choix | Référence | Option | Heures de base | Heures finales | Correction

### 7.5 Onglet « LPDC » (`LPDCTabController`)

Deux tableaux :
- **PDC de base** (BASE) : documents obligatoires selon le secteur
- **PDC particuliers** (PART) : documents optionnels sélectionnables

Contrôles supplémentaires : champs de saisie pour les coefficients LPDC secteur et affaire.

**Colonnes** : ☑ Choix (si applicable) | Référence | Document | Heures de base | Heures finales | Correction

### 7.6 Onglet « Labo » (`LaboTabController`)

Deux tableaux :
- **Travaux obligatoires** : déterminés par le secteur
- **Travaux optionnels** : sélectionnables avec case à cocher

**Catégories** : Labo métallurgie (`LAB_METAL`), Labo isolant (`LAB_ISOL`)

### 7.8 Onglet « Recherche machine » (`TabMachineSearch`)

Onglet permettant d'interroger la base de données REX (Retour d'Expérience) contenue dans le fichier Excel `data/REX_HET.xlsx`. L'objectif est de retrouver des machines similaires réalisées par le passé pour aider au chiffrage.

#### Source de données

Le fichier Excel contient deux feuilles exploitées :
- **Machines** : une ligne par machine, avec ~28 colonnes (projet, client, désignation, caractéristiques électriques, type produit, DAS, secteur, etc.)
- **Projets** : heures réalisées par projet, ventilées sur 8 codes job (`230ETELEC`, `230ETMECA`, `230ETMECNC`, `230ETNQ`, `230ETREGU`, `240RD`, `240RDNC`, `Total général`)

Le chemin du fichier est configuré dans `config.xml` via la balise `<rex-database-path>`.

#### Interface de recherche

L'interface est organisée en sections repliables :

1. **Recherche par texte** (contient) : N° Projet, Nom projet, Client, Client final, Désignation
2. **Filtres de sélection** : Année, NB POLES (`2`, `4`, `>4`), IP (deux chiffres séparés), IM, EEX, Type produit, Produit, Type affaire, DAS, Secteur
3. **Valeurs numériques** (± tolérance) : Nbr machines, MW, KV, Cos(phi), Hz, TR/MIN, DAL, LFER, NB ENCOCHES — avec tolérance configurable (5–100%, défaut 10%)

**Comportement des filtres** :
- Les filtres sont combinés en « ET » logique
- Les lignes dont la cellule est vide/NaN pour un champ filtré ne sont **pas** exclues (inclusion par défaut des données manquantes)
- Les combos Type produit → Produit et DAS → Secteur sont filtrés dynamiquement (comme dans l'onglet Général)
- Les champs Type produit, Produit et DAS sont pré-remplis depuis le projet courant
- La touche Entrée dans un champ texte/numérique lance la recherche

#### Tableau de résultats

Les résultats s'affichent dans un `QTableWidget` triable par colonnes. Les colonnes à codes (Type produit, Produit, Type affaire, DAS, Secteur) sont affichées avec leurs libellés lisibles. La colonne « Heures projet » est masquée.

Une scrollbar horizontale externe est synchronisée avec la scrollbar interne du tableau pour un défilement fluide même quand le tableau est intégré dans la scroll area principale.

#### Dialogue détail projet (double-clic)

Un double-clic sur une ligne ouvre un `ProjectDetailDialog` (1400×700) affichant :

1. **Heures du projet** : grille des 8 codes job avec les heures réalisées (issues de la feuille « Projets »)
2. **Machines du projet** : tableau de toutes les machines partageant le même N° Projet

**Édition directe** : chaque cellule du tableau est éditable par double-clic :
- Les colonnes **Type produit, Produit, Type affaire, DAS, Secteur** présentent un `QComboBox` avec les labels de l'application. Le filtrage dynamique est appliqué (Produit dépend du Type produit, Secteur dépend du DAS). Une option vide est toujours disponible.
- Les colonnes **IM, EEX** présentent un `QComboBox` avec les valeurs existantes dans la base
- Les autres colonnes présentent un champ texte libre (`QLineEdit`)

**Sauvegarde** : toute modification est immédiatement persistée dans le fichier Excel source via `openpyxl` (écriture cellule par cellule). Le DataFrame en mémoire est mis à jour simultanément.

### 7.9 Onglet « Résumé » (`TabSummary`)

Panneau gauche : **arbre récapitulatif** (`CollapsibleSection`) affichant la hiérarchie complète du projet avec les heures par section.

Panneau droit : **panneau des totaux** avec :

| Élément | Description |
|---------|-------------|
| Sous-total 1ère machine | Somme de toutes les heures effectives |
| Divers % | Pourcentage divers (modifiable, défaut 5%) |
| Total 1ère machine | Sous-total × (1 + divers%) |
| Total N machines | Inclut la dégressivité multi-machines |
| Coeff REX % | Coefficient REX (modifiable) |
| Heures REX | Heures REX manuelles (alternative au coeff) |
| **Total final** | Résultat final du chiffrage |

**Menu d'export** : JSON, Excel ORTEMS, Rapport Excel détaillé.

---

## 8. Logique de calcul

### 8.1 Calcul des heures par tâche

Chaque tâche possède une méthode `effective_hours(context)` :

```
Si manual_hours est défini :
    effective_hours = manual_hours
Sinon :
    effective_hours = default_hours(context)
```

Le `context` est un dictionnaire fourni par `Project.context()` contenant :
- `product`, `machine_type`, `affaire`, `secteur`
- `LPDC_secteur_coeff`, `LPDC_affaire_coeff`
- `calcul_coeff_type_affaire`
- `option_coeff_category`

### 8.2 Calcul du sous-total 1ère machine

```
first_machine_subtotal = Σ effective_hours(tâches générales)
                       + Σ effective_hours(calculs actifs)
                       + Σ effective_hours(options sélectionnées)
                       + Σ effective_hours(documents LPDC actifs)
                       + Σ effective_hours(travaux labo actifs)
```

### 8.3 Calcul du total 1ère machine

```
first_machine_total = first_machine_subtotal × (1 + divers_percent)
```

### 8.4 Calcul multi-machines

Seules les tâches marquées `is_multiplicative` contribuent aux machines supplémentaires.

**Dégressivité par quantité :**

| Quantité | Coefficient par machine supplémentaire |
|----------|---------------------------------------|
| 2 | 100% (×1.0) |
| 3 à 5 | 75% (×0.75) |
| 6 à 25 | 35% (×0.35) |
| > 25 | 15% (×0.15) |

```
multiplicative_subtotal = Σ effective_hours(tâches multiplicatives uniquement)

Coefficient multi-machines = Σ des contributions par tranche
  Exemple pour qty=4 : 1.0 + 0.75 + 0.75 = 2.5

n_machines_total = first_machine_total + multiplicative_subtotal × multi_machine_coeff
```

### 8.5 Calcul avec REX

```
Si manual_rex_hours est défini :
    total_with_rex = manual_rex_hours
Sinon :
    total_with_rex = n_machines_total × manual_rex_coeff
```

Le coefficient REX et les heures REX sont liés par la relation :
```
manual_rex_hours = n_machines_total × manual_rex_coeff
```
Modifier l'un met à jour l'autre automatiquement.

---

## 9. Gestion des coefficients

### 9.1 Coefficients par type de tâche

| Type | Coefficients appliqués | Source |
|------|----------------------|--------|
| **Tâches générales** | `coeff_type_affaire[affaire]` × `coeff_secteur[secteur]` | `general_task_data_new.json` |
| **Calculs** | `calcul_coeff_type_affaire[category]` | `calculs.json` |
| **Options** | `option_coeff_category[category]` | `options.json` |
| **LPDC** | `LPDC_affaire_coeff` × `LPDC_secteur_coeff` | `LPDC.json` |
| **Labo** | `coeff_secteur[secteur]` | `labo.json` |

### 9.2 Coefficients LPDC par secteur

| Secteur | Coefficient |
|---------|-------------|
| INDUS | 1.0 |
| OIL_GAS | 1.2 |
| NUC_QUALIFIE | 1.8 |
| NUC_NON_QUALIFIE | 1.0 |
| MARINE_CIVILE | 1.0 |
| MIL | 0 |

### 9.3 Coefficients LPDC par type d'affaire

| Type d'affaire | Coefficient |
|---------------|-------------|
| NEUF | 1.0 |
| IDENTIQUE_JE | 0.2 |
| REMPLACEMENT | 1.2 |

### 9.4 Coefficient divers

Pourcentage appliqué au sous-total pour couvrir les imprévus. Défaut : **5%**.

### 9.5 Coefficient REX (Retour d'Expérience)

Multiplicateur final tenant compte de l'expérience acquise. Défaut : **1.0** (100%).

---

## 10. Flux de données et signaux

### Architecture des signaux

```
Entrée utilisateur (TabGeneral / Tableaux / Résumé)
    │
    ▼
Signal Vue émis :
    field_changed(criticité)          → TabGeneral
    manual_value_modified(index, val) → TaskTableWidget
    checkbox_toggled(index, state)    → TaskTableWidget
    divers_changed(val)               → TabSummary
    rex_coeff_changed(val)            → TabSummary
    rex_hours_changed(val)            → TabSummary
    │
    ▼
Contrôleur traite le signal :
    - Met à jour Model.project
    - Appelle apply_defaults() si criticité = 2
    │
    ▼
Model émet :
    project_changed  → reconstruction complète des onglets
    data_updated     → rafraîchissement léger
    │
    ▼
Tous les Tab Controllers écoutent → reconstruction/rafraîchissement
    │
    ▼
TabSummaryController → met à jour l'arbre + les totaux
```

### Debouncing

Les modifications de criticité 2 (changement de produit, secteur, DAS) déclenchent un `QTimer` de 300 ms dans le `TabGeneralController`. Si un nouveau changement arrive dans ce délai, le timer est réinitialisé. Cela évite les recalculs intempestifs lors de changements en rafale.

---

## 11. Sérialisation et format des projets

### Sauvegarde (`save_project()`)

Le projet est sauvegardé au format JSON avec un système de **delta** : seuls les éléments modifiés par l'utilisateur sont persistés.

```json
{
  "version": 1,
  "project": {
    "crm_number": "2025.01.0001",
    "client": "Nom du client",
    "affaire": "NEUF",
    "das": "MS",
    "secteur": "INDUS",
    "machine_type": "SYNCH",
    "product": "ALT_2P",
    "designation": "",
    "quantity": 1,
    "revision": "A",
    "date": "2026-02-26",
    "created_by": "Walid BOUGHANMI",
    "validated_by": "Walid BOUGHANMI",
    "description": "",
    "divers_percent": 0.05,
    "manual_rex_coeff": 1.0
  },
  "modifications": {
    "tasks": [
      {"index": 5, "manual_hours": 360.0}
    ],
    "calculs": [
      {"index": 1, "is_selected": false, "manual_hours": 400.0}
    ],
    "options": [
      {"index": 147, "is_selected": true, "manual_hours": 925.0}
    ],
    "lpdc_docs": [
      {"index": 1, "is_selected": true, "manual_hours": 3041.7}
    ],
    "labo": []
  }
}
```

### Chargement (`load_project()`)

1. Les scalaires du projet sont restaurés
2. `apply_defaults()` reconstruit toutes les tâches depuis les données de référence
3. Les modifications sauvegardées sont appliquées en delta (par index) sur les tâches reconstruites

Ce mécanisme garantit que les projets restent compatibles même si les données de référence évoluent.

---

## 12. Exports Excel

### 12.1 Export ORTEMS (`export_ortems_excel()`)

L'export ORTEMS distribue les heures sur les différents postes de travail (job codes) selon des pondérations définies par catégorie.

**Processus** :
1. Chargement du template `ortems_template.xlsx`
2. Appel de `project.make_ortems_repartition()` :
   - Pour chaque tâche active, les heures sont réparties sur les job codes selon les mappings `ortems_repartition`
   - Le coefficient divers est appliqué
   - Le coefficient REX est appliqué
3. Écriture des résultats dans la feuille « prepa ORTEMS »
4. Le nombre de projeteurs (`n_projeteurs`) est défini selon le secteur

**Job codes utilisés** (23 postes) : `ADM_COA`, `ING_ELECTROTECH`, `PROJ_MACHINE`, `ING_MECANIQUE`, etc., chacun décliné en suffixes `DEF` (Définition) et `PROD` (Production).

### 12.2 Export Rapport de Chiffrage (`export_excel_report()`)

Génère un rapport détaillé du chiffrage dans un format structuré.

**Processus** :
1. Chargement du template `chiffrage_template.xlsx`
2. Écriture de l'en-tête projet (CRM, client, dates, etc.)
3. Recalcul de tous les totaux
4. Nettoyage de la zone dynamique (à partir de la ligne 17)
5. Écriture séquentielle des sections :
   - Tâches d'Enclenchement
   - Calculs actifs (par catégorie)
   - Plans FAB (heures non nulles)
   - Options sélectionnées
   - Documents LPDC actifs
   - Travaux Labo actifs
   - Tâches de Suivi
   - Ligne Divers (sous-total × %)
   - Total Machine N°1
   - Total N machines et REX

Chaque ligne affiche : heures de base | correction manuelle | heures corrigées finales (× REX).

---

## 13. Fichiers de configuration et de données

### 13.1 `config.xml`

Configuration générale de l'application :

```xml
<config>
    <data>
        <base_data>data/base_data.json</base_data>
        <options>data/options.json</options>
        <tasks>data/general_task_data_new.json</tasks>
        <LPDC>data/LPDC.json</LPDC>
        <calculs>data/calculs.json</calculs>
        <labo>data/labo.json</labo>
    </data>
    <assets>assets/</assets>
    <templates>
        <ortems>template/ortems_template.xlsx</ortems>
        <chiffrage>template/chiffrage_template.xlsx</chiffrage>
    </templates>
    <ui>
        <theme>Fusion</theme>
        <width>1080</width>
        <height>720</height>
        <stylesheet>src/styles.qss</stylesheet>
    </ui>
</config>
```

### 13.2 `data/base_data.json`

Données de référence de l'entreprise :

| Clé | Contenu |
|-----|---------|
| `people` | Liste des collaborateurs |
| `product_types` | Types de machines (`SYNCH`, `ASYNCH`, `MIL`) |
| `products` | Produits par type (ex : `SYNCH` → `ALT_2P`, `ALT_4P_L`, etc.) |
| `types_affaire` | Types d'affaire (`NEUF`, `IDENTIQUE_JE`, `REMPLACEMENT`) |
| `DAS` | Divisions d'activité (`MS`, `NUC`, `MIL`) |
| `sectors` | Secteurs par DAS |
| `jobs` | 23 codes postes de travail |
| `job_suffixes` | `DEF` (Définition), `PROD` (Production) |
| `n_projeteurs` | Nombre de projeteurs par secteur |

### 13.3 `data/general_task_data_new.json`

Structure hiérarchique à 3 niveaux :

```
Catégorie (ex: "Enclenchement et Suivi")
└── Sous-catégorie (ex: "Enclenchement")
    └── Tâche (ex: "Réunion")
        ├── base: {ALT_2P: 4, ALT_4P_L: 4, ...}
        ├── coeff_secteur: {INDUS: 1, OIL_GAS: 1.2, ...}
        ├── coeff_type_affaire: {IDENTIQUE_JE: 0, ...}
        ├── is_multiplicative: false
        └── ortems_repartition: {ING_ELECTROTECH_DEF: 0.5, ...}
```

### 13.4 `data/calculs.json`

| Clé | Contenu |
|-----|---------|
| `categories` | 5 catégories de calculs |
| `coeff_type_affaire` | Coefficients par type d'affaire et catégorie |
| `ortems_repartition` | Distribution ORTEMS par catégorie de calcul |
| `calculs` | Liste des calculs avec heures par machine et mode de sélection |

### 13.5 `data/options.json`

| Clé | Contenu |
|-----|---------|
| `categories` | 12 types d'options |
| `category_coeff` | Coefficients par catégorie et type d'affaire |
| `ortems_repartition` | Distribution ORTEMS par catégorie d'option |
| `options` | Options groupées par catégorie avec index, label, heures |

### 13.6 `data/LPDC.json`

| Clé | Contenu |
|-----|---------|
| `coeff_secteur` | Coefficients LPDC par secteur |
| `coeff_affaire` | Coefficients LPDC par type d'affaire |
| `categories` | `BASE` (obligatoire), `PART` (optionnel) |
| `ortems_repartition` | Distribution ORTEMS |
| `documents` | Documents avec applicabilité et règles de sélection |

### 13.7 `data/labo.json`

| Clé | Contenu |
|-----|---------|
| `categories` | `LAB_METAL`, `LAB_ISOL` |
| `ortems_repartition` | Distribution ORTEMS |
| `labo` | Travaux de labo avec heures et coefficients secteur |

---

## 14. Compilation et déploiement

### Script `build.bat`

Le fichier `build.bat` compile l'application en exécutable Windows via **PyInstaller** :

1. **Nettoyage** du répertoire cible sur le lecteur réseau (`\\SRV-JE-005\public_ji$\...`)
2. **Compilation PyInstaller** :
   - Mode `--onedir` (dossier unique)
   - Mode `--noconsole` (pas de fenêtre console)
   - Inclusion des ressources : `config.xml`, `data/`, `assets/`, `src/styles.qss` dans `_internal/`
3. **Résultat** : `ChiffrageHET.exe` (dans le dossier `dist/`)
4. **Déploiement** : copie vers le partage réseau

### Exécution manuelle

```batch
build.bat
```

---

## 15. Référence API — Classes et méthodes

### `ApplicationData` (`src/utils/ApplicationData.py`)

| Méthode | Description |
|---------|-------------|
| `__init__()` | Charge `config.xml`, tous les fichiers JSON, appelle `sort_raw_data()` |
| `load_config()` | Parse `config.xml` → chemins, thème, dimensions |
| `sort_raw_data()` | Transforme les données brutes en objets Python typés |

Attributs principaux :
- `tasks`, `lpdc_docs`, `options`, `calculs`, `labo` — données de référence
- `people`, `product_types`, `products`, `types_affaires`, `DAS`, `sectors` — catalogue
- `*_categories`, `*_coeff_*`, `*_ortems` — coefficients et distributions

---

### `Project` (`src/model.py`)

| Méthode | Description |
|---------|-------------|
| `context()` | Retourne le dictionnaire de contexte pour les calculs |
| `apply_defaults()` | Copie profonde des données de référence, filtre selon le contexte |
| `get_all_tasks()` | Aplatit la hiérarchie des tâches en liste |
| `grouped_calculs()` | Retourne `dict[catégorie] → list[Calcul]` |
| `grouped_options()` | Retourne `dict[catégorie] → list[Option]` |
| `grouped_lpdc()` | Retourne `dict[catégorie] → list[LPDCDocument]` |
| `grouped_labo()` | Retourne `dict[catégorie] → list[Labo]` |
| `compute_first_machine_subtotal()` | Somme de toutes les heures effectives |
| `compute_first_machine_total()` | Sous-total × (1 + divers%) |
| `_compute_multi_machine_coeff(qty)` | Calcul du coefficient multi-machines |
| `compute_n_machines_total()` | Total incluant toutes les machines |
| `calculate_total_with_rex()` | Total final avec REX |
| `make_ortems_repartition()` | Distribution sur postes de travail |
| `generate_summary_tree()` | Arbre récapitulatif pour l'affichage |
| `compute_tree_hours(node)` | Somme récursive des heures d'un nœud |
| `save_project()` | Sérialisation JSON avec delta |

---

### `Model` (`src/model.py`)

| Méthode | Description |
|---------|-------------|
| `save_project()` | Délègue à `project.save_project()` |
| `load_project(data)` | Restaure un projet depuis un dict JSON |

| Signal | Description |
|--------|-------------|
| `project_changed` | Émis après reconstruction complète |
| `data_updated` | Émis après modification mineure |

---

### `Controller` (`src/controller.py`)

| Méthode | Description |
|---------|-------------|
| `__init__(app_data, app)` | Crée la vue, le modèle, tous les contrôleurs d'onglets |
| Import/export wiring | Connecte les boutons import/export aux dialogues fichiers |

---

### `MachineDatabase` (`src/utils/MachineDatabase.py`)

Charge et interroge la base de machines REX depuis un fichier Excel.

| Méthode | Description |
|---------|-------------|
| `load()` | Charge les feuilles « Machines » et « Projets », normalise IP, extrait les valeurs uniques |
| `search(filters, tolerance)` | Filtre le DataFrame selon les critères (texte, numérique ± tolérance, dropdown) |
| `get_project_machines(project_id)` | Retourne toutes les machines d'un projet |
| `get_project_hours(project_id)` | Retourne les heures du projet (ventilation par code job) |
| `update_machine_cell(df_index, column, value)` | Met à jour une cellule en mémoire et dans le fichier Excel via openpyxl |
| `get_original_df_indices(project_id)` | Retourne les indices du DataFrame principal pour un projet |

Attributs principaux :
- `df` — DataFrame des machines
- `df_projets` — DataFrame des heures projet
- `unique_values` — dict des valeurs uniques par colonne (pour les filtres)

---

### `MachineSearchController` (`src/tabs/TabMachineSearch.py`)

| Méthode | Description |
|---------|-------------|
| `_on_search()` | Lance la recherche avec les filtres courants |
| `_on_double_click(index)` | Ouvre le `ProjectDetailDialog` pour le projet sélectionné |
| `_on_reset()` | Réinitialise les filtres et pré-remplit depuis le projet courant |
| `_update_produit_combo()` | Met à jour Produit selon Type produit |
| `_update_secteur_combo()` | Met à jour Secteur selon DAS |
| `_prefill_from_project()` | Pré-remplit Type produit, Produit, DAS depuis le projet courant |
| `_build_label_maps()` | Construit les mappings code → label pour l'affichage |

---

### `BaseTaskTabController` (`src/utils/BaseTaskTabController.py`)

| Méthode | Type | Description |
|---------|------|-------------|
| `_get_all_tasks()` | Abstraite | Retourne la liste des tâches à afficher |
| `_build_tables()` | Abstraite | Construit les widgets tableaux |
| `_connect_table(table)` | Concrète | Connecte les signaux d'un tableau |
| `_on_project_changed()` | Concrète | Reconstruit les tableaux |
| `_on_manual_change()` | Concrète | Met à jour `manual_hours` d'une tâche |
| `_on_checkbox_toggle()` | Concrète | Met à jour `is_selected` d'une tâche |

---

### `TaskTableWidget` (`src/utils/TabTasks.py`)

| Méthode | Description |
|---------|-------------|
| `add_category(name)` | Ajoute un en-tête de catégorie |
| `add_task(task, context)` | Ajoute une ligne de tâche |
| `show_table()` | Affiche le tableau complet |
| `update_table()` | Rafraîchit les valeurs sans recréer les widgets |
| `refresh()` | Reconstruction complète du tableau |

| Signal | Description |
|--------|-------------|
| `manual_value_modified(index, value)` | Modification manuelle d'heures |
| `checkbox_toggled(index, state)` | Changement de sélection |

---

### Widgets personnalisés (`src/utils/widgets.py`)

| Widget | Description |
|--------|-------------|
| `NoWheelSpinBox` | SpinBox qui ignore les événements de molette (évite les modifications accidentelles) |
| `CoefficientSpinBox` | SpinBox spécialisée pour la saisie de coefficients |

---

### Fonctions d'export (`src/utils/exports.py`)

| Fonction | Description |
|----------|-------------|
| `export_ortems_excel(project, path)` | Génère le fichier Excel ORTEMS |
| `export_excel_report(project, path)` | Génère le rapport de chiffrage Excel |

---

## 16. Problèmes connus

*(Issus de `notes.txt`)*

| # | Description | Impact |
|---|-------------|--------|
| 1 | La feuille 'tri1 LPDC' cellule C2:I2 référence incorrectement des lignes calculs pour le flag asynchrone | Erreur de calcul LPDC pour machines asynchrones |
| 2 | La feuille 'chiffrage' cellule D19 (tâche réunion) référence la mauvaise ligne de données pour le cas marine militaire | Heures incorrectes pour les projets MIL |
| 3 | La section Labo nécessite des tests complets sur tous les types d'affaire | Fiabilité incertaine des calculs labo |
| 4 | La logique de calcul ORTEMS est incomplète et nécessite une validation par rapport à la référence Excel | Distribution ORTEMS potentiellement incorrecte |

---

*Documentation générée le 19 mars 2026. Basée sur l'analyse complète du code source HET_3.*
