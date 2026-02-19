# Budget_HET - Chiffrage HET

Application desktop de chiffrage d'heures d'etudes pour projets industriels (Jeumont Electric), developpee en Python avec PyQt6. Remplace le fichier Excel BUDGET_HET.

> **Note** : Les resultats peuvent legerement differer de l'Excel en raison du passage aux DAS. Les secteurs Oil&Gas et Industrie sont regroupes dans les Machines speciales.

## Fonctionnalites

- **General** : Saisie des informations projet (Client, CRM, DAS, type de produit, quantite, revision...).
- **Taches** : Heures d'ingenierie de base par type de machine, ajustees par coefficients secteur/affaire.
- **Calculs** : Heures de calcul avec coefficients specifiques au type d'affaire.
- **LPDC** : Documents contractuels obligatoires et optionnels selon le DAS, avec ajustement manuel des heures.
- **Options** : Catalogue d'options groupees (Mecanique, Electrique, Essais...), activables et editables.
- **Labo** : Heures d'essais laboratoire.
- **Resume** : Total des heures en temps reel, avec divers (5 % par defaut) et coefficient REX manuel.

## Architecture

Architecture **MVC** :

```
main.py                      # Point d'entree
config.xml                   # Configuration (chemins, theme UI, dimensions fenetre)
src/
  model.py                   # Classe Model (Project + calculs agreges)
  view.py                    # MainWindow (PyQt6)
  controller.py              # Controleur principal, instancie les onglets
  tabs/                      # Un controleur par onglet (General, Taches, Calculs, Options, LPDC, Labo, Resume)
  utils/
    TabTasks.py              # Table Widget et view commun pour les onglets tâches
    BaseTaskTabController.py # Classe abstraite de controller pour les onglets tâches
    ApplicationData.py       # Chargement et parsing de tous les fichiers de donnees
    Task.py                  # Dataclasses : GeneralTask, LPDCDocument, Option, Calcul, Labo
data/
  base_data.json             # Listes (Clients, DAS, types d'affaires, coefficients...)
  general_task_data_new.json # Taches de base avec heures et coefficients par machine/affaire
  LPDC.json                  # Documents contractuels et regles d'activation
  options.json               # Catalogue des options
  calculs.json               # Taches de calcul
  labo.json                  # Taches laboratoire
```

## Installation

**Prerequis** : Python 3.10+

```bash
pip install PyQt6
```

## Lancement

```bash
python main.py
```

1. Remplir l'onglet **General** et valider pour charger les donnees par defaut.
2. Ajuster les onglets **Taches**, **Calculs**, **LPDC**, **Options** et **Labo**.
3. Consulter l'onglet **Resume** pour le total final.

## Configuration

Tout est parametrable sans toucher au code :

- `config.xml` : chemins des fichiers, theme Qt (`Fusion`), dimensions de la fenetre.
- `data/*.json` : regles metier, heures standard, coefficients, catalogue d'options et de documents.