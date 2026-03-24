import json
import os
import subprocess
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

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
from src.tabs.TabMachineSearch import TabMachineSearch, MachineSearchController


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
            (TabMachineSearch(), MachineSearchController, "Recherche Machines"),
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
        self.view_summary.export_excel_clicked.connect(self.on_export_excel_report)
        self.view_summary.quick_export_clicked.connect(self.on_quick_export)

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

    def on_quick_export(self):
        try:
            from src.utils.exports import quick_export
            paths = quick_export(self.model)
            
            data = self.model.save_project()
            file_name = f"{self.model.project.crm_number}_{self.model.project.revision}_{self.model.project.date}.json"
            save_dir = self.model.app_data.project_save_dir
            os.makedirs(save_dir, exist_ok=True)
            json_path = os.path.join(save_dir, file_name)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            all_paths = [
                ("Sauvegarde JSON", json_path),
                ("Prepa ORTEMS", paths["ortems"]),
                ("Rapport chiffrage", paths["rapport"]),
            ]
            self._show_export_result_dialog(all_paths)
        except Exception as e:
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de l'export rapide :\n{e}")

    def _show_export_result_dialog(self, file_entries: list):
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Export rapide terminé")
        dialog.setMinimumWidth(800)
        layout = QVBoxLayout(dialog)

        title = QLabel("Export rapide terminé")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        for label_text, filepath in file_entries:
            normalized = os.path.normpath(filepath)
            row = QHBoxLayout()
            desc = QLabel(f"{label_text}:")
            desc.setFixedWidth(130)
            link = QLabel(f'<a href="#">{normalized}</a>')
            link.setTextFormat(Qt.TextFormat.RichText)
            link.setWordWrap(True)
            link.linkActivated.connect(lambda _, p=normalized: subprocess.Popen(["explorer", "/select,", p]))
            row.addWidget(desc)
            row.addWidget(link, 1)
            layout.addLayout(row)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def _on_export_json(self):
        default_dir = self.model.app_data.project_save_dir
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
        default_dir = self.model.app_data.project_save_dir
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

    def on_export_excel_report(self):
        default_dir = self.model.app_data.project_save_dir
        crm = self.model.project.crm_number or "projet"
        rev = self.model.project.revision or "rev"
        default_path = os.path.join(default_dir, f"{crm}_{rev}_report.xlsx")
        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Exporter rapport Excel",
            default_path,
            "Fichiers Excel (*.xlsx)",
        )
        if not path:
            return
        try:
            self.model.project.export_excel_report(path)
            print(f"Rapport Excel exporté : {path}")
        except Exception as e:
            print(f"Erreur export rapport Excel : {e}")
