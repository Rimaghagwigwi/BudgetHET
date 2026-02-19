from typing import Dict, List
from utils.BaseTaskTabController import BaseTaskTabController
from utils.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask, Option


class OptionsTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet des options."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.options

    def _build_tables(self) -> List[TaskTableWidget]:
        # Grouper les options par catégorie
        grouped: Dict[str, List[Option]] = {}
        
        for opt in self.model.project.options:
            if opt.category not in grouped:
                grouped[opt.category] = []
            grouped[opt.category].append(opt)

        table = TaskTableWidget(label="Options", task_type="Option", is_optional=True)
        table.context = self.model.project.context()
        self._connect_table(table)

        for cat_id, options in grouped.items():
            cat_label = self.model.project.app_data.option_category_list.get(cat_id, cat_id)
            table.add_category(cat_label)
            for opt in options:
                table.add_task(cat_label, opt)

        table.show_table()
        table.adjust_height_to_content()
        return [table]