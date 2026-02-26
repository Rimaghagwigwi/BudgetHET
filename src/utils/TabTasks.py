from typing import Any, Dict, List, Tuple
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QVBoxLayout, QAbstractItemView, QCheckBox, QLineEdit,
                             QHBoxLayout, QSizePolicy, QWidget, QScrollArea, QFrame)
from src.utils.Task import AbstractTask


class TaskTableWidget(QTableWidget):
    """Widget de tableau générique pour afficher les tâches (Tâches générales, Calculs, Options, LPDC)."""
    
    manual_value_modified = pyqtSignal(str, int)  # (text, ref)
    checkbox_toggled = pyqtSignal(bool, int)  # (is_checked, ref)

    def __init__(self, label: str, task_type: str, is_optional: bool = False):
        super().__init__()
        self.label = QLabel(label) if label else None
        if self.label:
            self.label.setObjectName("important")
        self.task_type = task_type
        self.is_optional = is_optional
        self.col_offset = 1 if is_optional else 0  # Décalage pour la colonne checkbox

        self.context: Dict[str, Any] = {}
        self.categories: Dict[str, List[AbstractTask]] = {}  # category_name -> List[AbstractTask]

        self._setup_table()
        self.adjust_height_to_content()

    def _setup_table(self):
        """Configure les colonnes et le style du tableau."""
        columns = (["Choix", "Ref", self.task_type, "Base", "Heures finales", "Correction"] if self.is_optional 
                   else ["Ref", self.task_type, "Base", "Heures finales", "Correction"])
            
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        if self.is_optional:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.col_offset + 0, QHeaderView.ResizeMode.ResizeToContents)  # Ref
        header.setSectionResizeMode(self.col_offset + 1, QHeaderView.ResizeMode.Stretch)  # Label
        header.setSectionResizeMode(self.col_offset + 2, QHeaderView.ResizeMode.ResizeToContents)  # Heures de base
        header.setSectionResizeMode(self.col_offset + 3, QHeaderView.ResizeMode.ResizeToContents)  # Heures finales
        header.setSectionResizeMode(self.col_offset + 4, QHeaderView.ResizeMode.ResizeToContents)  # Correction

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def add_category(self, category_name: str):
        self.categories[category_name] = []

    def add_task(self, category_name: str, task: AbstractTask):
        """Ajoute une tâche (objet AbstractTask) à une catégorie."""
        if category_name not in self.categories:
            self.add_category(category_name)
        self.categories[category_name].append(task)

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
        self.setSpan(row, 0, 1, self.columnCount() - 1)

        # Valeur du total
        total_hours_item = QTableWidgetItem(f"{total_hours:.2f}")
        total_hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        total_hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_hours_item.setBackground(QBrush(QColor("#ecf0f1")))
        total_hours_item.setFont(font)
        self.setItem(row, self.columnCount() - 1, total_hours_item)

    def _add_task_row(self, task: AbstractTask, row: int) -> float:
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
            if hasattr(task, 'is_selected'):
                checkbox.setChecked(task.is_selected)
            checkbox.checkStateChanged.connect(
                lambda _state, ref=task.index, cb=checkbox: self.checkbox_toggled.emit(cb.isChecked(), ref)
            )

        # Ref
        ref_item = QTableWidgetItem(str(task.index))
        ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, self.col_offset + 0, ref_item)

        # Label
        label_item = QTableWidgetItem(task.label)
        self.setItem(row, self.col_offset + 1, label_item)

        # Heures par défaut (lecture seule)
        default_h = task.default_hours(self.context)
        hours_item = QTableWidgetItem(f"{default_h:.2f}".rstrip("0").rstrip("."))
        hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        hours_item.setForeground(QBrush(QColor("#2980b9")))
        self.setItem(row, self.col_offset + 2, hours_item)

        # Heures finales (lecture seule, mise à jour dynamique)
        final_h = task.effective_hours(self.context)
        final_hours_item = QTableWidgetItem(f"{final_h:.2f}".rstrip("0").rstrip("."))
        final_hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        final_hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(row, self.col_offset + 3, final_hours_item)

        # Correction manuelle
        line_edit = QLineEdit()
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if task.manual_hours is not None:
            line_edit.setText(f"{task.manual_hours:.2f}")
        line_edit.editingFinished.connect(
            lambda le=line_edit, ref=task.index: self.manual_value_modified.emit(le.text(), ref)
        )
        self.setCellWidget(row, self.col_offset + 4, line_edit)

        # Calculer les heures effectives pour le total
        is_checked = not self.is_optional or (checkbox and checkbox.isChecked())
        if is_checked:
            return task.manual_hours if task.manual_hours is not None else default_h
        return 0.0

    def show_table(self):
        """Affiche toutes les catégories et leurs tâches."""
        for cat_name, task_list in self.categories.items():
            total_hours = 0.0
            
            # Ajouter l'en-tête de catégorie
            self._add_category_header_row(cat_name, total_hours)
            
            # Ajouter chaque tâche
            for task in task_list:
                row = self.rowCount()
                total_hours += self._add_task_row(task, row)
            
            # Mettre à jour le total dans l'en-tête
            header_row = self.rowCount() - len(task_list) - 1
            total_item = self.item(header_row, self.columnCount() - 1)
            total_item.setText(f"{total_hours:.2f}".rstrip("0").rstrip("."))

    def _content_height(self) -> int:
        """Calcule la hauteur totale nécessaire pour afficher tout le contenu."""
        h = self.horizontalHeader().height() + 2
        for row in range(self.rowCount()):
            h += self.rowHeight(row)
        return h

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self._content_height())

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def adjust_height_to_content(self):
        """Notifie le layout que la taille a changé."""
        self.updateGeometry()

    @property
    def is_empty(self) -> bool:
        """Retourne True si le tableau ne contient aucune tâche."""
        return not any(self.categories.values())

    def refresh(self):
        """Recrée l'affichage du tableau avec les données actuelles."""
        self.clearContents()
        self.setRowCount(0)
        self.show_table()
        self.adjust_height_to_content()

    @staticmethod
    def _fmt(hours: float) -> str:
        """Formate un nombre d'heures en supprimant les zéros inutiles."""
        return f"{hours:.1f}".rstrip("0").rstrip(".")

    def _sync_manual_hours(self, task: AbstractTask, task_row: int) -> None:
        """Lit le QLineEdit de correction et met à jour task.manual_hours."""
        line_edit = self.cellWidget(task_row, self.col_offset + 4)
        if not isinstance(line_edit, QLineEdit):
            return
        text = line_edit.text().strip()
        if not text:
            task.manual_hours = None
            return
        try:
            task.manual_hours = float(text)
        except ValueError:
            task.manual_hours = None

    def _is_task_checked(self, task_row: int) -> bool:
        """Retourne True si la tâche est active (toujours True pour les tâches non-optionnelles)."""
        if not self.is_optional:
            return True
        checkbox_widget = self.cellWidget(task_row, 0)
        if not checkbox_widget:
            return False
        checkbox = checkbox_widget.findChild(QCheckBox)
        return checkbox.isChecked() if checkbox else False

    def _update_task_row(self, task: AbstractTask, task_row: int) -> float:
        """Met à jour une ligne de tâche et retourne sa contribution au total."""
        default_h = task.default_hours(self.context)

        item_base = self.item(task_row, self.col_offset + 2)
        if item_base:
            item_base.setText(self._fmt(default_h))

        item_final = self.item(task_row, self.col_offset + 3)
        if item_final:
            item_final.setText(self._fmt(task.effective_hours(self.context)))

        self._sync_manual_hours(task, task_row)

        if not self._is_task_checked(task_row):
            return 0.0
        return task.manual_hours if task.manual_hours is not None else default_h

    def _update_category(self, task_list: List[AbstractTask], header_row: int) -> None:
        """Met à jour toutes les lignes d'une catégorie et son total."""
        total_hours = sum(
            self._update_task_row(task, header_row + 1 + idx)
            for idx, task in enumerate(task_list)
        )
        total_item = self.item(header_row, self.columnCount() - 1)
        if total_item:
            total_item.setText(self._fmt(total_hours))

    def update_table(self):
        """Met à jour les heures par défaut et les totaux des catégories sans recréer les widgets."""
        current_row = 0
        for task_list in self.categories.values():
            self._update_category(task_list, current_row)
            current_row += 1 + len(task_list)


