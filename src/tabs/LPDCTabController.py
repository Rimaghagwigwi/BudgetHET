from typing import List, Dict
from src.model import Model
from src.utils.Task import LPDCDocument
from src.tabs.TabTasks import TabTasks, TaskTableWidget


class LPDCTabController:
    def __init__(self, model: Model, view: TabTasks):
        self.model = model
        self.view = view
        self.mandatory_table: TaskTableWidget = None
        self.optional_table: TaskTableWidget = None
        
        self.model.project_changed.connect(self._on_project_changed)

    def _on_project_changed(self):
        """Reconstruit les tables LPDC quand le projet change."""
        machine_type = self.model.project.machine_type
        secteur = self.model.project.secteur
        app_data = self.model.app_data
        
        # Trouver les clés de produits correspondantes
        relevant_keys = [machine_type]
        for cat, products in app_data.categories_produit.items():
            if machine_type in products:
                relevant_keys.append(cat)
                
        all_lpdc = self.model.project.lpdc_docs
        
        mandatory = []
        optional = []
        
        for doc in all_lpdc:
            # Vérifier si applicable
            is_applicable = any(key in doc.applicable_pour for key in relevant_keys)
            if not is_applicable:
                continue

            # Vérifier si obligatoire ou optionnel
            if secteur in doc.secteur_obligatoire:
                mandatory.append(doc)
            elif doc.option_possible:
                optional.append(doc)

        # Créer les tables
        self.mandatory_table = self._create_table(mandatory, "Documents LPDC obligatoires", is_optional=False)
        self.optional_table = self._create_table(optional, "Documents LPDC optionnels", is_optional=True)
        
        self.view.display_tables([self.mandatory_table, self.optional_table])

    def _create_table(self, docs_list: List[LPDCDocument], label: str, is_optional: bool) -> TaskTableWidget:
        """Crée une table pour une liste de documents LPDC."""
        table = TaskTableWidget(label=label, task_type="Document", is_optional=is_optional)
        table.manual_value_modified.connect(self._on_manual_change)
        table.checkbox_toggled.connect(self._on_checkbox_toggle)
        
        if docs_list:
            table.add_category("Documents")
            for doc in docs_list:
                table.add_task("Documents",
                             ref=doc.index,
                             label=doc.label,
                             default_hours=doc.hours,
                             manual_hours=doc.manual_hours)
            
            table.show_table()
            table.adjust_height_to_content()
        
        return table

    def _on_manual_change(self, text: str, ref: int):
        """Appelé quand l'utilisateur modifie une valeur manuelle."""
        try:
            manual_value = float(text) if text else None
        except ValueError:
            manual_value = None
        
        # Mettre à jour le document correspondant dans le model
        for doc in self.model.project.lpdc_docs:
            if doc.index == ref:
                doc.manual_hours = manual_value
                print(f"Updated LPDC doc {doc.label} (ref {ref}) manual hours to {manual_value}")
                # Mettre à jour les totaux
                if self.mandatory_table:
                    self.mandatory_table.update_totals()
                if self.optional_table:
                    self.optional_table.update_totals()
                return

    def _on_checkbox_toggle(self, checked: bool, ref: int):
        """Appelé quand l'utilisateur coche/décoche un document optionnel."""
        for doc in self.model.project.lpdc_docs:
            if doc.index == ref:
                doc.is_selected = checked
                print(f"LPDC doc {doc.label} (ref {ref}) {'selected' if checked else 'unselected'}")
                # Mettre à jour les totaux
                if self.mandatory_table:
                    self.mandatory_table.update_totals()
                if self.optional_table:
                    self.optional_table.update_totals()
                return