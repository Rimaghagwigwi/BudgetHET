from typing import List
from src.tabs.BaseTaskTabController import BaseTaskTabController
from src.tabs.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask


class GeneralTaskTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet des tâches générales."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.get_all_tasks()

    def _build_tables(self) -> List[TaskTableWidget]:
        tables = []
        project = self.model.project

        for category, subcategories in project.tasks.items():
            table = TaskTableWidget(label=category, task_type="Tâche", is_optional=False)
            table.context = project.context()
            self._connect_table(table)

            for subcat_name, tasks in subcategories.items():
                table.add_category(subcat_name)
                for task in tasks:
                    table.add_task(subcat_name, task)

            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        return tables
    
