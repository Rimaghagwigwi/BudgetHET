# Budget_HET - Chiffrage HET

Application desktop de chiffrage d'heures d'études pour projets industriels (Jeumont Electric), développée en Python avec PyQt6. Remplace le fichier Excel BUDGET_HET.

---

## Table des matières

1. [Installation](#installation)
2. [Utilisation](#utilisation)
   - [Flux de travail](#flux-de-travail)
   - [Description des onglets](#description-des-onglets)
   - [Modifier les fichiers de données](#modifier-les-fichiers-de-données)
3. [Notes et remarques](#notes-et-remarques)
4. [Détails techniques](#détails-techniques)

---

## Installation

**Prérequis** : Python 3.10+

```bash
pip install -r requirements.txt
# ou
pip install PyQt6
```

**Lancement** :

```bash
python main.py
```

---

## Utilisation

### Flux de travail

1. **Onglet Général** → Remplir les informations projet (Client, CRM, DAS, type de produit, quantité, révision) puis **valider** pour charger les données par défaut.
2. **Onglet Tâches** → Ajuster les heures d'ingénierie par tâche selon le projet.
3. **Onglet Calculs** → Sélectionner et ajuster les heures de calcul (électromagnétique, mécanique, aéraulique).
4. **Onglet LPDC** → Sélectionner les documents contractuels obligatoires/optionnels selon le DAS.
5. **Onglet Options** → Activer les options techniques par catégorie (ATEX, instrumentation, essais...).
6. **Onglet Labo** → Définir les heures d'essais laboratoire (métallurgie, isolation).
7. **Onglet Résumé** → Consulter le total final en temps réel, avec coefficient REX et pourcentage divers.

### Description des onglets

| Onglet | Fonction | Données associées |
|--------|----------|-------------------|
| **Général** | Saisie des informations projet : Client, CRM, DAS, type de produit, quantité, révision | `base_data.json` |
| **Tâches** | Heures d'ingénierie de base par type de machine, ajustées par coefficients secteur/affaire | `general_task_data_new.json` |
| **Calculs** | Heures de calcul (électromagnétique, bobinage, mécanique, ANSYS, aéraulique/thermique) | `calculs.json` |
| **LPDC** | Documents contractuels obligatoires et optionnels selon le DAS | `LPDC.json` |
| **Options** | Catalogue d'options groupées (ATEX, Instrumentation, Essais, Normes, etc.) | `options.json` |
| **Labo** | Heures d'essais laboratoire (métallurgie, isolation) | `labo.json` |
| **Résumé** | Total des heures en temps réel, avec divers (5% par défaut) et coefficient REX manuel | — |

### Modifier les fichiers de données

Tous les fichiers de données sont situés dans le dossier `data/`. Ils sont au format JSON et peuvent être édités avec n'importe quel éditeur de texte.

#### `base_data.json` — Données de base

Contient les listes de référence utilisées dans l'onglet Général :

```json
{
  "people": ["Walid BOUGHANMI", "Thérèse VANDEWYNCKEL", ...],
  "product_types": {
    "SYNCH": "Synchrone",
    "ASYNCH": "Asynchrone",
    "MIL": "Marine militaire"
  },
  "products": {
    "SYNCH": { "ALT_2P": "Alternateur 2p", ... },
    "ASYNCH": { "ASYNCH_CAGE": "Asynchrone à cage", ... },
    "MIL": { "MEP": "MEP", "ANR/DAR": "ANR/DAR", "TAR": "TAR" }
  },
  "types_affaire": { "NEUF": "Machine neuve", ... },
  "DAS": { "MS": "Machines spéciales", "NUC": "Nucléaire", "MIL": "Marine militaire" },
  "sectors": { ... },
  "jobs": { ... },
  "job_suffixes": { "DEF": "Définition", "PROD": "Production" }
}
```

**Pour ajouter un nouveau client** : ajouter une entrée dans `"people"`.

**Pour ajouter un nouveau type de produit** : ajouter une clé dans `"product_types"` et les produits correspondants dans `"products"`.

---

#### `general_task_data_new.json` — Tâches d'ingénierie

Structure hiérarchique des tâches avec heures de base par type de machine :

```json
{
  "tasks": {
    "Enclenchement et Suivi": {
      "Enclenchement": {
        "réunion": {
          "base": {
            "ALT_2P": 4, "ALT_4P_L": 4, ...,
            "MEP": 700, "ANR/DAR": 500, "TAR": 600
          },
          "coeff_secteur": { "INDUS": 1, "OIL_GAS": 2, ... },
          "ortems_repartition": { "RESP_ET_PROJ_DEF": 1 }
        },
        ...
      }
    },
    "PLANS FAB / SPEC d'Achat / LDN": { ... }
  }
}
```

**Propriétés d'une tâche** :
- `base` : Heures de base par type de produit (ALT_2P, ASYNCH_CAGE, MEP, etc.)
- `coeff_secteur` : Multiplicateurs par secteur (INDUS, OIL_GAS, NUC_QUALIFIE, etc.)
- `coeff_type_affaire` : Multiplicateurs par type d'affaire (NEUF, IDENTIQUE_JE, REMPLACEMENT)
- `is_multiplicative` : Si `true`, les heures sont multipliées par la quantité de machines
- `ortems_repartition` : Répartition par métier pour l'export ORTEMS

**Pour modifier une heure de base** : changer la valeur dans `"base"` pour le type de machine concerné.

---

#### `calculs.json` — Tâches de calcul

Liste des calculs avec catégories et règles de sélection :

```json
{
  "categories": {
    "ELECMAG": "Électromagnétique",
    "BOB": "Bobinage",
    "CONCEPT_MECA": "Conception mécanique",
    "MECA_ANSYS": "Mécanique ANSYS",
    "AERO_THERMIQUE": "Aéraulique et Thermique"
  },
  "coeff_type_affaire": { ... },
  "ortems_repartition": { ... },
  "calculs": [
    {
      "index": 6,
      "label": "Calcul magnétique et thermique machine",
      "category": "ELECMAG",
      "hours": { "ASYNCH": 8, "SYNCH": 8 },
      "selection": {
        "ASYNCH": "mandatory",
        "SYNCH": "mandatory",
        "MIL": "optional"
      }
    },
    ...
  ]
}
```

**Règles de sélection** :
- `"mandatory"` : Le calcul est automatiquement sélectionné
- `"optional"` : Le calcul est disponible mais non sélectionné par défaut
- Absence de clé : Le calcul n'est pas disponible pour ce type de produit

---

#### `options.json` — Catalogue d'options

Options groupées par catégorie avec heures associées :

```json
{
  "categories": {
    "ATEX": "Certification ou ATEX",
    "INSTRUM": "Instrumentation et accessoires",
    "ESSAIS": "Essais",
    ...
  },
  "category_coeff": { ... },
  "ortems_repartition": { ... },
  "options": {
    "ATEX": [
      { "index": 12, "label": "ATEX Expb (Z1)", "hours": 50 },
      { "index": 13, "label": "ATEX Expzc (Z2)", "hours": 50 },
      ...
    ],
    ...
  }
}
```

**Pour ajouter une option** : ajouter un objet dans le tableau de la catégorie concernée avec un `index` unique.

---

#### `LPDC.json` — Documents contractuels

Liste des documents par DAS avec règles de sélection obligatoire/optionnelle.

---

#### `labo.json` — Essais laboratoire

```json
{
  "categories": { "LAB_METAL": "Labo métallurgie", "LAB_ISOL": "Labo isolant" },
  "ortems_repartition": { ... },
  "labo": [
    { "index": 1, "label": "Labo Métalo", "category": "LAB_METAL", "hours": 0 },
    { "index": 2, "label": "Labo isolant", "category": "LAB_ISOL", "hours": 0 }
  ]
}
```

---

## Notes et remarques

### Travaux en cours

- Finaliser l'onglet Labo
- Créer et sauvegarder les autres projets militaires
- Vérifier les paramètres hydrauliques (à discuter avec l'équipe)
- Pour l'export ORTEMS : mettre la logique de calculs dans le Python

### Erreurs identifiées dans les fichiers Excel d'origine

> **⚠️ Ces erreurs existaient dans le fichier Excel BUDGET_HET original et sont corrigées dans cette application.**

1. **Erreur LPDC (asynchrone)** :
   - Localisation : `'tri1 LPDC'C2:I2`
   - Condition erronée : `'tri calculs'C4="asynchrone"` et `'tri calculs'D4="asynchrone"` toujours **FAUX** (mauvaise référence de cellule)
   - Impact : Résultats LPDC incorrects pour les machines asynchrones

2. **Erreur tâches réunion (Marine militaire)** :
   - Localisation : `'chiffrage'D19` (tâches réunion)
   - Problème : Référence `'data produit'!$D8:$M8` au lieu de `'data produit'!$D2:$M2`
   - Impact : La ligne "réunion" était une copie de "Tracé d'ensemble (3D)" au lieu des heures de réunion

---

## Détails techniques

### Architecture MVC

```
main.py                      # Point d'entrée
config.xml                   # Configuration (chemins, thème UI, dimensions fenêtre)
src/
  model.py                   # Classe Model (Project + calculs agrégés)
  view.py                    # MainWindow (PyQt6)
  controller.py              # Contrôleur principal, instancie les onglets
  tabs/                      # Un contrôleur par onglet (General, Taches, Calculs, Options, LPDC, Labo, Resume)
  utils/
    TabTasks.py              # Table Widget et view commun pour les onglets tâches
    BaseTaskTabController.py # Classe abstraite de contrôleur pour les onglets tâches
    ApplicationData.py       # Chargement et parsing de tous les fichiers de données
    Task.py                  # Dataclasses : GeneralTask, LPDCDocument, Option, Calcul, Labo
data/
  base_data.json             # Listes (Clients, DAS, types d'affaires, coefficients...)
  general_task_data_new.json # Tâches de base avec heures et coefficients par machine/affaire
  LPDC.json                  # Documents contractuels et règles d'activation
  options.json               # Catalogue des options
  calculs.json               # Tâches de calcul
  labo.json                  # Tâches laboratoire
template/
  ortems_template.xlsx       # Template Excel pour l'export ORTEMS
```

### Configuration (`config.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<config>
    <datapaths>
        <path key="base_data">data/base_data.json</path>
        <path key="options">data/options.json</path>
        <path key="tasks">data/general_task_data_new.json</path>
        <path key="LPDC">data/LPDC.json</path>
        <path key="calculs">data/calculs.json</path>
        <path key="labo">data/labo.json</path>
    </datapaths>
    <asset-dir>assets/</asset-dir>
    <ortems-template-path>template/ortems_template.xlsx</ortems-template-path>
    <ui>
        <theme>Fusion</theme>
        <stylesheet>src/styles.qss</stylesheet>
        <window>
            <title>Chiffrage HET</title>
            <width>1080</width>
            <height>720</height>
        </window>
    </ui>
</config>
```

### Export ORTEMS

L'application peut exporter les heures vers un fichier Excel compatible ORTEMS via le template `template/ortems_template.xlsx`.

La répartition par métier (job) est définie dans les fichiers JSON via la propriété `ortems_repartition`. Exemple :

```json
"ortems_repartition": {
  "PROJ_MACHINE_DEF": 0.7,
  "ING_MEC_SOL_DEF": 0.3
}
```

Les codes métiers disponibles sont définis dans `base_data.json` (`jobs` et `job_suffixes`).