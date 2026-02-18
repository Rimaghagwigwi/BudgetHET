from typing import Dict, List
from src.tabs.BaseTaskTabController import BaseTaskTabController
from src.tabs.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask, Calcul


class CalculsTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet des calculs (obligatoires et optionnels)."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.calculs

    def _build_tables(self) -> List[TaskTableWidget]:
        project = self.model.project
        machine_type = project.machine_type

        # Séparer les calculs obligatoires et optionnels
        mandatory: Dict[str, List[Calcul]] = {}
        optional: Dict[str, List[Calcul]] = {}

        for calc in project.calculs:
            selection = calc.selection.get(machine_type, "Non")
            if selection == "Oui":
                mandatory.setdefault(calc.category, []).append(calc)
            elif selection == "Choix":
                optional.setdefault(calc.category, []).append(calc)

        return [
            self._create_table("Calculs obligatoires", "Calcul", False, mandatory),
            self._create_table("Calculs optionnels", "Calcul", True, optional),
        ]

    def _create_table(self, label: str, task_type: str, is_optional: bool,
                      grouped: Dict[str, List[Calcul]]) -> TaskTableWidget:
        """Crée et remplit une table de calculs groupés par catégorie."""
        table = TaskTableWidget(label=label, task_type=task_type, is_optional=is_optional)
        table.context = self.model.project.context()
        self._connect_table(table)

        for category, calculs in grouped.items():
            table.add_category(category)
            for calc in calculs:
                table.add_task(category, calc)

        table.show_table()
        table.adjust_height_to_content()
        return table