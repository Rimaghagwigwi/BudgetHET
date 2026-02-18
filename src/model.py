from typing import Dict, List, Optional, Any
from src.utils.ApplicationData import ApplicationData
from src.utils.Task import AbstractTask, GeneralTask, LPDCDocument, Labo, Option, Calcul
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

        self.lpdc_coeff: float = 1.0
        self.calcul_coeff_type_affaire: Dict[str, float] = {} # Dict[activité: coeff] appliqué aux calculs selon le type d'affaire
        self.option_coeff_category: Dict[str, float] = {} # Dict[category: coeff] appliqué aux options selon le type d'affaire
        
        self.divers_percent: float = 0.05
        self.manual_rex_coeff: float = 1.0

        self.first_machine_total: Optional[float] = None
        self.n_machines_total: Optional[float] = None
        self.total_with_divers: Optional[float] = None
        self.total_with_rex: Optional[float] = None
        
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

            "LPDC_coeff": self.lpdc_coeff,
            "calcul_coeff_type_affaire": self.calcul_coeff_type_affaire,
            "option_coeff_category": self.option_coeff_category
        }

    def apply_defaults(self):
        """Applique les valeurs par défaut après avoir choisi le type de machine, le secteur et le type d'affaire."""
        
        ctx = self.context()

        # Récupérer les coefficients dépendant du contexte depuis app_data
        self.lpdc_coeff = self.app_data.lpdc_coefficients[self.secteur]
        self.calcul_coeff_type_affaire = self.app_data.calcul_coeff_type_affaire[self.affaire]
        self.option_coeff_category = self.app_data.option_category_coeff.get(self.affaire, {})
        
        self.divers_percent = 0.05
        self.manual_rex_coeff = 1.0

        self.first_machine_total = None
        self.n_machines_total = None
        self.total_with_divers = None
        self.total_with_rex = None
        
        self.tasks = self.app_data.tasks.copy()
        self.lpdc_docs = [doc for doc in self.app_data.lpdc_docs if doc.is_active(ctx) or doc.option_possible]
        self.options = self.app_data.options.copy()
        self.calculs = [calc for calc in self.app_data.calculs if calc.is_available_as_option(ctx) or calc.is_mandatory(ctx)]
        self.labo = self.app_data.labo.copy()
    
    def get_task_default_hours(self, task: GeneralTask) -> float:
        return task.default_hours(self.context())

    def get_all_tasks(self) -> List[GeneralTask]:
        """Retourne la liste plate de toutes les tâches générales."""
        return [task for subcats in self.tasks.values() for tasks in subcats.values() for task in tasks]

    def generate_summary_tree(self) -> Dict[str, Any]:
        return {
            "Tâches Générales": self.tasks,
            "Pièces et documents contractuels": self.lpdc_docs,
            "Options": self.options,
            "Calculs": self.calculs,
            "Laboratoire": self.labo,
        }
    
    def compute_tree_hours(self, node) -> float:
        if isinstance(node, AbstractTask):
            return node.effective_hours(self.context())
        if isinstance(node, list):
            return sum(self.compute_tree_hours(t) for t in node)
        if isinstance(node, dict):
            return sum(self.compute_tree_hours(v) for v in node.values())
        return 0.0

    def compute_total_firstmachine(self) -> float:
        """Calcule le sous-total de base (toutes les tâches)."""
        self.first_machine_total = sum(
            self.compute_tree_hours(data)
            for data in [self.tasks, self.lpdc_docs, self.options, self.calculs, self.labo]
        )
        return self.first_machine_total
    
    def _compute_multi_machine_coeff(self, quantity: int) -> float:
        """Calcule le coefficient pour machines multiples."""
        if quantity < 2:
            return 1.0
        elif quantity < 4:
            return 1 + (quantity - 1) * 0.75
        elif quantity < 24:
            return 1 + (quantity - 1) * 0.35
        else:
            return 1 + (quantity - 1) * 0.15
        
    def compute_n_machines_total(self) -> float:
        """Calcule le total pour n machines."""
        self.n_machines_total = self.first_machine_total * self._compute_multi_machine_coeff(self.quantity)
        return self.n_machines_total
    
    def compute_total_with_divers(self) -> float:
        """Calcule le total avec divers."""
        self.total_with_divers = self.n_machines_total * (1 + self.divers_percent)
        return self.total_with_divers
    
    def calculate_total_hours(self) -> float:
        self.total_with_rex = self.total_with_divers * self.manual_rex_coeff
        return self.total_with_rex


class Model(QObject):
    project_changed = pyqtSignal()  # Émis lors de l'application des paramètres par défaut
    data_updated = pyqtSignal()     # Émis lors de modifications mineures (valeurs, checkboxes)

    def __init__(self, app_data: ApplicationData):
        super().__init__()
        self.app_data = app_data
        self.project = Project(app_data)