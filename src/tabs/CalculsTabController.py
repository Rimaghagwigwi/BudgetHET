from typing import List, Dict
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush
from src.model import Model
from src.utils.Task import Calcul

from src.tabs.TabTasks import TabTasks, TaskTableWidget

class CalculsTabController:
    def __init__(self, model: Model, view: TabTasks):
        self.model = model
        self.view = view

        self.mandatory_dict: Dict[str, List[Calcul]] = {}
        self.mandatory_table: TaskTableWidget = TaskTableWidget(label="Calculs obligatoires", task_type="Calcul", is_optional=False)
        self.mandatory_table.manual_value_modified.connect(self._on_manual_change)
        self.mandatory_table.checkbox_toggled.connect(self._on_checkbox_toggle)

        self.optional_dict: Dict[str, List[Calcul]] = {}
        self.optional_table: TaskTableWidget = TaskTableWidget(label="Calculs optionnels", task_type="Calcul", is_optional=True)
        self.optional_table.manual_value_modified.connect(self._on_manual_change)
        self.optional_table.checkbox_toggled.connect(self._on_checkbox_toggle)

        self.model.project_changed.connect(self._on_project_changed)

    def _populate_table(self, table: TaskTableWidget, grouped_calculs: Dict[str, List[Calcul]]):
        for category, calculs in grouped_calculs.items():
            table.add_category(category)
            for calc in calculs:
                default_hours = calc.default_hours(self.model.project.context())
                table.add_task(category, 
                             ref=calc.index, 
                             label=calc.label, 
                             default_hours=default_hours, 
                             manual_hours=calc.manual_hours)
        
        table.show_table()
        table.adjust_height_to_content()

    def _on_project_changed(self):
        machine_type = self.model.project.machine_type
        
        # Grouper les calculs par catégorie
        self.mandatory_dict.clear()
        self.optional_dict.clear()
        
        for calc in self.model.project.calculs:
            if calc.selection.get(machine_type) == "Oui":
                if calc.category not in self.mandatory_dict:
                    self.mandatory_dict[calc.category] = []
                self.mandatory_dict[calc.category].append(calc)
            elif calc.selection.get(machine_type) == "Choix":
                if calc.category not in self.optional_dict:
                    self.optional_dict[calc.category] = []
                self.optional_dict[calc.category].append(calc)
        
        # Reconstruire les tables
        self.mandatory_table.categories.clear()
        self.optional_table.categories.clear()
        self._populate_table(self.mandatory_table, self.mandatory_dict)
        self._populate_table(self.optional_table, self.optional_dict)
        self.view.display_tables([self.mandatory_table, self.optional_table])
        
    def _on_manual_change(self, text, ref):
        try:
            manual_value = float(text) if text else None
        except ValueError:
            manual_value = None
        
        # Mettre à jour la valeur dans le model
        for calc in self.model.project.calculs:
            if calc.index == ref:
                calc.manual_hours = manual_value
                print(f"Manual value changed for {calc.label}: {text}")
                # Mettre à jour les totaux
                self.mandatory_table.update_totals()
                self.optional_table.update_totals()
                return

    def _on_checkbox_toggle(self, state, ref):
        # Mettre à jour l'état dans le model
        for calc in self.model.project.calculs:
            if calc.index == ref:
                calc.is_selected = state
                print(f"Checkbox toggled for {calc.label}: {'Checked' if state else 'Unchecked'}")
                # Mettre à jour les totaux
                self.mandatory_table.update_totals()
                self.optional_table.update_totals()
                return