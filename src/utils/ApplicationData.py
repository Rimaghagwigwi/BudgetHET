from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from src.utils.Task import GeneralTask, LPDCDocument, Option, Calcul

class ApplicationData:
    def __init__(self, config_path="config.xml"):
        self.load_config(config_path)

        self.raw_data = {}
        for key, path in self.paths.items():
            with open(path, 'r', encoding='utf-8') as f:
                self.raw_data[key] = json.load(f)
        
        self.tasks: Dict[str, Dict[str, List[GeneralTask]]] = {} # Dict[category: Dict[sub-category: List[GeneralTask]]]
        self.lpdc_docs: List[LPDCDocument] = []
        self.calculs: List[Calcul] = []
        self.options: List[Option] = []

    def load_config(self, config_path):
        tree = ET.parse(config_path)
        root = tree.getroot()
        
        # Paths
        self.paths = {}
        for path_elem in root.findall("./paths/path"):
            key = path_elem.get("key")
            path = path_elem.text
            if key and path:
                self.paths[key] = path
                
        # UI
        self.ui_theme = root.findtext("./ui/theme", "Fusion")
        self.window_title = root.findtext("./ui/window/title", "Chiffrage HET")
        try:
            self.window_width = int(root.findtext("./ui/window/width", "1080"))
            self.window_height = int(root.findtext("./ui/window/height", "720"))
        except ValueError:
            self.window_width = 1080
            self.window_height = 720

    def sort_raw_data(self):
        """Trie les données brutes des json en listes d'objets. La logique de conversion est differente pour chaque type de données."""
        # 1. Données générales
        base_data = self.raw_data.get("base_data", {})

        # Types d'affaires disponibles: Neuf, Remplacement, etc
        self.types_affaires: List[str] = base_data.get("types_affaires", [])
        
        # Secteurs disponibles: Dict[Das: List[Secteurs du DAS]]
        self.secteurs: Dict[str, List[str]] = base_data.get("DAS", {})

        # Catégories de produits disponibles: Dict[Catégorie: List[Produits de la catégorie]]
        self.categories_produit: Dict[str, List[str]] = base_data.get("products", {})

        # Personnes disponibles pour réalisation et validation
        self.personnes: List[str] = base_data.get("personnes", [])

        # 2. Tâches générales
        cols = self.raw_data['tasks'].get("columns", {})
        rows = self.raw_data['tasks'].get("rows", {})

        index = 1
        for category, sub_categories in rows.items():
            self.tasks[category] = {}
            for sub_category, task_list in sub_categories.items():
                self.tasks[category][sub_category] = []
                for label, table in task_list.items():
                    base_hours_machine = {}
                    i = 0
                    for machine_type in cols.get("base_produit", []):
                        base_hours_machine[machine_type] = table[i]
                        i += 1
                    coeff_type_affaire = {}
                    for affaire_type in cols.get("Coeffs_type_affaire", []):
                        coeff_type_affaire[affaire_type] = table[i]
                        i += 1
                    coeff_secteur = {}
                    for secteur in cols.get("Coeffs_secteur", []):
                        coeff_secteur[secteur] = table[i]
                        i += 1
                    general_task = GeneralTask(
                        index=index,
                        label=label,
                        base_hours_machine=base_hours_machine,
                        coeff_type_affaire=coeff_type_affaire,
                        coeff_secteur=coeff_secteur
                    )
                    self.tasks[category][sub_category].append(general_task)
                    index += 1
        # 3. LPDC
        docs_source: List[dict] = self.raw_data["LPDC"].get("documents", [])
        
        for doc in docs_source:
            document = LPDCDocument(
                index=doc.get("index", 0),
                label=doc.get("label", ""),
                hours=doc.get("hours", 0.0),
                applicable_pour=doc.get("applicable_pour", []),
                secteur_obligatoire=doc.get("secteur_obligatoire", []),
                option_possible=doc.get("option_possible", False)
            )
            self.lpdc_docs.append(document)
        
        # 4. Calculs
        calc_list: List[dict] = self.raw_data['calculs'].get("calculs", [])
        for calc in calc_list:
            calculation = Calcul(
                index=calc.get("index", 0),
                label=calc.get("label", ""),
                category=calc.get("category", ""),
                hours=calc.get("hours", {}),
                selection=calc.get("selection", {})
            )
            self.calculs.append(calculation)
        
        # 5. Options
        category_list = self.raw_data["options"].get("options", {})
        for cat_name, opts_list in category_list.items():
            for option in opts_list:
                option = Option(
                    index=option.get("index", 0),
                    label=option.get("label", ""),
                    category=cat_name,
                    hours=option.get("hours", 0.0)
                )
                self.options.append(option)