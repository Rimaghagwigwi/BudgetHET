import json
import yaml
from typing import Dict, List, Optional, Any
from src.utils.Task import GeneralTask, LPDCDocument, Option, Calcul, Labo

class ApplicationData:
    def __init__(self, config_path="config.yaml"):
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
        self.n_projeteurs: Dict[str, int] = {} # Dict[secteur: nombre] - {"INDUS": 1, ...}
        self.taux_productivite: float = 0.55
        self.pct_conges: float = 0.17
        self.demarrage_mois: float = 0.5

        self.tasks: Dict[str, Dict[str, List[GeneralTask]]] = {} # Dict[category: Dict[sub-category: List[GeneralTask]]]

        self.calculs: List[Calcul] = []
        self.calcul_categories: Dict[str, str] = {} # Dict[code: label]
        self.calcul_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]
        
        self.labo: List[Labo] = []
        self.labo_categories: Dict[str, str] = {} # Dict[code: label]
        self.labo_coeff_affaire: Dict[str, float] = {} # Dict[affaire: coeff]
        self.labo_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]

        self.options: List[Option] = []
        self.option_categories: Dict[str, str] = {} # Dict[code: label]
        self.option_coeff_affaire: Dict[str, Dict[str, float]] = {} # Dict[type_affaire: Dict[category: coeff]]
        self.option_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]

        self.lpdc_docs: List[LPDCDocument] = []
        self.lpdc_categories: Dict[str, str] = {} # Dict[code: label] - {"BASE": "PDC de base", ...}
        self.lpdc_coeff_secteur: Dict[str, float] = {} # Dict[secteur: coeff]
        self.lpdc_coeff_affaire: Dict[str, float] = {} # Dict[affaire: coeff]
        self.lpdc_ortems: Dict[str, Dict[str, float]] = {} # Dict[category: Dict[code: coeff]]

    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Paths
        self.paths = config.get("datapaths", {})

        # UI
        ui = config.get("ui", {})
        self.ui_theme = ui.get("theme", "Fusion")
        window = ui.get("window", {})
        self.window_title = window.get("title", "Chiffrage HET")
        try:
            self.window_width = int(window.get("width", 1080))
            self.window_height = int(window.get("height", 720))
        except (ValueError, TypeError):
            self.window_width = 1080
            self.window_height = 720

        # Dossier projets
        self.asset_dir = config.get("asset-dir")
        self.project_save_dir = config.get("project-save-dir")
        self.ortems_template_path = config.get("ortems-template-path")
        self.excel_report_template_path = config.get("excel-report-template-path")
        self.rex_database_path = config.get("rex-database-path")
        self.quick_export_path = config.get("quick-export-path")

        # Stylesheet
        stylesheet_path = ui.get("stylesheet", "")
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
        self.n_projeteurs = base_data.get("n_projeteurs", {})

        delai_params = base_data.get("delai_etude_params", {})
        self.taux_productivite = delai_params.get("taux_productivite", 0.55)
        self.pct_conges = delai_params.get("pct_conges", 0.17)
        self.demarrage_mois = delai_params.get("demarrage_mois", 0.5)

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
                        multiplicative=is_multiplicative,
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
        self.calcul_coeff_affaire = self.raw_data["calculs"]["coeff_type_affaire"]
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
        self.option_coeff_affaire: Dict[str, Dict[str, float]] = self.raw_data["options"]["category_coeff"]
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
        self.labo_coeff_affaire = self.raw_data["labo"]["coeff_affaire"] # Dict[affaire: coeff]
        self.labo_ortems = self.raw_data["labo"].get("ortems_repartition", {}) # Dict[category: Dict[code: coeff]]

        labo_list: List[dict] = self.raw_data['labo']["labo"]
        for item in labo_list:
            labo_task = Labo(
                index=item.get("index", 0),
                label=item.get("label", ""),
                hours=item.get("hours", 0.0),
                category=item.get("category", ""),
                coeff_secteur=item.get("coeff_secteur", {})
            )
            self.labo.append(labo_task)

    def save_delai_params(self):
        """Persiste les paramètres de délai d'étude et n_projeteurs dans base_data.json."""
        path = self.paths.get("base_data")
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data["n_projeteurs"] = self.n_projeteurs
        data["delai_etude_params"] = {
            "taux_productivite": self.taux_productivite,
            "pct_conges": self.pct_conges,
            "demarrage_mois": self.demarrage_mois,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)