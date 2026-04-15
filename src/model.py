import copy
from typing import Dict, List, Optional, Any
from src.utils.ApplicationData import ApplicationData
from src.utils.Task import AbstractTask, GeneralTask, LPDCDocument, Labo, Option, Calcul
from src.utils.exports import export_ortems_excel as _export_ortems, export_excel_report as _export_report
from PyQt6.QtCore import QObject, pyqtSignal

class Project:
    def __init__(self, app_data: ApplicationData):
        self.app_data = app_data
        # Données générales
        self.crm_number = ""
        self.client = ""
        self.affaire = ""
        self.das = ""
        self.secteur = ""
        self.machine_type = ""
        self.product = ""
        self.designation = ""
        self.quantity = 1
        self.revision = "A"
        self.date = ""
        self.created_by = ""
        self.validated_by = ""
        self.description = ""

        self.lpdc_coeff_secteur: float = 1.0
        self.lpdc_coeff_affaire: float = 1.0
        self.calcul_coeff: Dict[str, float] = {}
        self.option_coeff: Dict[str, float] = {}
        self.labo_coeff_affaire: float = 1.0
        
        self.divers_percent: float = 0.05
        self.manual_rex_coeff: float = 1.0
        self.manual_rex_hours: Optional[float] = None

        self.first_machine_subtotal: Optional[float] = None
        self.first_machine_total: Optional[float] = None
        self.n_machines_total: Optional[float] = None
        self.total_with_rex: Optional[float] = None

        # Corrections de catégorie : clé = "table_label/category_name" → valeur
        self.category_corrections: Dict[str, float] = {}
        
        self.tasks: Dict[str, Dict[str, List[GeneralTask]]] = {}
        self.lpdc_docs: List[LPDCDocument] = []
        self.options: List[Option] = []
        self.calculs: List[Calcul] = []
        self.labo: List[Labo] = []
    
    def context(self) -> Dict[str, str]:
        return {
            "product": self.product,
            "machine_type": self.machine_type,
            "affaire": self.affaire,
            "secteur": self.secteur,

            "calcul_coeff": self.calcul_coeff,
            "labo_coeff_affaire": self.labo_coeff_affaire,
            "option_coeff": self.option_coeff,
            "lpdc_coeff_secteur": self.lpdc_coeff_secteur,
            "lpdc_coeff_affaire": self.lpdc_coeff_affaire
        }

    def apply_affaire_coefficients(self):
        """Met à jour uniquement les coefficients dépendant du type d'affaire, sans réinitialiser le projet."""
        self.lpdc_coeff_affaire = self.app_data.lpdc_coeff_affaire.get(self.affaire, 1.0)
        self.labo_coeff_affaire = self.app_data.labo_coeff_affaire.get(self.affaire, 1.0)
        self.calcul_coeff = self.app_data.calcul_coeff_affaire.get(self.affaire, {})
        self.option_coeff = self.app_data.option_coeff_affaire.get(self.affaire, {})

    def apply_defaults(self):
        """Applique les valeurs par défaut après avoir choisi le type de machine, le secteur et le type d'affaire."""
        
        ctx = self.context()

        # Récupérer les coefficients dépendant du contexte depuis app_data
        self.lpdc_coeff_secteur = self.app_data.lpdc_coeff_secteur.get(self.secteur, 1.0)
        self.lpdc_coeff_affaire = self.app_data.lpdc_coeff_affaire.get(self.affaire, 1.0)
        self.labo_coeff_affaire = self.app_data.labo_coeff_affaire.get(self.affaire, 1.0)
        self.calcul_coeff = self.app_data.calcul_coeff_affaire.get(self.affaire, {})
        self.option_coeff = self.app_data.option_coeff_affaire.get(self.affaire, {})
        
        self.divers_percent = 0.05
        self.manual_rex_coeff = 1.0
        self.manual_rex_hours = None

        self.first_machine_subtotal = None
        self.first_machine_total = None
        self.n_machines_total = None
        self.total_with_rex = None

        self.category_corrections = {}
        
        self.tasks = copy.deepcopy(self.app_data.tasks)
        self.lpdc_docs = copy.deepcopy([doc for doc in self.app_data.lpdc_docs if doc.is_active(ctx) or doc.option_possible])
        self.options = copy.deepcopy(self.app_data.options)
        self.calculs = copy.deepcopy([calc for calc in self.app_data.calculs if calc.is_available_as_option(ctx) or calc.is_mandatory(ctx)])
        self.labo = copy.deepcopy(self.app_data.labo)
    
    def get_task_default_hours(self, task: GeneralTask) -> float:
        return task.default_hours(self.context())

    def get_all_tasks(self) -> List[GeneralTask]:
        """Retourne la liste plate de toutes les tâches générales."""
        return [task for subcats in self.tasks.values() for tasks in subcats.values() for task in tasks]
    
    def items_by_category(self, items, categories) -> Dict[str, list]:
        """Regroupe des items (attribut .category) ordonnés selon categories."""
        grouped: Dict[str, list] = {}
        for item in items:
            grouped.setdefault(item.category, []).append(item)
        ordered: Dict[str, list] = {}
        for cat in categories:
            if cat in grouped:
                ordered[cat] = grouped[cat]
        for cat in grouped:
            if cat not in ordered:
                ordered[cat] = grouped[cat]
        return ordered

    def grouped_lpdc(self) -> Dict[str, List[LPDCDocument]]:
        """Retourne les documents LPDC regroupés en 'BASE' et 'PART'."""
        result: Dict[str, List[LPDCDocument]] = {"BASE": [], "PART": []}
        for doc in self.lpdc_docs:
            if self.machine_type not in doc.applicable_pour:
                continue
            if self.secteur in doc.secteur_obligatoire:
                result["BASE"].append(doc)
            elif doc.option_possible:
                result["PART"].append(doc)
        return result

    @staticmethod
    def _change_group_label(grouped: Dict[str, List], label_map: Dict[str, str]) -> Dict[str, List]:
        """Change les labels des groupes selon un mapping fourni."""
        return {label_map.get(k, k): v for k, v in grouped.items()}

    def generate_summary_tree(self) -> Dict[str, Any]:
        encl_et_suivi = self.tasks.get("Gestion de projet", {})
        plans_fab = self.tasks.get("Plans / Specs / LDN", {})

        return {
            "Enclenchement": encl_et_suivi.get("Enclenchement", []),
            "Calculs": self._change_group_label(
                self.items_by_category(self.calculs, self.app_data.calcul_categories),
                self.app_data.calcul_categories),
            "Plans / Specs / LDN": plans_fab,
            "Options": self._change_group_label(
                self.items_by_category(self.options, self.app_data.option_categories),
                self.app_data.option_categories),
            "Plans et documents contractuels": self._change_group_label(
                self.grouped_lpdc(), self.app_data.lpdc_categories),
            "Laboratoire": self._change_group_label(
                self.items_by_category(self.labo, self.app_data.labo_categories),
                self.app_data.labo_categories),
            "Suivi": encl_et_suivi.get("Suivi", []),
        }
    
    def compute_tree_hours(self, node) -> float:
        if isinstance(node, AbstractTask):
            return node.effective_hours(self.context())
        if isinstance(node, list):
            return sum(self.compute_tree_hours(t) for t in node)
        if isinstance(node, dict):
            return sum(self.compute_tree_hours(v) for v in node.values())
        return 0.0

    def compute_first_machine_subtotal(self) -> float:
        """Calcule le sous-total de base (toutes les tâches)."""
        self.first_machine_subtotal = sum(
            self.compute_tree_hours(data)
            for data in [self.tasks, self.lpdc_docs, self.options, self.calculs, self.labo]
        )
        return self.first_machine_subtotal
    
    def compute_first_machine_total(self) -> float:
        """Calcule le total avec divers."""
        self.first_machine_total = self.first_machine_subtotal * (1 + self.divers_percent)
        return self.first_machine_total
    
    def _compute_multi_machine_coeff(self, quantity: int) -> float:
        """Calcule le coefficient pour machines multiples."""
        if quantity == 2:
            return 1.0
        elif quantity <= 5:
            return (quantity - 1) * 0.75
        elif quantity <= 25:
            return (quantity - 1) * 0.35
        else:
            return (quantity - 1) * 0.15
        
    def compute_n_machines_total(self) -> float:
        """Calcule le total pour n machines."""
        multiplicative_tasks_hours = sum([t.effective_hours(self.context()) for t in self.get_all_tasks() if t.multiplicative])
        coeff = self._compute_multi_machine_coeff(self.quantity)
        additional_hours = multiplicative_tasks_hours * coeff

        self.n_machines_total = self.first_machine_total + additional_hours 
        return self.n_machines_total
    
    def calculate_total_with_rex(self) -> float:
        if self.manual_rex_hours is not None:
            self.total_with_rex = self.manual_rex_hours
        else:
            self.total_with_rex = self.n_machines_total * self.manual_rex_coeff
        return self.total_with_rex
    
    def _lpdc_category(self, doc: LPDCDocument) -> Optional[str]:
        """Détermine la catégorie ORTEMS d'un document LPDC."""
        if self.machine_type not in doc.applicable_pour:
            return None
        if self.secteur in doc.secteur_obligatoire:
            return "BASE"
        if doc.option_possible:
            return "PART"
        return None

    def make_ortems_repartition(self) -> Dict[str, float]:
        """Crée la répartition ORTEMS.

        Itère les mêmes listes que compute_first_machine_subtotal()
        pour garantir la cohérence entre le total et la répartition.
        """
        repartition = dict.fromkeys(self.app_data.jobs.keys(), 0.0)
        ctx = self.context()

        # 1. Tâches générales (répartition per-task)
        for task in self.get_all_tasks():
            hours = task.effective_hours(ctx)
            if hours > 0 and task.ortems_repartition:
                for job_code, coeff in task.ortems_repartition.items():
                    repartition[job_code] += hours * coeff

        # 2. Sources catégorisées (itération directe sur les listes)
        for items, ortems_map in [
            (self.calculs, self.app_data.calcul_ortems),
            (self.options, self.app_data.option_ortems),
            (self.labo,    self.app_data.labo_ortems),
        ]:
            cat_sums: Dict[str, float] = {}
            for item in items:
                cat_sums[item.category] = cat_sums.get(item.category, 0.0) + item.effective_hours(ctx)
            for cat, total in cat_sums.items():
                for job_code, coeff in ortems_map.get(cat, {}).items():
                    repartition[job_code] += total * coeff

        # 3. LPDC (catégorie déterminée par le contexte)
        lpdc_sums: Dict[str, float] = {}
        for doc in self.lpdc_docs:
            hours = doc.effective_hours(ctx)
            if hours > 0:
                cat = self._lpdc_category(doc)
                if cat:
                    lpdc_sums[cat] = lpdc_sums.get(cat, 0.0) + hours
        for cat, total in lpdc_sums.items():
            for job_code, coeff in self.app_data.lpdc_ortems.get(cat, {}).items():
                repartition[job_code] += total * coeff

        # Application du divers et du REX
        for job_code in repartition:
            repartition[job_code] *= (1 + self.divers_percent) * self.manual_rex_coeff

        return repartition
    
    def compute_delai_etude(self) -> Dict[str, float]:
        """Calcule le délai d'étude (mois) à partir de la répartition ORTEMS."""
        repartition = self.make_ortems_repartition()
        heures_proj = repartition.get("PROJ_MACHINE_DEF", 0.0)
        n_proj = self.app_data.n_projeteurs.get(self.secteur, 1)
        jours_ouvrables_par_mois = 365.25 / 12 * 5 / 7

        delai_brut = (heures_proj / 7.7) / jours_ouvrables_par_mois / n_proj if n_proj else 0.0
        taux = self.app_data.taux_productivite or 1.0
        delai_productif = delai_brut / taux
        conges_mois = delai_productif * self.app_data.pct_conges
        delai_reel = self.app_data.demarrage_mois + conges_mois + delai_productif

        return {
            "heures_proj": heures_proj,
            "n_projeteurs": n_proj,
            "delai_brut": delai_brut,
            "delai_productif": delai_productif,
            "conges_mois": conges_mois,
            "delai_reel": delai_reel,
        }

    def export_ortems_excel(self, path: str):
        _export_ortems(self, path)

    def export_excel_report(self, path: str):
        _export_report(self, path)


