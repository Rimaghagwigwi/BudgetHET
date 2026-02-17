from typing import Dict, List, Tuple
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QLabel, 
                             QVBoxLayout, QAbstractItemView, QCheckBox, QLineEdit, 
                             QHBoxLayout, QWidget, QScrollArea, QFrame)


class TaskTableWidget(QTableWidget):
    """Widget de tableau générique pour afficher les tâches (Tâches générales, Calculs, Options, LPDC)."""
    
    manual_value_modified = pyqtSignal(str, int)  # (text, ref)
    checkbox_toggled = pyqtSignal(bool, int)  # (is_checked, ref)

    def __init__(self, label: str, task_type: str, is_optional: bool = False):
        super().__init__()
        self.label = QLabel(label) if label else None
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        self.task_type = task_type
        self.is_optional = is_optional
        self.col_offset = 1 if is_optional else 0  # Décalage pour la colonne checkbox

        self.categories: Dict[str, Dict] = {}  # category_name -> {task_list, total_hours}

        self._setup_table()
        self.adjust_height_to_content()

    def _setup_table(self):
        """Configure les colonnes et le style du tableau."""
        columns = (["Choix", "Ref", self.task_type, "Heures", "Correction"] if self.is_optional 
                   else ["Ref", self.task_type, "Heures", "Correction"])
            
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        if self.is_optional:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.col_offset + 0, QHeaderView.ResizeMode.ResizeToContents)  # Ref
        header.setSectionResizeMode(self.col_offset + 1, QHeaderView.ResizeMode.Stretch)  # Label
        header.setSectionResizeMode(self.col_offset + 2, QHeaderView.ResizeMode.ResizeToContents)  # Heures
        header.setSectionResizeMode(self.col_offset + 3, QHeaderView.ResizeMode.ResizeToContents)  # Correction

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #dcdcdc; }")

    def add_category(self, category_name: str):
        self.categories[category_name] = {
            "task_list": [],
            "total_hours": 0.0
        }

    def add_task(self, category_name: str, ref: int = None, label: str = "", 
                 default_hours: float = 0.0, manual_hours: float = None):
        """Ajoute une tâche à une catégorie."""
        if category_name not in self.categories:
            self.add_category(category_name)
        
        task = {
            "ref": ref,
            "label": label,
            "default_hours": default_hours,
            "manual_hours": manual_hours
        }
        self.categories[category_name]["task_list"].append(task)

    def _add_category_header_row(self, cat_name: str, total_hours: float):
        """Ajoute une ligne d'en-tête pour une catégorie."""
        row = self.rowCount()
        self.insertRow(row)

        font = QFont()
        font.setBold(True)

        # Nom de la catégorie (fusionné sur plusieurs colonnes)
        cat_item = QTableWidgetItem(cat_name)
        cat_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        cat_item.setBackground(QBrush(QColor("#ecf0f1")))
        cat_item.setFont(font)
        self.setItem(row, 0, cat_item)
        self.setSpan(row, 0, 1, self.columnCount() - 2)

        # "Total:"
        total_label_item = QTableWidgetItem("Total:")
        total_label_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_label_item.setBackground(QBrush(QColor("#ecf0f1")))
        total_label_item.setFont(font)
        self.setItem(row, self.columnCount() - 2, total_label_item)

        # Valeur du total
        total_hours_item = QTableWidgetItem(f"{total_hours:.2f}")
        total_hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        total_hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_hours_item.setBackground(QBrush(QColor("#ecf0f1")))
        total_hours_item.setFont(font)
        self.setItem(row, self.columnCount() - 1, total_hours_item)

    def _add_task_row(self, task: Dict, row: int) -> float:
        """Ajoute une ligne de tâche et retourne les heures effectives."""
        self.insertRow(row)

        # Checkbox (si optionnel)
        checkbox = None
        if self.is_optional:
            checkbox = QCheckBox()
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.addWidget(checkbox)
            self.setCellWidget(row, 0, chk_widget)
            checkbox.stateChanged.connect(
                lambda state, ref=task["ref"]: self.checkbox_toggled.emit(state == Qt.CheckState.Checked, ref)
            )

        # Ref
        ref_item = QTableWidgetItem(str(task["ref"]))
        ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, self.col_offset + 0, ref_item)

        # Label
        label_item = QTableWidgetItem(task["label"])
        self.setItem(row, self.col_offset + 1, label_item)

        # Heures par défaut (lecture seule)
        hours_item = QTableWidgetItem(f"{task['default_hours']:.2f}")
        hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(row, self.col_offset + 2, hours_item)

        # Correction manuelle
        line_edit = QLineEdit()
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if task["manual_hours"] is not None:
            line_edit.setText(f"{task['manual_hours']:.2f}")
        line_edit.editingFinished.connect(
            lambda le=line_edit, ref=task["ref"]: self.manual_value_modified.emit(le.text(), ref)
        )
        self.setCellWidget(row, self.col_offset + 3, line_edit)

        # Calculer les heures effectives pour le total
        if not self.is_optional or (checkbox and checkbox.isChecked()):
            return task["manual_hours"] if task["manual_hours"] is not None else task["default_hours"]
        return 0.0

    def show_table(self):
        """Affiche toutes les catégories et leurs tâches."""
        for cat_name, cat_data in self.categories.items():
            total_hours = 0.0
            
            # Ajouter l'en-tête de catégorie
            self._add_category_header_row(cat_name, total_hours)
            
            # Ajouter chaque tâche
            for task in cat_data["task_list"]:
                row = self.rowCount()
                total_hours += self._add_task_row(task, row)
            
            # Mettre à jour le total dans l'en-tête
            header_row = self.rowCount() - len(cat_data["task_list"]) - 1
            total_item = self.item(header_row, self.columnCount() - 1)
            total_item.setText(f"{total_hours:.2f}")

    def adjust_height_to_content(self):
        """Ajuste la hauteur du tableau pour afficher tout le contenu sans scrollbar."""
        total_height = self.horizontalHeader().height() + 2
        for row in range(self.rowCount()):
            total_height += self.rowHeight(row)
        self.setMinimumHeight(total_height)
        self.setMaximumHeight(total_height)

    def refresh(self):
        """Recrée l'affichage du tableau avec les données actuelles."""
        self.clearContents()
        self.setRowCount(0)
        self.show_table()
        self.adjust_height_to_content()

    def update_totals(self):
        """Met à jour uniquement les totaux des catégories sans recréer les widgets."""
        current_row = 0
        for cat_name, cat_data in self.categories.items():
            # current_row est la ligne d'en-tête de la catégorie
            total_hours = 0.0
            
            # Parcourir les lignes de tâches de cette catégorie
            for task_idx, task in enumerate(cat_data["task_list"]):
                task_row = current_row + 1 + task_idx
                
                # Récupérer la valeur manuelle depuis le LineEdit
                line_edit = self.cellWidget(task_row, self.col_offset + 3)
                if isinstance(line_edit, QLineEdit):
                    text = line_edit.text().strip()
                    if text:
                        try:
                            task["manual_hours"] = float(text)
                        except ValueError:
                            task["manual_hours"] = None
                    else:
                        task["manual_hours"] = None
                
                # Vérifier si la tâche est cochée (pour les options)
                is_checked = True
                if self.is_optional:
                    checkbox_widget = self.cellWidget(task_row, 0)
                    if checkbox_widget:
                        checkbox = checkbox_widget.findChild(QCheckBox)
                        is_checked = checkbox.isChecked() if checkbox else False
                
                # Calculer les heures effectives
                if is_checked:
                    hours = task["manual_hours"] if task["manual_hours"] is not None else task["default_hours"]
                    total_hours += hours
            
            # Mettre à jour la cellule du total
            total_item = self.item(current_row, self.columnCount() - 1)
            if total_item:
                total_item.setText(f"{total_hours:.2f}")
            
            # Passer à la catégorie suivante
            current_row += 1 + len(cat_data["task_list"])


class TabTasks(QWidget):
    """Vue principale pour afficher les tableaux de tâches dans un onglet avec scrolling."""
    
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(10, 10, 10, 10)
        self.layout_container.setSpacing(20)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

    def clear(self):
        """Supprime tous les widgets du conteneur."""
        while self.layout_container.count():
            item = self.layout_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_tables(self, tables: List[TaskTableWidget]):
        """Affiche une liste de tables dans le conteneur."""
        self.clear()
        for table in tables:
            if table.label:
                self.layout_container.addWidget(table.label)
            self.layout_container.addWidget(table)
        self.layout_container.addStretch()