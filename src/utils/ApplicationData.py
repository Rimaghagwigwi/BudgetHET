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

        self.people: List[str] = []
        self.product_types: Dict[str, str] = {} # Dict[code: label] - {"SYNCH": "Synchrone", ...}
        self.product: Dict[str, Dict[str, str]] = {} # Dict[Catégorie: Dict[code: label]] - {"SYNCH": {"ALT_2P": "Alternateur 2p", ...}, ...}
        self.types_affaires: Dict[str, str] = {} # Dict[code: label] - {"REMPLACEMENT": "Remplacement lieu et place", ...}
        self.das: Dict[str, str] = {} # Dict[code: label] - {"MS": "Machines spéciales", ...}
        self.secteurs: Dict[str, Dict[str, str]] = {} # Dict[DAS: Dict[code: label]] - {"MS": {"INDUS": "Industrie", ...}, ...}
        self.jobs: Dict[str, str] = {} # Dict[code: label] - {"ADM_COA": "Admin CAO", ...}

        self.tasks: Dict[str, Dict[str, List[GeneralTask]]] = {} # Dict[category: Dict[sub-category: List[GeneralTask]]]

        self.lpdc_docs: List[LPDCDocument] = []
        self.lpdc_categories: Dict[str, str] = {} # Dict[code: label] - {"BASE": "PDC de base", ...}
        self.lpdc_coeff_secteur: Dict[str, float] = {} # Dict[secteur: coeff]
        self.lpdc_coeff_affaire: Dict[str, float] = {} # Dict[affaire: coeff]
        self.lpdc_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]

        self.calculs: List[Calcul] = []
        self.calcul_categories: Dict[str, str] = {} # Dict[code: label]
        self.calcul_secteur_coeff: Dict[str, Dict[str, float]] = {} # Dict[type_affaire: Dict[activité: coeff]]
        self.calcul_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]

        self.options: List[Option] = []
        self.option_categories: Dict[str, str] = {} # Dict[code: label]
        self.option_category_coeff: Dict[str, Dict[str, float]] = {} # Dict[type_affaire: Dict[category: coeff]]
        self.option_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]
        
        self.labo: List[Labo] = []
        self.labo_categories: Dict[str, str] = {} # Dict[code: label]
        self.labo_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]

    def load_config(self, config_path):
        tree = ET.parse(config_path)
        root = tree.getroot()
        
        # Paths
        self.paths = {}
        for path_elem in root.findall("./datapaths/path"):
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

        # Dossier projets
        self.asset_dir = root.findtext("./asset-dir", "assets/")

        # Stylesheet
        stylesheet_path = root.findtext("./ui/stylesheet", "")
        self.stylesheet = ""
        if stylesheet_path:
            try:
                with open(stylesheet_path, 'r', encoding='utf-8') as f:
                    self.stylesheet = f.read()
            except (FileNotFoundError, IOError):
                pass

    def sort_raw_data(self):
        """Trie les données brutes des json en listes d'objets. La logique de conversion est differente pour chaque type de données."""
        # 1. Données générales
        base_data = self.raw_data.get("base_data", {})

        self.people: List[str] = base_data.get("people", [])
        self.product_types: Dict[str, str] = base_data.get("product_types", {})
        self.product: Dict[str, Dict[str, str]] = base_data.get("products", {})
        self.types_affaires: Dict[str, str] = base_data.get("types_affaire", {})
        self.das: Dict[str, str] = base_data.get("DAS", {})
        self.secteurs: Dict[str, Dict[str, str]] = base_data.get("sectors", {})

        self.jobs.clear()
        base_jobs: Dict[str, str] = base_data.get("jobs", {})
        suffixes: Dict[str, str] = base_data.get("job_suffixes", {})
        for suffix_code, suffix_label in suffixes.items():
            for job_code, job_label in base_jobs.items():
                full_code = f"{job_code}_{suffix_code}"
                full_label = f"{job_label} {suffix_label}"
                self.jobs[full_code] = full_label

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
                    ortems_repartition = task_data.get("ortems_repartition", {})
                    
                    general_task = GeneralTask(
                        index=index,
                        label=label,
                        base_hours_machine=base_hours_machine,
                        coeff_type_affaire=coeff_type_affaire,
                        coeff_secteur=coeff_secteur,
                        mutiplicative=is_multiplicative,
                        ortems_repartition=ortems_repartition
                    )
                    self.tasks[category][sub_category].append(general_task)
                    index += 1
        # 3. LPDC
        self.lpdc_coeff_secteur = self.raw_data["LPDC"]["coeff_secteur"]
        self.lpdc_coeff_affaire = self.raw_data["LPDC"]["coeff_affaire"]
        self.lpdc_categories = self.raw_data["LPDC"]["categories"]
        self.lpdc_ortems = self.raw_data["LPDC"].get("ortems_repartition", {}) # Dict[category: Dict[code: coeff]]

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
        self.calcul_ortems = self.raw_data["calculs"].get("ortems_repartition", {}) # Dict[category: Dict[code: coeff]]

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
        self.option_ortems = self.raw_data["options"].get("ortems_repartition", {}) # Dict[category: Dict[code: coeff]]

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
        self.labo_categories: Dict[str, str] = self.raw_data["labo"]["categories"] # Dict[code: label]
        self.labo_ortems = self.raw_data["labo"].get("ortems_repartition", {}) # Dict[category: Dict[code: coeff]]

        labo_list: List[dict] = self.raw_data['labo']["labo"]
        for item in labo_list:
            labo_task = Labo(
                index=item.get("index", 0),
                label=item.get("label", ""),
                hours=item.get("hours", 0.0),
                category=item.get("category", "")
            )
            self.labo.append(labo_task)