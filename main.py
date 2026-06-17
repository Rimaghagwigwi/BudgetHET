import os
import sys
from PyQt6.QtWidgets import QApplication
from src.controller import Controller
from src.model import ApplicationData


def _get_startup_project_path(argv: list[str]) -> str | None:
    """Retourne le premier fichier JSON existant passé en argument, sinon None."""
    for arg in argv[1:]:
        candidate = os.path.abspath(arg.strip('"'))
        if os.path.isfile(candidate) and candidate.lower().endswith(".json"):
            return candidate
    return None

if __name__ == "__main__":
    # Chargement des données
    application_data = ApplicationData()
    application_data.sort_raw_data()
    startup_project_path = _get_startup_project_path(sys.argv)
    
    # Lancement de l'application
    app = QApplication(sys.argv)
    app.setStyle(application_data.ui_theme) # Look plus moderne par défaut sur Windows
    
    controller = Controller(application_data, startup_project_path=startup_project_path)
    
    sys.exit(app.exec())