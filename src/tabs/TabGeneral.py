from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QPushButton, QDateEdit, QTextEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal, QDate, QTimer
from src.model import Model
from src.widgets import NoWheelSpinBox
from src.utils.ApplicationData import ApplicationData # Import custom widget

class TabGeneral(QWidget):
    apply_clicked = pyqtSignal() # Signal personnalisé

    def __init__(self):
        super().__init__()
        self.setObjectName("tabGeneral")
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # 1. N° CRM
        self.input_crm = QLineEdit()
        self.input_crm.setPlaceholderText("Ex: 2023.12.0001")
        form.addRow("N° CRM :", self.input_crm)
        
        # 2. Client
        self.input_client = QLineEdit()
        form.addRow("Client :", self.input_client)
        
        # 3. Type d'affaire
        self.combo_type_affaire = QComboBox()
        form.addRow("Type d'affaire :", self.combo_type_affaire)
        
        # 4. DAS
        self.combo_das = QComboBox()
        form.addRow("DAS :", self.combo_das)

        # 5. Secteur
        self.combo_secteur = QComboBox()
        form.addRow("Secteur :", self.combo_secteur)
        
        # 6. Categorie produit
        self.combo_category = QComboBox()
        form.addRow("Catégorie produit :", self.combo_category)
        
        # 7. Produit
        self.combo_product = QComboBox()
        form.addRow("Produit :", self.combo_product)
        
        # 8. Désignation produit
        self.input_designation = QLineEdit()
        form.addRow("Désignation produit :", self.input_designation)
        
        # 9. Nombre de machines
        self.spin_qty = NoWheelSpinBox() # Use NoWheelSpinBox
        self.spin_qty.setRange(1, 1000)
        self.spin_qty.setValue(1)
        form.addRow("Nombre de machines :", self.spin_qty)
        
        # 10. Révision du chiffrage
        self.combo_revision = QComboBox()
        self.combo_revision.addItems(["A", "B", "C", "D", "E", "F", "G"])
        form.addRow("Révision :", self.combo_revision)
        
        # 11. Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date :", self.date_edit)
        
        # 12. Réalisé par
        self.combo_realise_par = QComboBox()
        form.addRow("Réalisé par :", self.combo_realise_par)
        
        # 13. Validé par
        self.combo_valide_par = QComboBox()
        form.addRow("Validé par :", self.combo_valide_par)
        
        # 14. Description
        self.text_description = QTextEdit()
        form.addRow("Description :", self.text_description)
        
        self.btn_apply = QPushButton("Appliquer Paramètres par Défaut")
        
        
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(self.btn_apply)
    
    def set_combo_items(self, combo: QComboBox, items):
        """
        Remplit un QComboBox avec des items.
        - Si items est une liste : ajoute directement les éléments
        - Si items est un dict : affiche les valeurs et stocke les clés comme données
        """
        combo.clear()
        if isinstance(items, dict):
            for code, label in items.items():
                combo.addItem(label, code)
        elif isinstance(items, list):
            combo.addItems(items)
        else:
            combo.addItems(list(items))
    
    def get_value(self, widget):
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QComboBox):
            # Retourne currentData() si disponible (code), sinon currentText() (label)
            data = widget.currentData()
            return data if data is not None else widget.currentText()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QDateEdit):
            return widget.date().toString("yyyy-MM-dd")
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        else:
            return None

class TabGeneralController:
    def __init__(self, model, view):
        self.model: Model = model
        self.view: TabGeneral = view
        self.populate_general_tab()
        self.create_signals()

    def populate_general_tab(self):
        try:
            # Type d'affaire
            self.view.set_combo_items(self.view.combo_type_affaire, self.model.app_data.types_affaires)

            # DAS et secteurs
            self.view.set_combo_items(self.view.combo_das, self.model.app_data.das)
            self.update_secteur_list()

            # Catégories produit
            self.view.set_combo_items(self.view.combo_category, self.model.app_data.types_produit)
            self.update_product_list()

            # Personnes
            self.view.set_combo_items(self.view.combo_realise_par, self.model.app_data.personnes)
            self.view.set_combo_items(self.view.combo_valide_par, self.model.app_data.personnes)

        except Exception as e:
            print(f"Erreur lors du peuplement de l'onglet Général: {e}")
        
    
    def update_secteur_list(self):
        """Met à jour la liste des secteurs en fonction du DAS sélectionné"""
        das_code = self.view.combo_das.currentData()  # Récupère le code du DAS
        if das_code:
            secteurs = self.model.app_data.secteurs.get(das_code, {})
            self.view.set_combo_items(self.view.combo_secteur, secteurs)
        else:
            self.view.combo_secteur.clear()

    def update_product_list(self):
        """Met à jour la liste des produits en fonction du type de produit sélectionné"""
        type_code = self.view.combo_category.currentData()  # Récupère le code du type
        if type_code:
            products = self.model.app_data.categories_produit.get(type_code, {})
            self.view.set_combo_items(self.view.combo_product, products)
        else:
            self.view.combo_product.clear()

    def apply_defaults(self):
        self.update_project_from_ui()
        self.model.project.apply_defaults()

        # Notifier les autres onglets que les données ont changé
        self.model.project_changed.emit()
        self.view.btn_apply.setText("Paramètres appliqués !")
        QTimer.singleShot(2000, lambda: self.view.btn_apply.setText("Appliquer Paramètres par Défaut"))

    def update_project_from_ui(self):
        prj = self.model.project

        prj.crm_number = self.view.get_value(self.view.input_crm)
        prj.client = self.view.get_value(self.view.input_client)
        prj.affaire = self.view.get_value(self.view.combo_type_affaire)
        prj.das = self.view.get_value(self.view.combo_das)
        prj.secteur = self.view.get_value(self.view.combo_secteur)
        prj.machine_type = self.view.get_value(self.view.combo_category)
        prj.product = self.view.get_value(self.view.combo_product)
        prj.designation = self.view.get_value(self.view.input_designation)
        prj.quantity = self.view.spin_qty.value()
        prj.revision = self.view.get_value(self.view.combo_revision)
        prj.date = self.view.get_value(self.view.date_edit)
        prj.created_by = self.view.get_value(self.view.combo_realise_par)
        prj.validated_by = self.view.get_value(self.view.combo_valide_par)
        prj.description = self.view.get_value(self.view.text_description)

    def create_signals(self):
        # Création des signaux qui utilisent les méthodes ci-dessus
        self.view.combo_das.currentIndexChanged.connect(self.update_secteur_list)
        self.view.combo_category.currentIndexChanged.connect(self.update_product_list)
        self.view.btn_apply.clicked.connect(self.apply_defaults)

        # Modification des données du projet lors du changement des champs
        widgets: List[QWidget] = [
            self.view.input_crm,
            self.view.input_client,
            self.view.combo_type_affaire,
            self.view.combo_das,
            self.view.combo_secteur,
            self.view.combo_category,
            self.view.combo_product,
            self.view.input_designation,
            self.view.spin_qty,
            self.view.combo_revision,
            self.view.date_edit,
            self.view.combo_realise_par,
            self.view.combo_valide_par,
            self.view.text_description
        ]
        for widget in widgets:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_project_from_ui)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.update_project_from_ui)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(self.update_project_from_ui)
            elif isinstance(widget, QDateEdit):
                widget.dateChanged.connect(self.update_project_from_ui)
            elif isinstance(widget, QTextEdit):
                widget.textChanged.connect(self.update_project_from_ui)