from typing import List
from src.tabs.BaseTaskTabController import BaseTaskTabController
from src.tabs.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask


class LaboTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet Laboratoire."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.labo

    def _build_tables(self) -> List[TaskTableWidget]:
        table = TaskTableWidget(
            label="Laboratoire", task_type="Tâche de laboratoire", is_optional=False
        )
        self._connect_table(table)

        labo_tasks = self.model.project.labo
        table.context = self.model.project.context()
        if labo_tasks:
            table.add_category("Tâches de laboratoire")
            for task in labo_tasks:
                table.add_task("Tâches de laboratoire", task)
            table.show_table()
            table.adjust_height_to_content()

        return [table]