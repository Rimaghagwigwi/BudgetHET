from typing import List, Optional
from src.model import Model
from src.utils.TabTasks import TabTasks, TaskTableWidget
from src.utils.Task import AbstractTask


class BaseTaskTabController:
    """Contrôleur de base pour les onglets de tâches.

    Fournit la gestion commune des signaux (modification manuelle, checkbox)
    et la mise à jour des totaux. Les sous-classes doivent implémenter
    _build_tables() et _get_all_tasks().
    """

    def __init__(self, model: Model, view: TabTasks):
        self.model = model
        self.view = view
        self.tables: List[TaskTableWidget] = []
        self.model.project_changed.connect(self._on_project_changed)

    def _get_all_tasks(self) -> List[AbstractTask]:
        """Retourne la liste plate de toutes les tâches gérées par ce contrôleur."""
        raise NotImplementedError

    def _build_tables(self) -> List[TaskTableWidget]:
        """Construit et retourne les tables à afficher."""
        raise NotImplementedError

    def _connect_table(self, table: TaskTableWidget):
        """Connecte les signaux communs à une table."""
        table.manual_value_modified.connect(self._on_manual_change)
        table.checkbox_toggled.connect(self._on_checkbox_toggle)

    def _on_project_changed(self):
        """Reconstruit les tables quand le projet change."""
        self.tables = self._build_tables()
        self.view.display_tables(self.tables)

    def _update_all_tables(self):
        """Met à jour le contexte, les heures par défaut et les totaux de toutes les tables."""
        context = self.model.project.context()
        for table in self.tables:
            table.context = context
            table.update_table()

    def _find_task_by_ref(self, ref: int) -> Optional[AbstractTask]:
        """Recherche une tâche par son index/ref."""
        for task in self._get_all_tasks():
            if task.index == ref:
                return task
        return None

    def _on_manual_change(self, text: str, ref: int):
        """Gère la modification manuelle d'une valeur d'heures."""
        try:
            manual_value = float(text) if text else None
        except ValueError:
            manual_value = None

        task = self._find_task_by_ref(ref)
        if task:
            task.manual_hours = manual_value
            self._update_all_tables()
            self.model.data_updated.emit()

    def _on_checkbox_toggle(self, checked: bool, ref: int):
        """Gère le changement d'état d'une checkbox."""
        task = self._find_task_by_ref(ref)
        if task and hasattr(task, 'is_selected'):
            task.is_selected = checked
            self._update_all_tables()
            self.model.data_updated.emit()
