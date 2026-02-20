from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, override


class AbstractTask:
    def __init__(self, label: str):
        self.label = label
        self.manual_hours: Optional[float] = None

    @abstractmethod
    def default_hours(self, context: Dict[str, Any]) -> float:
        pass

    @abstractmethod
    def effective_hours(self, context: Dict[str, Any]) -> float:
        pass


class GeneralTask(AbstractTask):
    def __init__(self, index: int, label: str,
                 base_hours_machine: Dict[str, float],
                 coeff_type_affaire: Dict[str, float],
                 coeff_secteur: Dict[str, float],
                 mutiplicative: bool = False):
        super().__init__(label)
        self.index = index
        self.base_hours_machine = base_hours_machine
        self.coeff_type_affaire = coeff_type_affaire
        self.coeff_secteur = coeff_secteur
        self.mutiplicative = mutiplicative

    @override
    def default_hours(self, context: Dict[str, Any]) -> float:
        product = context.get("product", "")
        affaire = context.get("affaire", "")
        secteur = context.get("secteur", "")
        
        base = self.base_hours_machine.get(product, 0.0)
        coeff_affaire = self.coeff_type_affaire.get(affaire, 1.0)
        coeff_secteur = self.coeff_secteur.get(secteur, 1.0)
        
        return base * coeff_affaire * coeff_secteur
    
    @override
    def effective_hours(self, context: Dict[str, Any]) -> float:
        if self.manual_hours is not None:
            return self.manual_hours
        else:
            return self.default_hours(context)
        
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
        self.manual_hours: Optional[float] = None

    def is_active(self, context: Dict[str, Any]) -> bool:
        """Détermine si le document est sélectionné en fonction du secteur."""
        machine_type = context.get("machine_type", "")
        if machine_type not in self.applicable_pour:
            return False
        secteur = context.get("secteur", "")
        if secteur in self.secteur_obligatoire:
            return True
        if self.option_possible:
            return self.is_selected
        return False

    @override
    def default_hours(self, context: Dict[str, Any]) -> float:
        return self.hours

    @override
    def effective_hours(self, context: Dict[str, Any]) -> float:
        coeff_affaire = context["LPDC_affaire_coeff"]
        coeff_secteur = context["LPDC_secteur_coeff"]
        if not self.is_active(context):
            return 0.0
        if self.manual_hours is not None:
            return self.manual_hours
        else:
            return self.default_hours(context) * coeff_affaire * coeff_secteur

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
        self.manual_hours: Optional[float] = None

    @override
    def default_hours(self, context: Dict[str, Any]) -> float:
        return self.hours

    @override
    def effective_hours(self, context: Dict[str, Any]) -> float:
        coeff_option = context["option_coeff_category"].get(self.category, 1.0)
        final_hours = self.default_hours(context) * coeff_option
        if self.is_selected:
            return self.manual_hours if self.manual_hours is not None else final_hours
        else:
            return 0.0
        
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
        # manual_hours is set in AbstractTask.__init__

    def is_mandatory(self, context: Dict[str, Any]) -> bool:
        machine_type = context.get("machine_type", "")
        return self.selection.get(machine_type, "Non") == "Oui"

    def is_available_as_option(self, context: Dict[str, Any]) -> bool:
        machine_type = context.get("machine_type", "")
        return self.selection.get(machine_type, "Non") == "Choix"
    
    def is_active(self, context: Dict[str, Any]) -> bool:
        return self.is_mandatory(context) or (self.is_available_as_option(context) and self.is_selected)

    @override
    def default_hours(self, context: Dict[str, Any]) -> float:
        machine_type = context.get("machine_type", "")
        return self.hours.get(machine_type, 0.0)

    @override
    def effective_hours(self, context: Dict[str, Any]) -> float:
        affaire_activity_coeff = context["calcul_coeff_type_affaire"].get(self.category, 1.0)
        if not self.is_active(context):
            return 0.0
        elif self.manual_hours is not None:
            return self.manual_hours
        else:
            return self.default_hours(context) * affaire_activity_coeff
        
class Labo(AbstractTask):
    def __init__(self, index: int, label: str, hours: float):
        super().__init__(label)
        self.index = index
        self.hours = hours

    @override
    def default_hours(self, context: Dict[str, Any]) -> float:
        return self.hours
    
    @override
    def effective_hours(self, context: Dict[str, Any]) -> float:
        if self.manual_hours is not None:
            return self.manual_hours
        else:
            return self.default_hours(context)