class TabTasks(QWidget):
    """Vue principale pour afficher les tableaux de tâches dans un onglet avec scrolling."""
    
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll: QScrollArea = QScrollArea()
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

    def add_global_coefficient(self, label: str, default: float):
        """Ajoute un champ de réglage de coefficient en haut de l'onglet."""
        coefficient_layout = QHBoxLayout()
        coefficient_layout.setContentsMargins(0, 0, 0, 0)

        label_widget = QLabel(label)
        label_widget.setObjectName("important")
        label_widget.setMinimumWidth(250)
        coefficient_layout.addWidget(label_widget)

        line_edit = QLineEdit(f"{default:.1f}")
        line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        coefficient_layout.addWidget(line_edit)

        coefficient_container = QWidget()
        coefficient_container.setLayout(coefficient_layout)
        self.layout_container.insertWidget(0, coefficient_container)
        return line_edit  # Retourne le QLineEdit pour permettre la connexion du signal


    def display_tables(self, tables: List[TaskTableWidget]):
        """Affiche une liste de tables dans le conteneur (les tables vides sont ignorées)."""
        self.clear()
        for table in tables:
            if table.is_empty:
                continue
            if table.label:
                self.layout_container.addWidget(table.label)
            self.layout_container.addWidget(table)
        self.layout_container.addStretch()