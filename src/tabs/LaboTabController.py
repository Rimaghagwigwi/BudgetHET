from typing import List
from src.utils.BaseTaskTabController import BaseTaskTabController
from src.utils.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask
from src.utils.Task import Labo
from typing import Dict, List


class LaboTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet Laboratoire."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.labo

    def _build_tables(self) -> List[TaskTableWidget]:
        mandatory_tasks: Dict[str, List[Labo]] = {}
        facultative_tasks: Dict[str, List[Labo]] = {}

        for task in self.model.project.labo:
            if task.is_mandatory(self.model.project.context()):
                mandatory_tasks.setdefault(task.category, []).append(task)
            else:
                facultative_tasks.setdefault(task.category, []).append(task)

        return [
            self._create_table("Laboratoire obligatoire", "Labo", False, mandatory_tasks),
            self._create_table("Laboratoire facultatif", "Labo", True, facultative_tasks),
        ]

    def _create_table(self, label: str, task_type: str, is_optional: bool,
                      grouped: Dict[str, List[Labo]]) -> TaskTableWidget:
        """Crée et remplit une table de calculs groupés par catégorie."""
        table = TaskTableWidget(label=label, task_type=task_type, is_optional=is_optional)
        table.context = self.model.project.context()
        self._connect_table(table)

        for category, calculs in grouped.items():
            cat_label = self.model.project.app_data.calcul_categories.get(category, category)
            table.add_category(cat_label)
            for calc in calculs:
                table.add_task(cat_label, calc)

        table.show_table()
        table.adjust_height_to_content()
        return table