from typing import List, Dict
from src.model import Model
from src.utils.Task import Option
from src.tabs.TabTasks import TabTasks, TaskTableWidget


class OptionsTabController:
    def __init__(self, model: Model, view: TabTasks):
        self.model = model
        self.view = view
        self.table: TaskTableWidget = None
        
        self.model.project_changed.connect(self._on_project_changed)

    def _on_project_changed(self):
        """Reconstruit la table des options quand le projet change."""
        all_options = self.model.project.options
        
        # Grouper les options par catégorie
        grouped_options = {}
        for opt in all_options:
            if opt.category not in grouped_options:
                grouped_options[opt.category] = []
            grouped_options[opt.category].append(opt)

        # Créer la table
        self.table = TaskTableWidget(label="Options", task_type="Option", is_optional=True)
        self.table.manual_value_modified.connect(self._on_manual_change)
        self.table.checkbox_toggled.connect(self._on_checkbox_toggle)
        
        for category, options in grouped_options.items():
            self.table.add_category(category)
            for opt in options:
                self.table.add_task(category,
                                   ref=opt.index,
                                   label=opt.label,
                                   default_hours=opt.hours,
                                   manual_hours=opt.manual_hours)
        
        self.table.show_table()
        self.table.adjust_height_to_content()
        self.view.display_tables([self.table])

    def _on_manual_change(self, text: str, ref: int):
        """Appelé quand l'utilisateur modifie une valeur manuelle."""
        try:
            manual_value = float(text) if text else None
        except ValueError:
            manual_value = None
        
        # Mettre à jour l'option correspondante dans le model
        for opt in self.model.project.options:
            if opt.index == ref:
                opt.manual_hours = manual_value
                print(f"Updated option {opt.label} (ref {ref}) manual hours to {manual_value}")
                # Mettre à jour les totaux
                if self.table:
                    self.table.update_totals()
                return

    def _on_checkbox_toggle(self, checked: bool, ref: int):
        """Appelé quand l'utilisateur coche/décoche une option."""
        for opt in self.model.project.options:
            if opt.index == ref:
                opt.is_selected = checked
                print(f"Option {opt.label} (ref {ref}) {'selected' if checked else 'unselected'}")
                # Mettre à jour les totaux
                if self.table:
                    self.table.update_totals()
                return