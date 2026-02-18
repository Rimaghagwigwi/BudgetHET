from typing import Dict, List
from src.tabs.BaseTaskTabController import BaseTaskTabController
from src.tabs.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask, Option


class OptionsTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet des options."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.options

    def _build_tables(self) -> List[TaskTableWidget]:
        # Grouper les options par catégorie
        grouped: Dict[str, List[Option]] = {}
        for opt in self.model.project.options:
            grouped.setdefault(opt.category, []).append(opt)

        table = TaskTableWidget(label="Options", task_type="Option", is_optional=True)
        self._connect_table(table)

        for category, options in grouped.items():
            table.add_category(category)
            for opt in options:
                table.add_task(
                    category,
                    ref=opt.index,
                    label=opt.label,
                    default_hours=opt.hours,
                    manual_hours=opt.manual_hours,
                )

        table.show_table()
        table.adjust_height_to_content()
        return [table]