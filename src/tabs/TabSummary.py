from typing import Any, Dict, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QTreeWidget, QTreeWidgetItem,
                             QHBoxLayout, QGridLayout, QLineEdit, QPushButton, QMenu,
                             QDialog, QDialogButtonBox, QGroupBox, QFormLayout, QScrollArea,
                             QToolButton)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFont, QRegularExpressionValidator, QIcon
from src.model import Model, Project
from src.utils.Task import AbstractTask

float_validator = QRegularExpressionValidator(QRegularExpression(r"^-?\d*\.?\d*$"))

class CollapsibleSection(QTreeWidget):
    """Widget arbre déroulant pour afficher la hiérarchie des tâches."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setColumnCount(2)  # Nom et Heures
        self.setHeaderLabels(["Description", "Heures"])
        self.setAlternatingRowColors(True)
        self.setIndentation(15)
        self.resizeColumnToContents(0)

    def _get_expanded_paths(self) -> set:
        """Sauvegarde les chemins des noeuds dépliés."""
        expanded = set()
        for i in range(self.topLevelItemCount()):
            self._collect_expanded(self.topLevelItem(i), "", expanded)
        return expanded

    def _collect_expanded(self, item: QTreeWidgetItem, path: str, expanded: set):
        current = f"{path}/{item.text(0)}"
        if item.isExpanded():
            expanded.add(current)
        for i in range(item.childCount()):
            self._collect_expanded(item.child(i), current, expanded)

    def _restore_expanded(self, paths: set):
        """Restaure l'état déplié des noeuds."""
        for i in range(self.topLevelItemCount()):
            self._apply_expand(self.topLevelItem(i), "", paths)

    def _apply_expand(self, item: QTreeWidgetItem, path: str, paths: set):
        current = f"{path}/{item.text(0)}"
        if current in paths:
            item.setExpanded(True)
        for i in range(item.childCount()):
            self._apply_expand(item.child(i), current, paths)

    def build_tree(self, items: Dict[str, Any], context: Dict[str, Any], rex_coeff: float = 1.0):
        """Construit l'arbre à partir d'un dictionnaire de données."""
        self._rex_coeff = rex_coeff
        expanded = self._get_expanded_paths()

        self.clear()
        for label, value in items.items():
            self._add_node(label, value, None, context)

        self.setColumnWidth(0, self.width()-100)
        if expanded:
            self._restore_expanded(expanded)
        else:
            self.collapseAll()

    def _add_node(self, label: str, value: Any, parent: QTreeWidgetItem | None, context: Dict[str, Any]):
        """Ajoute récursivement un noeud à l'arbre."""
        item = QTreeWidgetItem([label, ""])
        
        if parent is None:
            self.addTopLevelItem(item)
            item.setFont(0, QFont("Arial", 11, QFont.Weight.Bold))
        else:
            parent.addChild(item)

        # Calculer les heures selon le type
        if isinstance(value, dict):
            total_hours = sum(self._add_node(sub_label, subvalue, item, context) 
                            for sub_label, subvalue in value.items())
            is_bold = parent is None
        elif isinstance(value, list):
            total_hours = sum(self._add_task_node(task, item, context) 
                            for task in value if isinstance(task, AbstractTask))
            is_bold = parent is None
        elif isinstance(value, AbstractTask):
            return self._add_task_node(value, parent, context)
        else:
            return 0.0
        
        # Masquer si aucune heure, sinon afficher
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        if total_hours == 0:
            item.setHidden(True)
        else:
            item.setText(1, f"{total_hours:.2f} h")
            if is_bold:
                item.setFont(1, QFont("Arial", 11, QFont.Weight.Bold))
        
        return total_hours

    def _add_task_node(self, task: AbstractTask, parent: QTreeWidgetItem, context: Dict[str, Any]) -> float:
        """Ajoute un noeud de tâche et retourne ses heures effectives (× REX)."""
        hours = task.effective_hours(context) * self._rex_coeff
        
        # Cacher les tâches à 0h
        if hours == 0:
            return 0.0
        
        item = QTreeWidgetItem([task.label, f"{hours:.2f} h"])
        item.setData(0, Qt.ItemDataRole.UserRole, task)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        
        # Style pour les tâches modifiées manuellement
        if task.manual_hours is not None:
            item.setFont(1, QFont("Arial", 11, QFont.Weight.Bold))
            item.setToolTip(1, f"Valeur manuelle: {task.manual_hours:.2f}h")
        
        if parent:
            parent.addChild(item)
        return hours


