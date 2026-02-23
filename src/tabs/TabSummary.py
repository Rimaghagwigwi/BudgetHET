from typing import Any, Dict, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QTreeWidget, QTreeWidgetItem,
                             QHBoxLayout, QGridLayout, QLineEdit, QPushButton, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFont, QRegularExpressionValidator
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
        #→self.setColumnWidth(0, int(width * 0.7))
        #self.setColumnWidth(1, int(width * 0.3))


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

    def build_tree(self, items: Dict[str, Any], context: Dict[str, Any]):
        """Construit l'arbre à partir d'un dictionnaire de données."""
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
            is_bold = False
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
        """Ajoute un noeud de tâche et retourne ses heures effectives."""
        hours = task.effective_hours(context)
        
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
    export_json_clicked = pyqtSignal()

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
        self.action_export_json = export_menu.addAction("Exporter en JSON")
        self.action_export_json.triggered.connect(self.export_json_clicked.emit)
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
        self._add_row_separator(layout, row); row += 1
        
        # Total avec REX
        total_with_rex_label = self._create_styled_label(text="Total final:", object_name="veryImportant")
        self.total_with_rex_val = self._create_styled_label(object_name="veryImportant")
        layout.addWidget(total_with_rex_label, row, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.total_with_rex_val, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

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
        try:
            text = self.edit_rex_percent.text()
            value = float(text) if text else 0.0
            self.rex_coeff_changed.emit(value / 100)
        except ValueError:
            pass

    def update_totals(self, first_machine_subtotal: float, first_machine_total: float, quantity: int, n_machines_total: float, total_with_rex: float):
        """Met à jour l'affichage des totaux."""
        self.val_first_machine_subtotal.setText(f"{first_machine_subtotal:.2f} h")
        self.val_first_machine_total.setText(f"{first_machine_total:.2f} h")
        self.label_n_machines.setText(f"Total {quantity} machines:")
        self.val_n_machines_total.setText(f"{n_machines_total:.2f} h")
        self.total_with_rex_val.setText(f"{total_with_rex:.2f} h")

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
    
    def _on_project_changed(self):
        """Appelé quand le projet change - reconstruit l'arbre."""
        project = self.model.project
        
        # Construire l'arbre avec les données du projet
        tree_items = project.generate_summary_tree()
        self.view.tree.build_tree(tree_items, project.context())
        
        # Synchroniser les line edit avec le model
        self.view.edit_divers.setText(f"{project.divers_percent * 100:.1f}")
        self.view.edit_rex_percent.setText(f"{project.manual_rex_coeff * 100:.0f}")
        
        # Mettre à jour les totaux
        self._update_totals()
    
    def _on_data_updated(self):
        """Appelé lors de modifications mineures (valeurs, checkboxes) - met à jour l'arbre."""

        project = self.model.project
        
        # Reconstruire l'arbre avec les nouvelles valeurs
        tree_items = project.generate_summary_tree()
        self.view.tree.build_tree(tree_items, project.context())
        
        # Mettre à jour les totaux
        self._update_totals()

    def _update_totals(self):
        """Recalcule et affiche tous les totaux."""
        project: Project = self.model.project

        first_machine_subtotal = project.compute_first_machine_subtotal()
        first_machine_total = project.compute_first_machine_total()
        n_machines_total = project.compute_n_machines_total()
        total_with_rex = project.calculate_total_with_rex()
        
        # Mettre à jour l'affichage
        self.view.update_totals(
            first_machine_subtotal=first_machine_subtotal,
            first_machine_total=first_machine_total,
            quantity=project.quantity,
            n_machines_total=n_machines_total,
            total_with_rex=total_with_rex
        )

    def _on_divers_changed(self, percent: float):
        """Appelé quand le pourcentage divers change."""
        self.model.project.divers_percent = percent / 100
        self._update_totals()
        # Pas besoin d'émettre data_updated car c'est juste un changement de total

    def _on_rex_coeff_changed(self, coeff: float):
        """Appelé quand le coefficient REX change."""
        self.model.project.manual_rex_coeff = coeff
        self._update_totals()
        # Pas besoin d'émettre data_updated car c'est juste un changement de total