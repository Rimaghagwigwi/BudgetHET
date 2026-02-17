from src.model import Model, Project
from src.tabs.TabTasks import TabTasks, TaskTableWidget
from src.utils.Task import AbstractTask, GeneralTask
from typing import Dict, List


class GeneralTaskTabController:
    def __init__(self, model: Model, view: TabTasks):
        self.model = model
        self.view = view

        self.categories: List[TaskTableWidget] = []

        self.model.project_changed.connect(self._on_project_changed)

    def _on_project_changed(self):
        self.categories.clear()
        for category, subcategories in self.model.project.tasks.items():
            cat_table = TaskTableWidget(label=category, task_type="Tâche", is_optional=False)
            cat_table.manual_value_modified.connect(self._on_manual_change)
            
            for subcat_name, tasks in subcategories.items():
                cat_table.add_category(subcat_name)
                for task in tasks:
                    cat_table.add_task(subcat_name, 
                                       ref=task.index, 
                                       label=task.label, 
                                       default_hours=self.model.project.get_task_default_hours(task), 
                                       manual_hours=task.manual_hours)
            
            cat_table.show_table()
            cat_table.adjust_height_to_content()  # Important : à appeler avant d'ajouter à la liste
            self.categories.append(cat_table)
        
        self.view.display_tables(self.categories)

    def _on_manual_change(self, text, ref):
        """Appelé quand l'utilisateur modifie une valeur manuelle."""
        try:
            manual_value = float(text) if text else None
        except ValueError:
            manual_value = None
        
        # Mettre à jour la tâche correspondante dans le model
        for _, subcategory in self.model.project.tasks.items():
            for _, tasks in subcategory.items():
                for task in tasks:
                    if task.index == ref:
                        task.manual_hours = manual_value
                        print(f"Updated task {task.label} (ref {ref}) manual hours to {manual_value}")
                        
                        # Mettre à jour les totaux dans toutes les tables
                        for cat_table in self.categories:
                            cat_table.update_totals()
                        return
    