class TabSummary(QWidget):
    """Onglet récapitulatif affichant toutes les tâches et les totaux."""
    
    divers_changed = pyqtSignal(float)
    rex_coeff_changed = pyqtSignal(float)
    rex_hours_changed = pyqtSignal(float)
    rex_hours_cleared = pyqtSignal()
    quick_export_clicked = pyqtSignal()
    export_json_clicked = pyqtSignal()
    export_ortems_clicked = pyqtSignal()
    export_excel_clicked = pyqtSignal()
    delai_settings_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Arbre déroulant
        self.tree = CollapsibleSection("Détails")
        self.main_layout.addWidget(self.tree, stretch=1)
        
        # Pied de page avec totaux
        self.bottom_frame = self._create_totals_section()
        self.main_layout.addWidget(self.bottom_frame)

    def _create_styled_label(self, text: str = "0.00 h", object_name: str = "") -> QLabel:
        """Crée un label avec style aligné à droite."""
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        return label
    
    def _create_percentage_input(self, placeholder: str) -> Tuple[QHBoxLayout, QLineEdit]:
        container = QHBoxLayout()
        edit_percent = QLineEdit()
        # Limiteur pour n'accepter que les nombres
        edit_percent.setValidator(float_validator)
        edit_percent.setPlaceholderText(placeholder)
        edit_percent.setAlignment(Qt.AlignmentFlag.AlignRight)
        edit_percent.setFixedWidth(60)
        container.addWidget(edit_percent)
        container.addWidget(QLabel("%"))
        return container, edit_percent
    
    def _add_row_separator(self, layout: QGridLayout, row: int):
        """Ajoute un séparateur horizontal fin entre deux lignes."""
        sep = QFrame()
        sep.setObjectName("rowSeparator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep, row, 0, 1, 2)

    def _create_totals_section(self) -> QFrame:
        """Crée la section des totaux en bas de l'onglet."""
        frame = QFrame()
        frame.setObjectName("totalsFrame")
        layout = QGridLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        row = 0

        # Bouton Exporter avec menu déroulant
        self.btn_export = QPushButton("Exporter le projet ▾")
        export_menu = QMenu(self.btn_export)

        self.action_quick_export = export_menu.addAction("Export rapide")
        self.action_quick_export.triggered.connect(self.quick_export_clicked.emit)

        self.action_export_json = export_menu.addAction("Sauvegarde - JSON")
        self.action_export_json.triggered.connect(self.export_json_clicked.emit)

        self.action_export_ORTEMS = export_menu.addAction("ORTEMS - Excel")
        self.action_export_ORTEMS.triggered.connect(self.export_ortems_clicked.emit)

        self.action_export_excel = export_menu.addAction("Rapport - Excel")
        self.action_export_excel.triggered.connect(self.export_excel_clicked.emit)

        self.btn_export.setMenu(export_menu)
        layout.addWidget(self.btn_export, row, 0, 1, 2)
        row += 1
        self._add_row_separator(layout, row); row += 1

        # Subtotal 1ère machine (sans divers)
        label_first_machine = self._create_styled_label(text="Sous-total 1ère machine:")
        self.val_first_machine_subtotal = self._create_styled_label(object_name="important")
        layout.addWidget(label_first_machine, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.val_first_machine_subtotal, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1
        self._add_row_separator(layout, row); row += 1
        
        # Divers (%)
        divers_label = self._create_styled_label(text="Divers risques techniques:")
        divers_container, self.edit_divers = self._create_percentage_input("0.0")
        self.edit_divers.editingFinished.connect(self._on_divers_text_changed)
        layout.addWidget(divers_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(divers_container, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1
        self._add_row_separator(layout, row); row += 1
        
        # Total 1ère machine (avec divers)
        total_label = self._create_styled_label(text="Total 1ère machine :")
        self.val_first_machine_total = self._create_styled_label(object_name="important")
        layout.addWidget(total_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.val_first_machine_total, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1
        self._add_row_separator(layout, row); row += 1
        
        # Total n machines
        self.label_n_machines = self._create_styled_label()
        self.val_n_machines_total = self._create_styled_label(object_name="important")
        layout.addWidget(self.label_n_machines, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.val_n_machines_total, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1
        self._add_row_separator(layout, row); row += 1
        
        # REX - Coefficient
        rex_coeff_label = self._create_styled_label(text="Coefficient REX:")
        rex_percent_container, self.edit_rex_percent = self._create_percentage_input("100")
        self.edit_rex_percent.editingFinished.connect(self._on_rex_percent_text_changed)
        layout.addWidget(rex_coeff_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(rex_percent_container, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1

        # REX - Heures (optionnel, remplace le coeff si renseigné)
        rex_hours_label = self._create_styled_label(text="Heures REX (optionnel) :")
        self.edit_rex_hours = QLineEdit()
        self.edit_rex_hours.setValidator(float_validator)
        self.edit_rex_hours.editingFinished.connect(self._on_rex_hours_text_changed)
        layout.addWidget(rex_hours_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.edit_rex_hours, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1

        self._add_row_separator(layout, row); row += 1
        
        # Total avec REX
        total_with_rex_label = self._create_styled_label(text="Total final:", object_name="veryImportant")
        self.total_with_rex_val = self._create_styled_label(object_name="veryImportant")
        layout.addWidget(total_with_rex_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.total_with_rex_val, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        row += 1

        self._add_row_separator(layout, row); row += 1

        # Délai étude (mois)
        delai_label = self._create_styled_label(text="Délai étude (mois):", object_name="important")
        delai_value_layout = QHBoxLayout()
        self.val_delai_etude = self._create_styled_label(object_name="important")
        self.btn_delai_settings = QToolButton()
        self.btn_delai_settings.setObjectName("gearButton")
        self.btn_delai_settings.setText("\u2699")
        self.btn_delai_settings.setFixedSize(24, 24)
        self.btn_delai_settings.setToolTip("Paramètres du délai d'étude")
        self.btn_delai_settings.clicked.connect(self.delai_settings_clicked.emit)
        delai_value_layout.addWidget(self.val_delai_etude)
        delai_value_layout.addWidget(self.btn_delai_settings)
        layout.addWidget(delai_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(delai_value_layout, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        return frame
    
    def _on_divers_text_changed(self):
        """Gère le changement de texte dans le champ divers."""
        try:
            text = self.edit_divers.text()
            value = float(text) if text else 0.0
            self.divers_changed.emit(value)
        except ValueError:
            pass
    
    def _on_rex_percent_text_changed(self):
        """Gère le changement de texte dans le champ REX %."""
        text = self.edit_rex_percent.text()
        value = float(text) if text else 100
        self.rex_coeff_changed.emit(value / 100)
    
    def _on_rex_hours_text_changed(self):
        text = self.edit_rex_hours.text().strip()
        if not text:
            self.rex_hours_cleared.emit()
        else:
            try:
                self.rex_hours_changed.emit(float(text))
            except ValueError:
                pass

    def update_totals(self, first_machine_subtotal: float, first_machine_total: float, quantity: int, n_machines_total: float, total_with_rex: float, delai_etude: float = 0.0):
        """Met à jour l'affichage des totaux."""
        self.val_first_machine_subtotal.setText(f"{first_machine_subtotal:.2f} h")
        self.val_first_machine_total.setText(f"{first_machine_total:.2f} h")
        self.label_n_machines.setText(f"Total {quantity} machines:")
        self.val_n_machines_total.setText(f"{n_machines_total:.2f} h")
        self.total_with_rex_val.setText(f"{total_with_rex:.2f} h")
        self.val_delai_etude.setText(f"{delai_etude:.1f}")

    def sync_rex_fields(self, coeff_pct: float, rex_hours: float):
        """Synchronise les deux champs REX sans déclencher de signaux."""
        self.edit_rex_percent.setText(f"{coeff_pct:.1f}")
        self.edit_rex_hours.setText(f"{rex_hours:.2f}")


class DelaiEtudeDialog(QDialog):
    """Popup de configuration des paramètres de délai d'étude."""

    def __init__(self, app_data, secteur: str, results: Dict[str, float], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres délai d'étude")
        self.setMinimumWidth(420)
        self.app_data = app_data
        self.secteur = secteur

        layout = QVBoxLayout(self)

        # --- Section paramètres d'entrée ---
        params_group = QGroupBox("Paramètres d'entrée")
        params_layout = QFormLayout(params_group)

        self.edit_productivite = QLineEdit(f"{app_data.taux_productivite * 100:.1f}")
        self.edit_productivite.setValidator(float_validator)
        params_layout.addRow("Taux de productivité (%):", self.edit_productivite)

        self.edit_conges = QLineEdit(f"{app_data.pct_conges * 100:.1f}")
        self.edit_conges.setValidator(float_validator)
        params_layout.addRow("% Congés:", self.edit_conges)

        self.edit_demarrage = QLineEdit(f"{app_data.demarrage_mois:.2f}")
        self.edit_demarrage.setValidator(float_validator)
        params_layout.addRow("Démarrage (mois):", self.edit_demarrage)

        layout.addWidget(params_group)

        # --- Section n_projeteurs par secteur ---
        proj_group = QGroupBox("Nombre de projeteurs par secteur")
        proj_layout = QFormLayout(proj_group)

        secteur_labels = {code: label for sectors in app_data.secteurs.values() for code, label in sectors.items()}
        self.edits_n_projeteurs: Dict[str, QLineEdit] = {}
        for code, value in app_data.n_projeteurs.items():
            edit = QLineEdit(f"{value}")
            edit.setValidator(float_validator)
            label_text = secteur_labels.get(code, code)
            if code == secteur:
                label_text += "  ◄"
            proj_layout.addRow(f"{label_text}:", edit)
            self.edits_n_projeteurs[code] = edit

        layout.addWidget(proj_group)

        # --- Section résultats intermédiaires (lecture seule) ---
        results_group = QGroupBox("Résultats intermédiaires")
        results_layout = QFormLayout(results_group)

        fields = [
            ("Heures prises en compte:", f"{results.get('heures_proj', 0):.0f} h"),
            ("Nombre de projeteurs:", f"{results.get('n_projeteurs', 0):.1f}"),
            ("Délai brut (mois):", f"{results.get('delai_brut', 0):.1f}"),
            ("Délai étude productif (mois):", f"{results.get('delai_productif', 0):.1f}"),
            ("Congés (mois):", f"{results.get('conges_mois', 0):.1f}"),
        ]
        for label_text, value_text in fields:
            val_label = QLabel(value_text)
            val_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            results_layout.addRow(label_text, val_label)

        # Résultat final mis en valeur
        delai_reel_label = QLabel(f"{results.get('delai_reel', 0):.1f} mois")
        delai_reel_label.setObjectName("veryImportant")
        delai_reel_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        results_layout.addRow("Délai réel étude:", delai_reel_label)

        layout.addWidget(results_group)

        # --- Boutons ---
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> Dict:
        """Retourne les valeurs saisies par l'utilisateur."""
        n_proj = {}
        for code, edit in self.edits_n_projeteurs.items():
            try:
                n_proj[code] = float(edit.text()) if edit.text() else self.app_data.n_projeteurs[code]
            except ValueError:
                n_proj[code] = self.app_data.n_projeteurs[code]

        try:
            taux = float(self.edit_productivite.text()) / 100 if self.edit_productivite.text() else self.app_data.taux_productivite
        except ValueError:
            taux = self.app_data.taux_productivite

        try:
            conges = float(self.edit_conges.text()) / 100 if self.edit_conges.text() else self.app_data.pct_conges
        except ValueError:
            conges = self.app_data.pct_conges

        try:
            demarrage = float(self.edit_demarrage.text()) if self.edit_demarrage.text() else self.app_data.demarrage_mois
        except ValueError:
            demarrage = self.app_data.demarrage_mois

        return {
            "taux_productivite": taux,
            "pct_conges": conges,
            "demarrage_mois": demarrage,
            "n_projeteurs": n_proj,
        }


class TabSummaryController:
    """Contrôleur pour l'onglet récapitulatif."""
    
    def __init__(self, model: Model, view: TabSummary):
        self.model = model
        self.view = view

        # Connecter les signaux du model
        self.model.project_changed.connect(self._on_project_changed)
        self.model.data_updated.connect(self._on_data_updated)
        
        # Connecter les signaux de la vue
        self.view.divers_changed.connect(self._on_divers_changed)
        self.view.rex_coeff_changed.connect(self._on_rex_coeff_changed)
        self.view.rex_hours_changed.connect(self._on_rex_hours_changed)
        self.view.rex_hours_cleared.connect(self._on_rex_hours_cleared)
        self.view.delai_settings_clicked.connect(self._on_delai_settings_clicked)

    def _rebuild_tree(self):
        """Reconstruit l'arbre récapitulatif avec le coefficient REX courant."""
        project = self.model.project
        tree_items = project.generate_summary_tree()
        self.view.tree.build_tree(tree_items, project.context(), rex_coeff=project.manual_rex_coeff)

    def _on_project_changed(self):
        """Appelé quand le projet change - reconstruit l'arbre."""
        self._rebuild_tree()
        
        # Synchroniser le champ divers
        self.view.edit_divers.setText(f"{self.model.project.divers_percent * 100:.1f}")
        # Vider le champ heures REX (manual_rex_hours = None après apply_defaults)
        self.view.edit_rex_hours.setText("")
        
        # Mettre à jour les totaux (sync_rex_fields appellé en interne)
        self._update_totals()
    
    def _on_data_updated(self):
        """Appelé lors de modifications mineures (valeurs, checkboxes) - met à jour l'arbre."""
        self._rebuild_tree()
        self._update_totals()

    def _update_totals(self):
        """Recalcule et affiche tous les totaux."""
        project: Project = self.model.project

        first_machine_subtotal = project.compute_first_machine_subtotal()
        first_machine_total = project.compute_first_machine_total()
        n_machines_total = project.compute_n_machines_total()
        total_with_rex = project.calculate_total_with_rex()

        # Délai d'étude
        self._delai_results = project.compute_delai_etude()
        delai_etude = self._delai_results.get("delai_reel", 0.0)
        
        # Mettre à jour l'affichage
        self.view.update_totals(
            first_machine_subtotal=first_machine_subtotal,
            first_machine_total=first_machine_total,
            quantity=project.quantity,
            n_machines_total=n_machines_total,
            total_with_rex=total_with_rex,
            delai_etude=delai_etude,
        )

        # Synchroniser les deux champs REX (toujours liés : coeff = heures / n_machines)
        if n_machines_total != 0:
            if project.manual_rex_hours is not None:
                # Heures saisies manuellement → dériver le coeff
                coeff_pct = project.manual_rex_hours / n_machines_total * 100
                self.view.sync_rex_fields(coeff_pct, project.manual_rex_hours)
            else:
                # Coeff utilisé → dériver les heures affichées
                rex_hours = project.manual_rex_coeff * n_machines_total
                self.view.sync_rex_fields(project.manual_rex_coeff * 100, rex_hours)

    def _on_divers_changed(self, percent: float):
        """Appelé quand le pourcentage divers change."""
        self.model.project.divers_percent = percent / 100
        self._update_totals()
        # Pas besoin d'émettre data_updated car c'est juste un changement de total

    def _on_rex_coeff_changed(self, coeff: float):
        """Appelé quand le coefficient REX change — efface les heures manuelles."""
        self.model.project.manual_rex_coeff = coeff
        self.model.project.manual_rex_hours = None  # Le coeff devient maître
        self._rebuild_tree()
        self._update_totals()

    def _on_rex_hours_changed(self, hours: float):
        """Appelé quand des heures REX sont saisies — dérive et stocke le coeff équivalent."""
        self.model.project.manual_rex_hours = hours
        n_machines = self.model.project.n_machines_total or 0
        if n_machines != 0:
            self.model.project.manual_rex_coeff = hours / n_machines
        self._rebuild_tree()
        self._update_totals()

    def _on_rex_hours_cleared(self):
        """Appelé quand le champ heures REX est vidé — revient au calcul par coeff."""
        self.model.project.manual_rex_hours = None
        self._rebuild_tree()
        self._update_totals()

    def _on_delai_settings_clicked(self):
        """Ouvre la popup de paramétrage du délai d'étude."""
        project = self.model.project
        results = getattr(self, '_delai_results', project.compute_delai_etude())

        dialog = DelaiEtudeDialog(project.app_data, project.secteur, results, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            app_data = project.app_data
            app_data.taux_productivite = values["taux_productivite"]
            app_data.pct_conges = values["pct_conges"]
            app_data.demarrage_mois = values["demarrage_mois"]
            app_data.n_projeteurs = values["n_projeteurs"]
            app_data.save_delai_params()
            self._update_totals()