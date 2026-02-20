from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from src.utils.Task import GeneralTask, LPDCDocument, Option, Calcul, Labo

class ApplicationData:
    def __init__(self, config_path="config.xml"):
        self.load_config(config_path)

        self.raw_data = {}
        for key, path in self.paths.items():
            with open(path, 'r', encoding='utf-8') as f:
                self.raw_data[key] = json.load(f)

        self.lpdc_coeff_secteur: Dict[str, float] = {} # Dict[secteur: coeff]
        self.lpdc_coeff_affaire: Dict[str, float] = {} # Dict[affaire: coeff]

        self.calcul_categories: Dict[str, str] = {} # Dict[code: label]
        self.calcul_secteur_coeff: Dict[str, Dict[str, float]] = {} # Dict[type_affaire: Dict[activité: coeff]]

        self.option_categories: Dict[str, str] = {} # Dict[code: label]
        self.option_category_coeff: Dict[str, Dict[str, float]] = {} # Dict[type_affaire: Dict[category: coeff]]
        
        self.tasks: Dict[str, Dict[str, List[GeneralTask]]] = {} # Dict[category: Dict[sub-category: List[GeneralTask]]]
        self.lpdc_docs: List[LPDCDocument] = []
        self.calculs: List[Calcul] = []
        self.options: List[Option] = []
        self.labo: List[Labo] = []

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

        # Types d'affaires disponibles: Dict[code: label] - ex: {"NEUF": "Neuf", ...}
        self.types_affaires: Dict[str, str] = base_data.get("types_affaire", {})
        
        # DAS disponibles: Dict[code: label] - ex: {"MS": "Machines spéciales", ...}
        self.das: Dict[str, str] = base_data.get("DAS", {})
        
        # Secteurs disponibles: Dict[DAS: Dict[code: label]]
        self.secteurs: Dict[str, Dict[str, str]] = base_data.get("sectors", {})

        # Types de produits: Dict[code: label] - ex: {"SYNCH": "Synchrone", ...}
        self.types_produit: Dict[str, str] = base_data.get("product_types", {})

        # Catégories de produits disponibles: Dict[Catégorie: Dict[code: label]]
        self.categories_produit: Dict[str, Dict[str, str]] = base_data.get("products", {})

        # Personnes disponibles pour réalisation et validation
        self.personnes: List[str] = base_data.get("people", [])

        # 2. Tâches générales
        tasks_data = self.raw_data['tasks'].get("tasks", {})

        index = 1
        for category, sub_categories in tasks_data.items():
            self.tasks[category] = {}
            for sub_category, task_list in sub_categories.items():
                self.tasks[category][sub_category] = []
                for label, task_data in task_list.items():
                    # Nouvelle structure: task_data contient directement base, coeff_type_affaire, coeff_secteur
                    base_hours_machine = task_data.get("base", {})
                    coeff_type_affaire = task_data.get("coeff_type_affaire", {})
                    coeff_secteur = task_data.get("coeff_secteur", {})
                    is_multiplicative = task_data.get("is_multiplicative", False)
                    
                    general_task = GeneralTask(
                        index=index,
                        label=label,
                        base_hours_machine=base_hours_machine,
                        coeff_type_affaire=coeff_type_affaire,
                        coeff_secteur=coeff_secteur,
                        mutiplicative=is_multiplicative
                    )
                    self.tasks[category][sub_category].append(general_task)
                    index += 1
        # 3. LPDC
        self.lpdc_coeff_secteur = self.raw_data["LPDC"]["coeff_secteur"]
        self.lpdc_coeff_affaire = self.raw_data["LPDC"]["coeff_affaire"]

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
        self.calcul_categories: Dict[str, str] = self.raw_data["calculs"]["categories"] # Dict[code: label]
        self.calcul_coeff_type_affaire = self.raw_data["calculs"]["coeff_type_affaire"]

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
        self.option_categories: Dict[str, str] = self.raw_data["options"]["categories"] # Dict[code: label]
        self.option_category_coeff: Dict[str, Dict[str, float]] = self.raw_data["options"]["category_coeff"]
        options_list: Dict[str, List[dict]] = self.raw_data["options"].get("options", {}) # Dict[category: List[Option]]
        for cat_id, opts_list in options_list.items():
            for option in opts_list:
                option = Option(
                    index=option.get("index", 0),
                    label=option.get("label", ""),
                    category=cat_id,
                    hours=option.get("hours", 0.0)
                )
                self.options.append(option)

        # 6. Labo
        labo_list: List[dict] = self.raw_data['labo'].get("labo", [])
        for item in labo_list:
            labo_task = Labo(
                index=item.get("index", 0),
                label=item.get("label", ""),
                hours=item.get("hours", 0.0)
            )
            self.labo.append(labo_task)