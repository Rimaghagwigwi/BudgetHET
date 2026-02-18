from typing import List
from src.tabs.BaseTaskTabController import BaseTaskTabController
from src.tabs.TabTasks import TaskTableWidget
from src.utils.Task import AbstractTask, LPDCDocument


class LPDCTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet LPDC (obligatoires et optionnels)."""

    def _get_all_tasks(self) -> List[AbstractTask]:
        return self.model.project.lpdc_docs

    def _build_tables(self) -> List[TaskTableWidget]:
        project = self.model.project
        machine_type = project.machine_type
        secteur = project.secteur

        mandatory = []
        optional = []

        for doc in project.lpdc_docs:
            if machine_type not in doc.applicable_pour:
                continue
            if secteur in doc.secteur_obligatoire:
                mandatory.append(doc)
            elif doc.option_possible:
                optional.append(doc)

        return [
            self._create_table(mandatory, "Documents LPDC obligatoires", is_optional=False),
            self._create_table(optional, "Documents LPDC optionnels", is_optional=True),
        ]

    def _create_table(self, docs: List[LPDCDocument], label: str,
                      is_optional: bool) -> TaskTableWidget:
        """Crée et remplit une table de documents LPDC."""
        table = TaskTableWidget(label=label, task_type="Document", is_optional=is_optional)
        self._connect_table(table)

        if docs:
            table.add_category("Documents")
            for doc in docs:
                table.add_task(
                    "Documents",
                    ref=doc.index,
                    label=doc.label,
                    default_hours=doc.hours,
                    manual_hours=doc.manual_hours,
                )
            table.show_table()
            table.adjust_height_to_content()

        return table