class Model(QObject):
    project_changed = pyqtSignal()  # Émis lors de l'application des paramètres par défaut
    data_updated = pyqtSignal()     # Émis lors de modifications mineures (valeurs, checkboxes)

    def __init__(self, app_data: ApplicationData):
        super().__init__()
        self.app_data = app_data
        self.project = Project(app_data)

    # ------------------------------------------------------------------
    # Sauvegarde / Chargement
    # ------------------------------------------------------------------

    def save_project(self) -> dict:
        """Sérialise le projet : valeurs scalaires + delta des modifications."""
        prj = self.project
        return {
            "version": 1,
            "project": {
                "crm_number":   prj.crm_number,
                "client":       prj.client,
                "affaire":      prj.affaire,
                "das":          prj.das,
                "secteur":      prj.secteur,
                "machine_type": prj.machine_type,
                "product":      prj.product,
                "designation":  prj.designation,
                "quantity":     prj.quantity,
                "revision":     prj.revision,
                "date":         prj.date,
                "created_by":   prj.created_by,
                "validated_by": prj.validated_by,
                "description":  prj.description,
                "divers_percent":    prj.divers_percent,
                "manual_rex_coeff":  prj.manual_rex_coeff,
            },
            "modifications": {
                "lpdc_docs": [
                    {"index": d.index, "is_selected": d.is_selected, "manual_base_hours": d.manual_base_hours}
                    for d in prj.lpdc_docs
                    if d.is_selected or d.manual_base_hours is not None
                ],
                "options": [
                    {"index": o.index, "is_selected": o.is_selected, "manual_base_hours": o.manual_base_hours}
                    for o in prj.options
                    if o.is_selected or o.manual_base_hours is not None
                ],
                "calculs": [
                    {"index": c.index, "is_selected": c.is_selected, "manual_base_hours": c.manual_base_hours}
                    for c in prj.calculs
                    if c.is_selected or c.manual_base_hours is not None
                ],
                "tasks": [
                    {"index": t.index, "manual_base_hours": t.manual_base_hours}
                    for t in prj.get_all_tasks()
                    if t.manual_base_hours is not None
                ],
                "labo": [
                    {"index": l.index, "is_selected": l.is_selected, "manual_base_hours": l.manual_base_hours}
                    for l in prj.labo
                    if l.is_selected or l.manual_base_hours is not None
                ],
                "category_corrections": prj.category_corrections,
            },
        }

    def load_project(self, data: dict):
        """Charge un projet : applique les valeurs puis les modifications."""
        prj = self.project
        pd = data.get("project", {})

        # Valeurs scalaires
        prj.crm_number   = pd.get("crm_number", "")
        prj.client       = pd.get("client", "")
        prj.affaire      = pd.get("affaire", "")
        prj.das          = pd.get("das", "")
        prj.secteur      = pd.get("secteur", "")
        prj.machine_type = pd.get("machine_type", "")
        prj.product      = pd.get("product", "")
        prj.designation  = pd.get("designation", "")
        prj.quantity     = pd.get("quantity", 1)
        prj.revision     = pd.get("revision", "A")
        prj.date         = pd.get("date", "")
        prj.created_by   = pd.get("created_by", "")
        prj.validated_by = pd.get("validated_by", "")
        prj.description  = pd.get("description", "")

        # Reconstruire les listes à partir des données sources
        prj.apply_defaults()

        # Restaurer divers/rex APRÈS apply_defaults (qui les réinitialise)
        prj.divers_percent   = pd.get("divers_percent", 0.05)
        prj.manual_rex_coeff = pd.get("manual_rex_coeff", 1.0)

        # Appliquer les modifications
        mods = data.get("modifications", {})

        lpdc_idx = {m["index"]: m for m in mods.get("lpdc_docs", [])}
        for doc in prj.lpdc_docs:
            if doc.index in lpdc_idx:
                m = lpdc_idx[doc.index]
                doc.is_selected  = m.get("is_selected", doc.is_selected)
                doc.manual_base_hours = m.get("manual_base_hours")

        opt_idx = {m["index"]: m for m in mods.get("options", [])}
        for opt in prj.options:
            if opt.index in opt_idx:
                m = opt_idx[opt.index]
                opt.is_selected  = m.get("is_selected", opt.is_selected)
                opt.manual_base_hours = m.get("manual_base_hours")

        calc_idx = {m["index"]: m for m in mods.get("calculs", [])}
        for calc in prj.calculs:
            if calc.index in calc_idx:
                m = calc_idx[calc.index]
                calc.is_selected  = m.get("is_selected", calc.is_selected)
                calc.manual_base_hours = m.get("manual_base_hours")

        task_idx = {m["index"]: m for m in mods.get("tasks", [])}
        for task in prj.get_all_tasks():
            if task.index in task_idx:
                task.manual_base_hours = task_idx[task.index].get("manual_base_hours")

        labo_idx = {m["index"]: m for m in mods.get("labo", [])}
        for labo in prj.labo:
            if labo.index in labo_idx:
                m = labo_idx[labo.index]
                labo.is_selected = m.get("is_selected", labo.is_selected)
                labo.manual_base_hours = m.get("manual_base_hours")

        prj.category_corrections = mods.get("category_corrections", {})