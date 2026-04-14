from typing import List
from src.utils.BaseTaskTabController import BaseTaskTabController
from src.utils.TabTasks import TaskTableWidget


class LaboOptionsTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet Labo et Options."""

    def _build_tables(self) -> List[TaskTableWidget]:
        project = self.model.project
        ctx = project.context()
        tables = []

        # 1. Labo
        grouped_labo = project.grouped_labo_for_table()
        if grouped_labo:
            table = TaskTableWidget(label="Laboratoire", task_type="Labo")
            table.context = ctx
            self._connect_table(table)
            for category, task_pairs in grouped_labo.items():
                cat_label = project.app_data.labo_categories.get(category, category)
                table.add_category(cat_label)
                for task, mandatory in task_pairs:
                    table.add_task(cat_label, task, mandatory=mandatory)
            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        # 2. Options (ordonnées par catégorie, repliées par défaut)
        grouped_options = project.grouped_options()
        if grouped_options:
            table = TaskTableWidget(label="Options", task_type="Option")
            table.context = ctx
            self._connect_table(table)
            for cat_id, options in grouped_options.items():
                cat_label = project.app_data.option_categories.get(cat_id, cat_id)
                table.add_category(cat_label)
                for opt in options:
                    table.add_task(cat_label, opt, mandatory=False)
            table.collapse_all()
            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        return tables
