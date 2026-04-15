from typing import List
from src.utils.BaseTaskTabController import BaseTaskTabController
from src.utils.TabTasks import TaskTableWidget


class DefinitionTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet Définition : Enclenchement + Calculs + Plans fab + Suivi."""

    def _build_tables(self) -> List[TaskTableWidget]:
        project = self.model.project
        ctx = project.context()
        tables = []

        # 1. Enclenchement
        encl_tasks = project.tasks.get("Gestion de projet", {}).get("Enclenchement", [])
        if encl_tasks:
            table = TaskTableWidget(label="Enclenchement", task_type="Tâche")
            table.context = ctx
            self._connect_table(table)
            table.add_category("Enclenchement")
            for task in encl_tasks:
                table.add_task("Enclenchement", task, mandatory=True)
            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        # 2. Calculs (ordonnés par catégorie, repliés par défaut)
        grouped_calculs = project.items_by_category(project.calculs, project.app_data.calcul_categories)
        if grouped_calculs:
            table = TaskTableWidget(label="Calculs", task_type="Calcul")
            table.context = ctx
            self._connect_table(table)
            for category, calcs in grouped_calculs.items():
                cat_label = project.app_data.calcul_categories.get(category, category)
                table.add_category(cat_label)
                for calc in calcs:
                    table.add_task(cat_label, calc, mandatory=calc.is_mandatory(ctx))
            table.collapse_all()
            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        # 3. Plans fab / Spec d'Achat / LDN
        LABEL = "Plans / Specs / LDN"
        plans_fab = project.tasks.get(LABEL, {})
        if plans_fab:
            table = TaskTableWidget(label=LABEL, task_type=LABEL)
            table.context = ctx
            self._connect_table(table)
            for subcat, tasks in plans_fab.items():
                table.add_category(subcat)
                for task in tasks:
                    table.add_task(subcat, task, mandatory=True)
            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        # 4. Suivi
        suivi_tasks = project.tasks.get("Gestion de projet", {}).get("Suivi", [])
        if suivi_tasks:
            table = TaskTableWidget(label="Suivi", task_type="Suivi")
            table.context = ctx
            self._connect_table(table)
            table.add_category("Suivi")
            for task in suivi_tasks:
                table.add_task("Suivi", task, mandatory=True)
            table.show_table()
            table.adjust_height_to_content()
            tables.append(table)

        return tables
