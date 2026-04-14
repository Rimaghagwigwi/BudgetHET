from typing import List
from src.utils.BaseTaskTabController import BaseTaskTabController
from src.utils.TabTasks import TaskTableWidget
from src.utils.Task import LPDCDocument


class LPDCTabController(BaseTaskTabController):
    """Contrôleur pour l'onglet LPDC."""

    def _build_tables(self) -> List[TaskTableWidget]:
        grouped = self.model.project.grouped_lpdc()
        base_docs: List[LPDCDocument] = grouped["BASE"]
        part_docs: List[LPDCDocument] = grouped["PART"]

        table = TaskTableWidget(label="Documents LPDC", task_type="Document")
        table.context = self.model.project.context()
        self._connect_table(table)

        if base_docs or part_docs:
            table.add_category("Documents")
            for doc in base_docs:
                table.add_task("Documents", doc, mandatory=True)
            for doc in part_docs:
                table.add_task("Documents", doc, mandatory=False)
            table.show_table()
            table.adjust_height_to_content()

        return [table]
    
    def _on_project_changed(self):
        """Reconstruit les tables quand le projet change."""
        self.tables = self._build_tables()
        self.view.display_tables(self.tables)

        secteur_coeff_edit = self.view.add_global_coefficient("Coefficient secteur d'activité", self.model.project.lpdc_coeff_secteur)
        secteur_coeff_edit.editingFinished.connect(lambda: self._on_lpdc_secteur_coefficient_change(float(secteur_coeff_edit.text())))

        affaire_coeff_edit = self.view.add_global_coefficient("Coefficient affaire", self.model.project.lpdc_coeff_affaire)
        affaire_coeff_edit.editingFinished.connect(lambda: self._on_lpdc_affaire_coefficient_change(float(affaire_coeff_edit.text())))
    
    def _on_lpdc_secteur_coefficient_change(self, new_coeff: float):
        """Gère la modification d'un coefficient global (ex: LPDC)."""
        self.model.project.lpdc_coeff_secteur = new_coeff
        self._update_all_tables()
        self.model.data_updated.emit()

    def _on_lpdc_affaire_coefficient_change(self, new_coeff: float):
        """Gère la modification d'un coefficient global (ex: LPDC)."""
        self.model.project.lpdc_coeff_affaire = new_coeff
        self._update_all_tables()
        self.model.data_updated.emit()
