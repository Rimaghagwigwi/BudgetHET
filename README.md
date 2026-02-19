# Budget_HET � Chiffrage HET

Application desktop de chiffrage d'heures d'�tudes pour projets industriels (Jeumont Electric), d�velopp�e en Python avec PyQt6. Remplace le fichier Excel BUDGET_HET.

> **Note** : Les r�sultats peuvent l�g�rement diff�rer de l'Excel en raison du passage aux DAS. Les secteurs Oil&Gas et Industrie sont regroup�s dans les Machines sp�ciales.

## Fonctionnalit�s

- **G�n�ral** : Saisie des informations projet (Client, CRM, DAS, type de produit, quantit�, r�vision�).
- **T�ches** : Heures d'ing�nierie de base par type de machine, ajust�es par coefficients secteur/affaire.
- **Calculs** : Heures de calcul avec coefficients sp�cifiques au type d'affaire.
- **LPDC** : Documents contractuels obligatoires et optionnels selon le DAS, avec ajustement manuel des heures.
- **Options** : Catalogue d'options group�es (M�canique, �lectrique, Essais�), activables et �ditables.
- **Labo** : Heures d'essais laboratoire.
- **R�sum�** : Total des heures en temps r�el, avec divers (5 % par d�faut) et coefficient REX manuel.

## Architecture

Architecture **MVC** :

```
main.py                      # Point d'entr�e
config.xml                   # Configuration (chemins, th�me UI, dimensions fen�tre)
src/
  model.py                   # Classe Model (Project + calculs agr�g�s)
  view.py                    # MainWindow (PyQt6)
  controller.py              # Contr�leur principal, instancie les onglets
  tabs/                      # Un contr�leur par onglet (G�n�ral, T�ches, Calculs, Options, LPDC, Labo, R�sum�)
  utils/
    TabTasks.py              # Widget et view commun pour les onglets tâches
    BaseTaskTabController.py # Classe abstraite de controler pour les onglets tâches
    ApplicationData.py       # Chargement et parsing de tous les fichiers de donn�es
    Task.py                  # Dataclasses : GeneralTask, LPDCDocument, Option, Calcul, Labo
data/
  base_data.json             # Listes (Clients, DAS, types d affaires, coefficients�)
  general_task_data_new.json # T�ches de base avec heures et coefficients par machine/affaire
  LPDC.json                  # Documents contractuels et r�gles d activation
  options.json               # Catalogue des options
  calculs.json               # T�ches de calcul
  labo.json                  # T�ches laboratoire
```

## Installation

**Pr�requis** : Python 3.10+

```bash
pip install PyQt6
```

## Lancement

```bash
python main.py
```

1. Remplir l'onglet **G�n�ral** et valider pour charger les donn�es par d�faut.
2. Ajuster les onglets **T�ches**, **Calculs**, **LPDC**, **Options** et **Labo**.
3. Consulter l'onglet **R�sum�** pour le total final.

## Configuration

Tout est param�trable sans toucher au code :

- `config.xml` : chemins des fichiers, th�me Qt (`Fusion`), dimensions de la fen�tre.
- `data/*.json` : r�gles m�tier, heures standard, coefficients, catalogue d'options et de documents.
