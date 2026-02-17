# Budget_HET

Application de chiffrage et de calcul d'heures pour projets industriels, développée en Python avec PyQt6.


## Commentaires généraux

*   **Objectifs** : 
    *   Remplacer le fichier Excel BUDGET_HET pour le chiffrage des heures d'études d'un projet.
    *   Passer à une architechture plus orientée vers l'utilisateur et éviter les mauvaises manipulations.
    *   S'adapter aux évolutions de Jeumont Electric (passage aux DAS)
    *   Garder un maximum de modularité.

*   **Notes** : Les résultats peuvent légèrement différés par rapport à l'excel, à cause du pasage aux DAS. Les secteurs Oil&Gas et industrie sont réunis dans les Machines spéciales.

## Fonctionnalités

*   **Gestion de Projet** : Saisie des informations générales (Client, CRM, DAS, Type de produit, etc.).
*   **Calcul Automatique** : Chargement automatique des tâches et heures de base selon le type de produit sélectionné.
*   **Documents Contractuels (LPDC)** :
    *   Gestion des documents obligatoires selon le DAS.
    *   Sélection de documents optionnels.
    *   Ajustement manuel des heures par document.
*   **Options** :
    *   Catalogue d'options groupées par catégories (Mécanique, Électrique, Essais, etc.).
    *   Activation/Désactivation et modification des heures associées.
*   **Synthèse** :
    *   Calcul en temps réel du total des heures.
    *   Répartition des heures par métier/rôle (Ingénierie, Documentation, Options, etc.).

## Structure du Projet

Le projet suit une architecture **MVC (Modèle-Vue-Contrôleur)** :

*   `main.py` : Point d'entrée de l'application.
*   `src/` : Code source.
    *   `model.py` : Logique métier et données (Calculs, Dataclasses Task/Option/Document).
    *   `view.py` : Interface graphique principale (MainWindow).
    *   `controller.py` : Chef d'orchestre reliant le Modèle et la Vue.
    *   `tabs/` : Composants d'interface pour chaque onglet (Général, LPDC, Options, Synthèse).
*   `data/` : Fichiers de configuration JSON.
    *   `base_data.json` : Listes déroulantes (Clients, DAS, Types d'affaires...).
    *   `tasks_matrix.json` : Matrice complète des tâches, heures de base et coefficients (Affaire/DAS).
    *   `LPDC.json` : Base de données des documents contractuels et règles d'application.
    *   `options.json` : Catalogue des options disponibles.

## Installation

1.  Assurez-vous d'avoir **Python 3.10+** installé.
2.  Installez les dépendances :
    ```bash
    pip install PyQt6
    ```
    *(Ou via requirements.txt si disponible)*

## Utilisation

Pour lancer l'application :

```bash
python main.py
```

1.  Remplissez l'onglet **Général** et cliquez sur "Appliquer" pour charger les données par défaut.
2.  Naviguez dans les onglets **LPDC** et **Options** pour affiner le chiffrage.
3.  Consultez l'onglet **Tâches** pour voir le détail des heures d'ingénierie.
4.  L'onglet **Synthèse** affiche le résultat final.

## Configuration

Les fichiers dans le dossier `data/` peuvent être modifiés pour ajuster les règles métier sans toucher au code :

*   Pour ajouter une option : éditez `data/options.json`.
*   Pour changer les heures standard ou les coefficients : éditez `data/tasks_matrix.json`.
