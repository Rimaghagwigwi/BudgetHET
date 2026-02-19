from typing import List
from utils.BaseTaskTabController import BaseTaskTabController
from utils.TabTasks import TaskTableWidget
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
        table.context = self.model.project.context()
        self._connect_table(table)

        if docs:
            table.add_category("Documents")
            for doc in docs:
                table.add_task("Documents", doc)
            table.show_table()
            table.adjust_height_to_content()

        return table
    
    def _on_project_changed(self):
        """Reconstruit les tables quand le projet change."""
        self.tables = self._build_tables()
        self.view.display_tables(self.tables)

        secteur_coeff_edit = self.view.add_global_coefficient("Coefficient secteur d'activité", self.model.project.lpdc_secteur_coeff)
        secteur_coeff_edit.editingFinished.connect(lambda: self._on_lpdc_secteur_coefficient_change(float(secteur_coeff_edit.text())))

        affaire_coeff_edit = self.view.add_global_coefficient("Coefficient affaire", self.model.project.lpdc_affaire_coeff)
        affaire_coeff_edit.editingFinished.connect(lambda: self._on_lpdc_affaire_coefficient_change(float(affaire_coeff_edit.text())))
    
    def _on_lpdc_secteur_coefficient_change(self, new_coeff: float):
        """Gère la modification d'un coefficient global (ex: LPDC)."""
        self.model.project.lpdc_secteur_coeff = new_coeff
        self._update_all_tables()
        self.model.data_updated.emit()

    def _on_lpdc_affaire_coefficient_change(self, new_coeff: float):
        """Gère la modification d'un coefficient global (ex: LPDC)."""
        self.model.project.lpdc_affaire_coeff = new_coeff
        self._update_all_tables()
        self.model.data_updated.emit()
