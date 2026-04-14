from abc import abstractmethod
from typing import Dict, List, Optional, Any, override


class AbstractTask:
    def __init__(self, label: str):
        self.label = label
        self.manual_base_hours: Optional[float] = None
        self.category_override_hours: Optional[float] = None

    @abstractmethod
    def base_hours(self, context: Dict[str, Any]) -> float:
        """Heures brutes avant application des coefficients de contexte."""
        pass

    def context_coefficients(self, context: Dict[str, Any]) -> float:
        """Produit des coefficients de contexte. Vaut 1.0 par défaut."""
        return 1.0

    def is_active(self, context: Dict[str, Any]) -> bool:
        """Indique si la tâche doit contribuer au total. Toujours True par défaut."""
        return True

    def default_hours(self, context: Dict[str, Any]) -> float:
        return self.base_hours(context) * self.context_coefficients(context)

    def effective_hours(self, context: Dict[str, Any]) -> float:
        if self.category_override_hours is not None:
            return self.category_override_hours
        if not self.is_active(context):
            return 0.0
        if self.manual_base_hours is not None:
            return self.manual_base_hours * self.context_coefficients(context)
        return self.default_hours(context)


class GeneralTask(AbstractTask):
    def __init__(self, index: int, label: str,
                 base_hours_machine: Dict[str, float],
                 coeff_type_affaire: Dict[str, float],
                 coeff_secteur: Dict[str, float],
                 multiplicative: bool = False,
                 ortems_repartition: Dict[str, float] = None):
        super().__init__(label)
        self.index = index
        self.base_hours_machine = base_hours_machine
        self.coeff_type_affaire = coeff_type_affaire
        self.coeff_secteur = coeff_secteur
        self.multiplicative = multiplicative
        self.ortems_repartition = ortems_repartition if ortems_repartition is not None else {}

    def context_coefficients(self, context: Dict[str, Any]) -> float:
        affaire = context.get("affaire", "")
        secteur = context.get("secteur", "")
        return self.coeff_type_affaire.get(affaire, 1.0) * self.coeff_secteur.get(secteur, 1.0)

    @override
    def base_hours(self, context: Dict[str, Any]) -> float:
        product = context.get("product", "")
        return self.base_hours_machine.get(product, 0.0)
        
class LPDCDocument(AbstractTask):
    def __init__(self, label: str,
                 index: int,
                 hours: float,
                 applicable_pour: List[str],
                 secteur_obligatoire: List[str],
                 option_possible: bool):
        super().__init__(label)
        self.index = index
        self.hours = hours
        self.applicable_pour = applicable_pour
        self.secteur_obligatoire = secteur_obligatoire
        self.option_possible = option_possible

        self.is_selected: bool = False

    def is_active(self, context: Dict[str, Any]) -> bool:
        machine_type = context.get("machine_type", "")
        if machine_type not in self.applicable_pour:
            return False
        secteur = context.get("secteur", "")
        if secteur in self.secteur_obligatoire:
            return True
        return self.option_possible and self.is_selected

    def context_coefficients(self, context: Dict[str, Any]) -> float:
        return context["lpdc_coeff_affaire"] * context["lpdc_coeff_secteur"]

    @override
    def base_hours(self, context: Dict[str, Any]) -> float:
        return self.hours

class Option(AbstractTask):
    def __init__(self, label: str,
                 index: int,
                 category: str,
                 hours: float):
        super().__init__(label)
        self.index = index
        self.category = category
        self.hours = hours

        self.is_selected: bool = False

    def context_coefficients(self, context: Dict[str, Any]) -> float:
        return context["option_coeff"].get(self.category, 1.0)

    def is_active(self, context: Dict[str, Any]) -> bool:
        return self.is_selected

    @override
    def base_hours(self, context: Dict[str, Any]) -> float:
        return self.hours
        
class Calcul(AbstractTask):
    def __init__(self, label: str,
                 index: int,
                 category: str,
                 hours: Dict[str, float],  # Heures par type de machine
                 selection: Dict[str, str]):  # Mode de sélection par type de machine
        super().__init__(label)
        self.index = index
        self.category = category
        self.hours = hours
        self.selection = selection
        self.is_selected: bool = False

    def is_mandatory(self, context: Dict[str, Any]) -> bool:
        machine_type = context.get("machine_type", "")
        return self.selection.get(machine_type, "") == "mandatory"

    def is_available_as_option(self, context: Dict[str, Any]) -> bool:
        machine_type = context.get("machine_type", "")
        return self.selection.get(machine_type, "") == "optional"
    
    def is_active(self, context: Dict[str, Any]) -> bool:
        return self.is_mandatory(context) or (self.is_available_as_option(context) and self.is_selected)

    def context_coefficients(self, context: Dict[str, Any]) -> float:
        return context["calcul_coeff"].get(self.category, 1.0)

    @override
    def base_hours(self, context: Dict[str, Any]) -> float:
        machine_type = context.get("machine_type", "")
        return self.hours.get(machine_type, 0.0)
        
class Labo(AbstractTask):
    def __init__(self, index: int, label: str, hours: float, category: str, coeff_secteur: Dict[str, float]):
        super().__init__(label)
        self.index = index
        self.hours = hours
        self.category = category
        self.coeff_secteur = coeff_secteur
        self.is_selected: bool = False

    def is_mandatory(self, context: Dict[str, Any]) -> bool:
        secteur = context.get("secteur", "")
        return secteur in self.coeff_secteur
    
    def is_active(self, context: Dict[str, Any]) -> bool:
        return self.is_mandatory(context) or self.is_selected

    def context_coefficients(self, context: Dict[str, Any]) -> float:
        secteur = context.get("secteur", "")
        coeff_affaire = context.get("labo_coeff_affaire", 1.0)
        return self.coeff_secteur.get(secteur, 1.0) * coeff_affaire

    @override
    def base_hours(self, context: Dict[str, Any]) -> float:
        return self.hours