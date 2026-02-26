from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QPushButton, QDateEdit, QTextEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal, QDate, QTimer
from src.model import Model
from src.utils.widgets import NoWheelSpinBox

class TabGeneral(QWidget):
    field_changed = pyqtSignal(int) # Signal pour les champs non essentiels

    def __init__(self):
        super().__init__()
        self.setObjectName("tabGeneral")
        layout = QVBoxLayout(self)

        # Bouton importer un projet
        self.btn_import = QPushButton("Importer un projet")
        layout.addWidget(self.btn_import)

        form = QFormLayout()
        
        # 1. N° CRM
        self.input_crm = QLineEdit()
        self.input_crm.setPlaceholderText("Ex: 2023.12.0001")
        form.addRow("N° CRM :", self.input_crm)
        self.input_crm.textChanged.connect(lambda: self.field_changed.emit(0))
        
        # 2. Client
        self.input_client = QLineEdit()
        form.addRow("Client :", self.input_client)
        self.input_client.textChanged.connect(lambda: self.field_changed.emit(0))
        
        # 3. Type d'affaire
        self.combo_type_affaire = QComboBox()
        form.addRow("Type d'affaire :", self.combo_type_affaire)
        self.combo_type_affaire.currentIndexChanged.connect(lambda: self.field_changed.emit(1))
        
        # 4. DAS
        self.combo_das = QComboBox()
        form.addRow("DAS * :", self.combo_das)
        self.combo_das.currentIndexChanged.connect(lambda: self.field_changed.emit(2))

        # 5. Secteur
        self.combo_secteur = QComboBox()
        form.addRow("Secteur * :", self.combo_secteur)
        self.combo_secteur.currentIndexChanged.connect(lambda: self.field_changed.emit(2))
        
        # 6. Categorie produit
        self.combo_category = QComboBox()
        form.addRow("Catégorie produit * :", self.combo_category)
        self.combo_category.currentIndexChanged.connect(lambda: self.field_changed.emit(2))
        
        # 7. Produit
        self.combo_product = QComboBox()
        form.addRow("Produit * :", self.combo_product)
        self.combo_product.currentIndexChanged.connect(lambda: self.field_changed.emit(2))
        
        # 8. Désignation produit
        self.input_designation = QLineEdit()
        form.addRow("Désignation produit :", self.input_designation)
        self.input_designation.editingFinished.connect(lambda: self.field_changed.emit(0))
        
        # 9. Nombre de machines
        self.spin_qty = NoWheelSpinBox() # Use NoWheelSpinBox
        self.spin_qty.setRange(1, 1000)
        self.spin_qty.setValue(1)
        form.addRow("Nombre de machines :", self.spin_qty)
        self.spin_qty.editingFinished.connect(lambda: self.field_changed.emit(1))
        
        # 10. Révision du chiffrage
        self.combo_revision = QComboBox()
        self.combo_revision.addItems(["A", "B", "C", "D", "E", "F", "G"])
        form.addRow("Révision :", self.combo_revision)
        self.combo_revision.currentIndexChanged.connect(lambda: self.field_changed.emit(0))
        
        # 11. Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date :", self.date_edit)
        self.date_edit.dateChanged.connect(lambda: self.field_changed.emit(0))
        
        # 12. Réalisé par
        self.combo_realise_par = QComboBox()
        form.addRow("Réalisé par :", self.combo_realise_par)
        self.combo_realise_par.currentIndexChanged.connect(lambda: self.field_changed.emit(0))
        
        # 13. Validé par
        self.combo_valide_par = QComboBox()
        form.addRow("Validé par :", self.combo_valide_par)
        self.combo_valide_par.currentIndexChanged.connect(lambda: self.field_changed.emit(0))
        
        # 14. Description
        self.text_description = QTextEdit()
        form.addRow("Description :", self.text_description)
        self.text_description.textChanged.connect(lambda: self.field_changed.emit(0))
        
        layout.addLayout(form)

        note = QLabel("(*) Modifier ces champs réinitialise le projet à sa valeur par défaut")
        note.setObjectName("footnote")
        layout.addWidget(note)

        layout.addStretch()
    
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
    DEBOUNCE_MS = 300  # Délai avant de déclencher la mise à jour lourde

    def __init__(self, model: Model, view: TabGeneral):
        self.model = model
        self.view = view
        self._pending_max_criticity = 0

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(self.DEBOUNCE_MS)
        self._debounce_timer.timeout.connect(self._on_debounce_fired)

        self.populate_general_tab()
        self.create_signals()

        self.view.field_changed.connect(self.update_project_from_ui)

    def populate_general_tab(self):
        try:
            # Type d'affaire
            self.view.set_combo_items(self.view.combo_type_affaire, self.model.app_data.types_affaires)

            # DAS et secteurs
            self.view.set_combo_items(self.view.combo_das, self.model.app_data.das)
            self.update_secteur_list()

            # Catégories produit
            self.view.set_combo_items(self.view.combo_category, self.model.app_data.product_types)
            self.update_product_list()

            # Personnes
            self.view.set_combo_items(self.view.combo_realise_par, self.model.app_data.people)
            self.view.set_combo_items(self.view.combo_valide_par, self.model.app_data.people)
        
            self.update_project_from_ui(2)
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
            products = self.model.app_data.product.get(type_code, {})
            self.view.set_combo_items(self.view.combo_product, products)
        else:
            self.view.combo_product.clear()

    def update_project_from_ui(self, max_criticity=0):
        # Lecture des widgets Qt (doit rester sur le thread principal)
        prj = self.model.project
        prj.crm_number = self.view.get_value(self.view.input_crm)
        prj.client = self.view.get_value(self.view.input_client)
        prj.designation = self.view.get_value(self.view.input_designation)
        prj.revision = self.view.get_value(self.view.combo_revision)
        prj.date = self.view.get_value(self.view.date_edit)
        prj.created_by = self.view.get_value(self.view.combo_realise_par)
        prj.validated_by = self.view.get_value(self.view.combo_valide_par)
        prj.description = self.view.get_value(self.view.text_description)
        prj.affaire = self.view.get_value(self.view.combo_type_affaire)
        prj.quantity = self.view.spin_qty.value()
        prj.das = self.view.get_value(self.view.combo_das)
        prj.secteur = self.view.get_value(self.view.combo_secteur)
        prj.machine_type = self.view.get_value(self.view.combo_category)
        prj.product = self.view.get_value(self.view.combo_product)

        # Mise à jour lourde (apply_defaults + reconstruction des onglets) : débouncée
        if max_criticity >= 1:
            self._pending_max_criticity = max(self._pending_max_criticity, max_criticity)
            self._debounce_timer.start()  # repart à zéro si déjà actif

    def _on_debounce_fired(self):
        """Appelé une seule fois après DEBOUNCE_MS ms d'inactivité sur les champs importants."""
        criticity = self._pending_max_criticity
        self._pending_max_criticity = 0
        if criticity >= 2:
            self.model.project.apply_defaults()
        self.model.project_changed.emit()

    def _set_combo_by_data(self, combo: QComboBox, data):
        """Sélectionne dans un QComboBox l'item dont itemData() == data."""
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                combo.setCurrentIndex(i)
                return
        if data:
            combo.setCurrentText(str(data))

    def load_project_to_ui(self):
        """Remplit tous les widgets de l'onglet Général depuis self.model.project."""
        prj = self.model.project

        # Bloquer les signaux pour éviter des mises à jour en cascade
        widgets = [
            self.view.input_crm, self.view.input_client, self.view.combo_type_affaire,
            self.view.combo_das, self.view.combo_secteur, self.view.combo_category,
            self.view.combo_product, self.view.input_designation, self.view.spin_qty,
            self.view.combo_revision, self.view.date_edit, self.view.combo_realise_par,
            self.view.combo_valide_par, self.view.text_description,
        ]
        for w in widgets:
            w.blockSignals(True)

        self.view.input_crm.setText(prj.crm_number)
        self.view.input_client.setText(prj.client)
        self._set_combo_by_data(self.view.combo_type_affaire, prj.affaire)

        # DAS + mise à jour de la liste secteurs
        self._set_combo_by_data(self.view.combo_das, prj.das)
        secteurs = self.model.app_data.secteurs.get(prj.das, {})
        self.view.set_combo_items(self.view.combo_secteur, secteurs)
        self._set_combo_by_data(self.view.combo_secteur, prj.secteur)

        # Catégorie produit + mise à jour de la liste produits
        self._set_combo_by_data(self.view.combo_category, prj.machine_type)
        products = self.model.app_data.product.get(prj.machine_type, {})
        self.view.set_combo_items(self.view.combo_product, products)
        self._set_combo_by_data(self.view.combo_product, prj.product)

        self.view.input_designation.setText(prj.designation)
        self.view.spin_qty.setValue(prj.quantity)
        self.view.combo_revision.setCurrentText(prj.revision)
        if prj.date:
            self.view.date_edit.setDate(QDate.fromString(prj.date, "yyyy-MM-dd"))
        self._set_combo_by_data(self.view.combo_realise_par, prj.created_by)
        self._set_combo_by_data(self.view.combo_valide_par, prj.validated_by)
        self.view.text_description.setPlainText(prj.description)

        for w in widgets:
            w.blockSignals(False)

        # Synchroniser les valeurs scalaires de l'UI vers le modèle (sans apply_defaults,
        # qui a déjà été appelé par load_project et dont le résultat inclut les modifications)
        self._debounce_timer.stop()
        self._pending_max_criticity = 0
        self.update_project_from_ui(0)  # criticity 0 : lecture seule, pas d'apply_defaults
        self.model.project_changed.emit()  # reconstruire les onglets avec l'état chargé

    def create_signals(self):
        # Création des signaux qui utilisent les méthodes ci-dessus
        self.view.combo_das.currentIndexChanged.connect(self.update_secteur_list)
        self.view.combo_category.currentIndexChanged.connect(self.update_product_list)