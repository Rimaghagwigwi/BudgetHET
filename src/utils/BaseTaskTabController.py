from typing import List, Optional
from src.model import Model
from src.utils.TabTasks import TabTasks, TaskTableWidget
from src.utils.Task import AbstractTask


class BaseTaskTabController:
    """Contrôleur de base pour les onglets de tâches.

    Fournit la gestion commune des signaux (modification manuelle, checkbox)
    et la mise à jour des totaux. Les sous-classes doivent implémenter _build_tables().
    """

    def __init__(self, model: Model, view: TabTasks):
        self.model = model
        self.view = view
        self.tables: List[TaskTableWidget] = []
        self.model.project_changed.connect(self._on_project_changed)

    def _build_tables(self) -> List[TaskTableWidget]:
        """Construit et retourne les tables à afficher."""
        raise NotImplementedError

    def _connect_table(self, table: TaskTableWidget):
        """Connecte les signaux d'une table avec routage par table (évite les collisions d'index)."""
        table.manual_value_modified.connect(
            lambda text, ref, t=table: self._on_manual_change_in_table(t, text, ref)
        )
        table.checkbox_toggled.connect(
            lambda checked, ref, t=table: self._on_checkbox_toggle_in_table(t, checked, ref)
        )
        table.category_correction_modified.connect(self._on_category_correction)

    @staticmethod
    def _find_task_in_table(table: TaskTableWidget, ref: int) -> Optional[AbstractTask]:
        """Recherche une tâche par son index dans une table spécifique."""
        for task_list in table.categories.values():
            for task, _ in task_list:
                if task.index == ref:
                    return task
        return None

    @staticmethod
    def _correction_key(table: TaskTableWidget, cat_name: str) -> str:
        """Cl\u00e9 unique pour identifier une correction de cat\u00e9gorie dans le projet."""
        table_label = table.label.text() if table.label else ""
        return f"{table_label}/{cat_name}"

    def _restore_category_corrections(self, table: TaskTableWidget):
        """Restaure les corrections de cat\u00e9gorie depuis le projet vers la table."""
        prj_corrections = self.model.project.category_corrections
        for cat_name in table.categories:
            key = self._correction_key(table, cat_name)
            if key in prj_corrections:
                table.category_corrections[cat_name] = prj_corrections[key]

    def _on_project_changed(self):
        """Reconstruit les tables quand le projet change."""
        self.tables = self._build_tables()
        for table in self.tables:
            self._restore_category_corrections(table)
            self._apply_all_category_overrides(table)
            table.refresh()
        self.view.display_tables(self.tables)

    def _update_all_tables(self):
        """Met à jour le contexte, les heures par défaut et les totaux de toutes les tables."""
        context = self.model.project.context()
        for table in self.tables:
            table.context = context
            self._apply_all_category_overrides(table)
            table.update_table()

    def _on_manual_change_in_table(self, table: TaskTableWidget, text: str, ref: int):
        """Gère la modification manuelle d'une valeur d'heures dans une table spécifique."""
        task = self._find_task_in_table(table, ref)
        if not task:
            return
        try:
            target_hours = float(text) if text else None
        except ValueError:
            target_hours = None

        if target_hours is not None:
            coeff = task.context_coefficients(table.context)
            task.manual_base_hours = target_hours / coeff if coeff else None
        else:
            task.manual_base_hours = None
        self._update_all_tables()
        self.model.data_updated.emit()

    def _on_checkbox_toggle_in_table(self, table: TaskTableWidget, checked: bool, ref: int):
        """Gère le changement d'état d'une checkbox dans une table spécifique."""
        task = self._find_task_in_table(table, ref)
        if task and hasattr(task, 'is_selected'):
            task.is_selected = checked
            self._update_all_tables()
            self.model.data_updated.emit()

    def _on_category_correction(self, cat_name: str, text: str):
        """Gère la modification d'une correction de catégorie et la persiste dans le projet."""
        # Identifier quelle table a émis le signal
        sender_table = None
        for table in self.tables:
            if cat_name in table.categories:
                sender_table = table
                break

        if sender_table:
            key = self._correction_key(sender_table, cat_name)
            correction = sender_table.category_corrections.get(cat_name)
            if correction is not None:
                self.model.project.category_corrections[key] = correction
            else:
                self.model.project.category_corrections.pop(key, None)

        # Recalculer les overrides puis rafraîchir les tables
        context = self.model.project.context()
        for table in self.tables:
            table.context = context
            self._apply_all_category_overrides(table)
            table.refresh()
        self.model.data_updated.emit()

    def _apply_all_category_overrides(self, table: TaskTableWidget):
        """Recalcule les overrides de catégorie pour toutes les catégories d'une table."""
        for cat_name, task_list in table.categories.items():
            correction = table.category_corrections.get(cat_name)
            sorted_tasks = table._sorted_tasks(task_list)

            if correction is None:
                for task, _ in sorted_tasks:
                    task.category_override_hours = None
                continue

            # Calculer les heures naturelles (sans corrections manuelles ni override)
            natural = {}
            for task, _ in sorted_tasks:
                saved_manual = task.manual_base_hours
                saved_override = task.category_override_hours
                task.manual_base_hours = None
                task.category_override_hours = None
                natural[task] = task.effective_hours(table.context)
                task.manual_base_hours = saved_manual
                task.category_override_hours = saved_override

            total = sum(natural.values())

            for task, _ in sorted_tasks:
                if total == 0:
                    task.category_override_hours = 0.0
                else:
                    task.category_override_hours = (natural[task] / total) * correction
