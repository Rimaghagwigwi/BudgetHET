import sys
from PyQt6.QtWidgets import QApplication
from src.controller import Controller
from src.model import ApplicationData

if __name__ == "__main__":
    # Chargement des données
    application_data = ApplicationData()
    application_data.sort_raw_data()
    
    # Lancement de l'application
    app = QApplication(sys.argv)
    app.setStyle(application_data.ui_theme) # Look plus moderne par défaut sur Windows
    
    controller = Controller(application_data)
    
    sys.exit(app.exec())