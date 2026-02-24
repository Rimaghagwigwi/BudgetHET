import json
import os
from PyQt6.QtWidgets import QFileDialog

from src.model import Model
from src.view import MainWindow
from src.tabs.TabGeneral import TabGeneral, TabGeneralController
from src.utils.TabTasks import TabTasks
from src.tabs.GeneralTaskTabController import GeneralTaskTabController
from src.tabs.CalculsTabController import CalculsTabController
from src.tabs.OptionsTabController import OptionsTabController
from src.tabs.LPDCTabController import LPDCTabController
from src.tabs.LaboTabController import LaboTabController
from src.tabs.TabSummary import TabSummary, TabSummaryController


class Controller:
    def __init__(self, application_data):
        self.model = Model(app_data=application_data)
        self.window = MainWindow(application_data)
        self.controllers = self._create_tabs()
        self._connect_io_signals()
        self.window.show()

    def _create_tabs(self):
        """Crée tous les onglets et leurs contrôleurs."""
        self.view_general = TabGeneral()
        self.view_summary = TabSummary()

        tab_configs = [
            (self.view_general, TabGeneralController,     "Général"),
            (TabTasks(),        GeneralTaskTabController, "Tâches"),
            (TabTasks(),        CalculsTabController,     "Calculs"),
            (TabTasks(),        OptionsTabController,     "Options"),
            (TabTasks(),        LPDCTabController,        "LPDC"),
            (TabTasks(),        LaboTabController,        "Labo"),
            (self.view_summary, TabSummaryController,     "Résumé"),
        ]

        controllers = []
        for view, ctrl_class, title in tab_configs:
            ctrl = ctrl_class(self.model, view)
            controllers.append(ctrl)
            self.window.add_tab(view, title)

        # Références nommées pour les contrôleurs nécessaires à l'import/export
        self.ctrl_general: TabGeneralController = controllers[0]
        return controllers

    def _connect_io_signals(self):
        self.view_general.btn_import.clicked.connect(self._on_import_project)
        self.view_summary.export_json_clicked.connect(self._on_export_json)
        self.view_summary.export_ortems_clicked.connect(self._on_export_ortems)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def _on_import_project(self):
        default_dir = self.model.app_data.asset_dir
        path, _ = QFileDialog.getOpenFileName(
            self.window, "Importer un projet", default_dir, "Projets JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.model.load_project(data)
            self.ctrl_general.load_project_to_ui()
            self.model.project_changed.emit()
        except Exception as e:
            print(f"Erreur lors de l'import du projet : {e}")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export_json(self):
        default_dir = self.model.app_data.asset_dir
        crm = self.model.project.crm_number or "projet"
        rev = self.model.project.revision or "rev"
        default_path = os.path.join(default_dir, f"{crm}_{rev}.json")
        path, _ = QFileDialog.getSaveFileName(
            self.window, "Exporter le projet", default_path, "Projets JSON (*.json)"
        )
        if not path:
            return
        try:
            data = self.model.save_project()
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Projet exporté : {path}")
        except Exception as e:
            print(f"Erreur lors de l'export du projet : {e}")

    def _on_export_ortems(self):
        default_dir = self.model.app_data.asset_dir
        crm = self.model.project.crm_number or "projet"
        rev = self.model.project.revision or "rev"
        default_path = os.path.join(default_dir, f"{crm}_{rev}.xlsx")
        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Exporter ORTEMS",
            default_path,
            "Fichiers Excel (*.xlsx)",
        )
        if not path:
            return
        try:
            self.model.project.export_ortems_excel(path)
            print(f"Export ORTEMS : {path}")
        except Exception as e:
            print(f"Erreur export ORTEMS : {e}")
