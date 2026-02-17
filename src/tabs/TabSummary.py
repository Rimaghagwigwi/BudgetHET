from typing import Any, Dict, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QTreeWidget, QTreeWidgetItem,
                             QHBoxLayout, QGridLayout, QLineEdit)
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
        self.setColumnWidth(0, 500)
        # Style amélioré pour lisibilité
        self.setStyleSheet("""
            QTreeWidget {
                font-size: 11pt;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 2px;
                min-height: 20px;
            }
        """)

    def build_tree(self, items: Dict[str, Any], context: Dict[str, Any]):
        """Construit l'arbre à partir d'un dictionnaire de données."""
        self.clear()
        
        for label, value in items.items():
            self._add_node(label, value, None, context)
        
        self.expandAll()

    def _add_node(self, label: str, value: Any, parent: QTreeWidgetItem | None, context: Dict[str, Any]):
        """Ajoute récursivement un nœud à l'arbre."""
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
        """Ajoute un nœud de tâche et retourne ses heures effectives."""
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

    def _create_styled_label(self, text: str = "0.00 h", size: int = 11, bold: bool = True, color: str = "") -> QLabel:
        """Crée un label avec style aligné à droite."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        label.setFont(QFont("Arial", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
        if color:
            label.setStyleSheet(f"color: {color};")
        return label
    
    def _create_percentage_input(self, placeholder: str) -> Tuple[QHBoxLayout, QLineEdit]:
        container = QHBoxLayout()
        edit_percent = QLineEdit()
        # Limiteur pour n'accepter que les nombres
        edit_percent.setValidator(float_validator)
        edit_percent.setPlaceholderText(placeholder)
        edit_percent.setStyleSheet("color: #2c3e50; font-size: 11pt;")
        edit_percent.setAlignment(Qt.AlignmentFlag.AlignRight)
        container.addWidget(edit_percent)
        container.addWidget(QLabel("%"))
        return container, edit_percent
    
    def _create_totals_section(self) -> QFrame:
        """Crée la section des totaux en bas de l'onglet."""
        frame = QFrame()
        frame.setStyleSheet("background-color: #f9f9f9; border-top: 2px solid #bdc3c7;")
        layout = QGridLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        row = 0
        
        # Total 1ère machine
        label_first_machine = self._create_styled_label(text = "Total 1ère machine:", size=12, color="#2c3e50")
        self.val_first_machine = self._create_styled_label(size=12, color="#2c3e50")
        layout.addWidget(label_first_machine, row, 0)
        layout.addWidget(self.val_first_machine, row, 1)
        row += 1
        
        # Total n machines
        self.label_n_machines = self._create_styled_label(size=12, color="#2c3e50")
        self.val_n_machines = self._create_styled_label(size=12, color="#2c3e50")
        layout.addWidget(self.label_n_machines, row, 0)
        layout.addWidget(self.val_n_machines, row, 1)
        row += 1
        
        # Divers (%)
        divers_label = self._create_styled_label(text="Divers:", size=12, color="#2c3e50")
        divers_container, self.edit_divers = self._create_percentage_input("0.0")
        self.edit_divers.editingFinished.connect(self._on_divers_text_changed)
        layout.addWidget(divers_label, row, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(divers_container, row, 1, Qt.AlignmentFlag.AlignTop)
        row += 1
        
        # Total
        total_label = self._create_styled_label(text="Total:", size=12, color="#2c3e50")
        self.val_total = self._create_styled_label(size=12, color="#2c3e50")
        layout.addWidget(total_label, row, 0)
        layout.addWidget(self.val_total, row, 1)
        row += 1
        
        # REX - Coefficient
        rex_coeff_label = self._create_styled_label(text="Coefficient REX:", size=12, color="#2c3e50")
        rex_percent_container, self.edit_rex_percent = self._create_percentage_input("100")
        self.edit_rex_percent.editingFinished.connect(self._on_rex_percent_text_changed)
        layout.addWidget(rex_coeff_label, row, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(rex_percent_container, row, 1, Qt.AlignmentFlag.AlignTop)
        row += 1
        
        # Total avec REX
        total_with_rex_label = self._create_styled_label(text="Total final:", size=14, color="#e74c3c")
        self.total_with_rex_val = self._create_styled_label(size=14, color="#e74c3c")
        layout.addWidget(total_with_rex_label, row, 0)
        layout.addWidget(self.total_with_rex_val, row, 1)
        
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

    def update_totals(self, first_machine: float, quantity: int, n_machines: float, total: float, total_with_rex: float):
        """Met à jour l'affichage des totaux."""
        self.val_first_machine.setText(f"{first_machine:.2f} h")
        self.label_n_machines.setText(f"Total {quantity} machines:")
        self.val_n_machines.setText(f"{n_machines:.2f} h")
        self.val_total.setText(f"{total:.2f} h")
        self.total_with_rex_val.setText(f"{total_with_rex:.2f} h")

class TabSummaryController:
    """Contrôleur pour l'onglet récapitulatif."""
    
    def __init__(self, model: Model, view: TabSummary):
        self.model = model
        self.view = view

        # Connecter les signaux du model
        self.model.project_changed.connect(self._on_project_changed)
        
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

    def _update_totals(self):
        """Recalcule et affiche tous les totaux."""
        project: Project = self.model.project
        
        # Calculer le sous-total de base
        first_machine = project.compute_total_firstmachine()
        
        # Calculer le total pour n machines
        n_machines = project.compute_n_machines_total()
        
        # Calculer le total avec divers
        total_with_divers = project.compute_total_with_divers()
        
        # Calculer le total avec REX
        total_with_rex = project.calculate_total_hours()
        
        # Mettre à jour l'affichage
        self.view.update_totals(
            first_machine=first_machine,
            quantity=project.quantity,
            n_machines=n_machines,
            total=total_with_divers,
            total_with_rex=total_with_rex
        )

    def _on_divers_changed(self, percent: float):
        """Appelé quand le pourcentage divers change."""
        self.model.project.divers_percent = percent / 100
        self._update_totals()

    def _on_rex_coeff_changed(self, coeff: float):
        """Appelé quand le coefficient REX change."""
        self.model.project.manual_rex_coeff = coeff
        self._update_totals()