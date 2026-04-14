from typing import Any, Dict, List, Optional, Tuple
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QVBoxLayout, QAbstractItemView, QCheckBox, QLineEdit,
                             QHBoxLayout, QSizePolicy, QWidget, QScrollArea, QFrame)
from src.utils.Task import AbstractTask


class TaskTableWidget(QTableWidget):
    """Widget de tableau unifié : chaque ligne a une checkbox (grisée si obligatoire, active si optionnelle)."""
    
    manual_value_modified = pyqtSignal(str, int)  # (text, ref)
    checkbox_toggled = pyqtSignal(bool, int)  # (is_checked, ref)
    category_correction_modified = pyqtSignal(str, str)  # (category_name, text)

    COL_OFFSET = 1  # La colonne 0 est toujours la checkbox "Choix"

    def __init__(self, label: str, task_type: str):
        super().__init__()
        self.label = QLabel(label) if label else None
        if self.label:
            self.label.setObjectName("important")
        self.task_type = task_type

        self.context: Dict[str, Any] = {}
        # category_name -> List[(task, mandatory)]
        self.categories: Dict[str, List[Tuple[AbstractTask, bool]]] = {}
        self.category_corrections: Dict[str, Optional[float]] = {}

        # Collapsible state
        self._collapsed: Dict[str, bool] = {}
        self._category_header_rows: Dict[str, int] = {}
        self._category_task_counts: Dict[str, int] = {}

        self._setup_table()
        self.cellClicked.connect(self._on_cell_clicked)
        self.adjust_height_to_content()

    def _setup_table(self):
        """Configure les colonnes et le style du tableau."""
        columns = ["Choix", "Ref", self.task_type, "Base", "Heures finales", "Correction"]
            
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)   # Choix
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)   # Ref
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)            # Label
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)   # Base
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)   # Heures finales
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)   # Correction

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def add_category(self, category_name: str):
        self.categories[category_name] = []

    def collapse_all(self):
        """Marque toutes les catégories comme repliées (à appeler avant show_table)."""
        for cat_name in self.categories:
            self._collapsed[cat_name] = True

    def add_task(self, category_name: str, task: AbstractTask, mandatory: bool = True):
        """Ajoute une tâche à une catégorie. mandatory=True → checkbox grisée, False → checkbox active."""
        if category_name not in self.categories:
            self.add_category(category_name)
        self.categories[category_name].append((task, mandatory))

    def _sorted_tasks(self, task_list: List[Tuple[AbstractTask, bool]]) -> List[Tuple[AbstractTask, bool]]:
        """Trie les tâches : obligatoires d'abord, optionnelles ensuite."""
        return sorted(task_list, key=lambda t: (not t[1], t[0].index))

    def _add_category_header_row(self, cat_name: str, total_hours: float):
        """Ajoute une ligne d'en-tête pour une catégorie (cliquable pour replier/déplier)."""
        row = self.rowCount()
        self.insertRow(row)

        font = QFont()
        font.setBold(True)
        bg = QBrush(QColor("#ecf0f1"))

        # Indicateur replié/déplié
        is_collapsed = self._collapsed.get(cat_name, False)
        indicator = "▶" if is_collapsed else "▼"

        # Nom de la catégorie (colonnes 0..3 : Choix, Ref, Label, Base)
        cat_item = QTableWidgetItem(f"{indicator} {cat_name}")
        cat_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        cat_item.setBackground(bg)
        cat_item.setFont(font)
        self.setItem(row, 0, cat_item)
        self.setSpan(row, 0, 1, self.COL_OFFSET + 3)  # colonnes 0-3

        # Total dans "Heures finales" (colonne 4)
        total_hours_item = QTableWidgetItem(f"{total_hours:.2f}")
        total_hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        total_hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_hours_item.setBackground(bg)
        total_hours_item.setFont(font)
        self.setItem(row, self.COL_OFFSET + 3, total_hours_item)

        # Correction de catégorie (colonne 5)
        line_edit = QLineEdit()
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        correction = self.category_corrections.get(cat_name)
        if correction is not None:
            line_edit.setText(f"{correction:.2f}")
        line_edit.editingFinished.connect(
            lambda le=line_edit, cn=cat_name: self._on_category_correction_input(cn, le.text())
        )
        self.setCellWidget(row, self.COL_OFFSET + 4, line_edit)

    def _add_task_row(self, task: AbstractTask, row: int, mandatory: bool) -> float:
        """Ajoute une ligne de tâche et retourne les heures effectives."""
        self.insertRow(row)
        off = self.COL_OFFSET

        if mandatory:
            # Pas de checkbox, cellule grisée
            empty_item = QTableWidgetItem()
            empty_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            empty_item.setBackground(QBrush(QColor("#ecf0f1")))
            self.setItem(row, 0, empty_item)
        else:
            # Checkbox sur fond blanc
            checkbox = QCheckBox()
            chk_widget = QWidget()
            chk_widget.setObjectName("optionalCheckboxCell")
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
        self.setItem(row, off + 0, ref_item)

        # Label
        label_item = QTableWidgetItem(task.label)
        self.setItem(row, off + 1, label_item)

        # Heures par défaut (lecture seule)
        default_h = task.default_hours(self.context)
        hours_item = QTableWidgetItem(f"{default_h:.2f}".rstrip("0").rstrip("."))
        hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        hours_item.setForeground(QBrush(QColor("#0063AF")))
        self.setItem(row, off + 2, hours_item)

        # Heures finales (lecture seule, mise à jour dynamique)
        final_h = task.effective_hours(self.context)
        final_hours_item = QTableWidgetItem(f"{final_h:.2f}".rstrip("0").rstrip("."))
        final_hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        final_hours_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(row, off + 3, final_hours_item)

        # Correction manuelle
        line_edit = QLineEdit()
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if task.manual_hours is not None:
            line_edit.setText(f"{task.manual_hours:.2f}")
        line_edit.editingFinished.connect(
            lambda le=line_edit, ref=task.index: self.manual_value_modified.emit(le.text(), ref)
        )
        self.setCellWidget(row, off + 4, line_edit)

        return task.effective_hours(self.context)

    def show_table(self):
        """Affiche toutes les catégories et leurs tâches (obligatoires d'abord, puis optionnelles)."""
        self._category_header_rows.clear()
        self._category_task_counts.clear()

        for cat_name, task_list in self.categories.items():
            sorted_tasks = self._sorted_tasks(task_list)
            total_hours = 0.0
            
            self._add_category_header_row(cat_name, total_hours)
            header_row = self.rowCount() - 1
            self._category_header_rows[cat_name] = header_row
            self._category_task_counts[cat_name] = len(sorted_tasks)
            
            for task, mandatory in sorted_tasks:
                row = self.rowCount()
                total_hours += self._add_task_row(task, row, mandatory)

            correction = self.category_corrections.get(cat_name)
            display = correction if correction is not None else total_hours
            total_item = self.item(header_row, self.COL_OFFSET + 3)
            total_item.setText(f"{display:.2f}".rstrip("0").rstrip("."))

            if correction is not None:
                self._set_task_corrections_enabled(header_row, len(sorted_tasks), False)

            # Appliquer l'état replié
            is_collapsed = self._collapsed.get(cat_name, False)
            if is_collapsed:
                for i in range(len(sorted_tasks)):
                    self.setRowHidden(header_row + 1 + i, True)

    def _content_height(self) -> int:
        """Calcule la hauteur totale nécessaire pour afficher tout le contenu."""
        h = self.horizontalHeader().height() + 2
        for row in range(self.rowCount()):
            if not self.isRowHidden(row):
                h += self.rowHeight(row)
        return h

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self._content_height())

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def adjust_height_to_content(self):
        """Notifie le layout que la taille a changé."""
        self.updateGeometry()

    def _on_cell_clicked(self, row: int, _col: int):
        """Détecte un clic sur une ligne d'en-tête de catégorie pour replier/déplier."""
        for cat_name, header_row in self._category_header_rows.items():
            if row == header_row:
                self._toggle_category(cat_name)
                break

    def _toggle_category(self, cat_name: str):
        """Replie ou déplie une catégorie."""
        is_collapsed = self._collapsed.get(cat_name, False)
        self._collapsed[cat_name] = not is_collapsed
        header_row = self._category_header_rows[cat_name]
        task_count = self._category_task_counts[cat_name]

        # Masquer/afficher les lignes de tâches
        for i in range(task_count):
            self.setRowHidden(header_row + 1 + i, not is_collapsed)

        # Mettre à jour l'indicateur
        indicator = "▶" if not is_collapsed else "▼"
        item = self.item(header_row, 0)
        if item:
            text = item.text()
            if text.startswith("▶ ") or text.startswith("▼ "):
                text = text[2:]
            item.setText(f"{indicator} {text}")

        self.adjust_height_to_content()

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
        line_edit = self.cellWidget(task_row, self.COL_OFFSET + 4)
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
        """Retourne True si la checkbox est cochée, ou True si ligne obligatoire (pas de checkbox)."""
        checkbox_widget = self.cellWidget(task_row, 0)
        if not checkbox_widget:
            return True  # Ligne obligatoire, pas de checkbox → toujours active
        checkbox = checkbox_widget.findChild(QCheckBox)
        return checkbox.isChecked() if checkbox else False

    def _on_category_correction_input(self, cat_name: str, text: str):
        """Gère la saisie d'une correction de catégorie."""
        text = text.strip()
        if text:
            try:
                self.category_corrections[cat_name] = float(text)
            except ValueError:
                self.category_corrections[cat_name] = None
        else:
            self.category_corrections[cat_name] = None

        # Émettre le signal pour que le contrôleur persiste et recalcule
        self.category_correction_modified.emit(cat_name, text)

    def _set_task_corrections_enabled(self, header_row: int, task_count: int, enabled: bool):
        """Active/désactive les corrections individuelles des tâches d'une catégorie."""
        col = self.COL_OFFSET + 4
        for idx in range(task_count):
            task_row = header_row + 1 + idx
            if not enabled:
                # Remplacer le QLineEdit par une cellule grisée
                self.removeCellWidget(task_row, col)
                gray_item = QTableWidgetItem()
                gray_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                gray_item.setBackground(QBrush(QColor("#ecf0f1")))
                self.setItem(task_row, col, gray_item)
            else:
                # Restaurer le QLineEdit si absent
                existing = self.cellWidget(task_row, col)
                if not isinstance(existing, QLineEdit):
                    line_edit = QLineEdit()
                    line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setCellWidget(task_row, col, line_edit)

    def _update_task_row(self, task: AbstractTask, task_row: int) -> float:
        """Met à jour une ligne de tâche et retourne sa contribution au total."""
        off = self.COL_OFFSET
        default_h = task.default_hours(self.context)

        item_base = self.item(task_row, off + 2)
        if item_base:
            item_base.setText(self._fmt(default_h))

        item_final = self.item(task_row, off + 3)
        if item_final:
            item_final.setText(self._fmt(task.effective_hours(self.context)))

        self._sync_manual_hours(task, task_row)

        return task.effective_hours(self.context)

    def _update_category(self, cat_name: str, task_list: List[Tuple[AbstractTask, bool]], header_row: int) -> None:
        """Met à jour toutes les lignes d'une catégorie et son total."""
        sorted_tasks = self._sorted_tasks(task_list)
        total_hours = sum(
            self._update_task_row(task, header_row + 1 + idx)
            for idx, (task, _mandatory) in enumerate(sorted_tasks)
        )

        correction = self.category_corrections.get(cat_name)
        display = correction if correction is not None else total_hours

        total_item = self.item(header_row, self.COL_OFFSET + 3)
        if total_item:
            total_item.setText(self._fmt(display))

    def update_table(self):
        """Met à jour les heures par défaut et les totaux des catégories sans recréer les widgets."""
        current_row = 0
        for cat_name, task_list in self.categories.items():
            self._update_category(cat_name, task_list, current_row)
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