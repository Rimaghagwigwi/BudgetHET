import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QToolButton,
    QSizePolicy, QFrame, QScrollArea, QAbstractScrollArea, QScrollBar
)
from PyQt6.QtCore import Qt

from src.model import Model
from src.utils.MachineDatabase import (
    MachineDatabase,
    STRING_FIELDS, NUMERIC_FIELDS, DROPDOWN_FIELDS, PREFILL_FIELDS,
    LABEL_MAP_COLUMNS, HIDDEN_COLUMNS,
    COL_DATE, COL_NB_POLES, COL_IP,
    COL_TYPE_PRODUIT, COL_PRODUIT, COL_TYPE_AFFAIRE, COL_DAS, COL_SECTEUR,
    COL_IM, COL_EEX,
)
from src.utils.widgets import NoWheelSpinBox, NoWheelComboBox


# ─────────────────────────────────────────────────────────────────────
#  Item de tableau triant numériquement quand c'est possible
# ─────────────────────────────────────────────────────────────────────
class _SortableItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            return super().__lt__(other)


# ─────────────────────────────────────────────────────────────────────
#  Section repliable
# ─────────────────────────────────────────────────────────────────────
class _CollapsibleSection(QWidget):
    """Header cliquable + contenu repliable."""
    def __init__(self, title: str, header_widgets=None, parent=None):
        super().__init__(parent)
        self.setObjectName("collapsibleSection")
        self._collapsed = False

        # ── Header ───────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("collapsibleHeader")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(6, 4, 6, 4)
        header_lay.setSpacing(8)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setObjectName("collapseToggle")
        self.toggle_btn.clicked.connect(self._toggle)
        header_lay.addWidget(self.toggle_btn)

        lbl = QLabel(title)
        lbl.setObjectName("collapsibleTitle")
        header_lay.addWidget(lbl)

        header_lay.addStretch()

        if header_widgets:
            for w in header_widgets:
                header_lay.addWidget(w)

        # ── Content ──────────────────────────────────────────────────
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(6)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(header)
        outer.addWidget(self.content)

    def _toggle(self, checked):
        self._collapsed = checked
        self.toggle_btn.setArrowType(
            Qt.ArrowType.RightArrow if checked else Qt.ArrowType.DownArrow
        )
        self.content.setVisible(not checked)

    def addWidget(self, w):
        self.content_layout.addWidget(w)

    def addLayout(self, lay):
        self.content_layout.addLayout(lay)


# =====================================================================
#  VUE
# =====================================================================
class TabMachineSearch(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("tabMachineSearch")

        # Scroll vertical global de l'onglet
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll_area)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        scroll_area.setWidget(container)

        # ── Boutons dans le header de la section ─────────────────────
        self.btn_search = QPushButton("Rechercher")
        self.btn_search.setObjectName("searchBtn")
        self.btn_reset = QPushButton("Réinitialiser")
        self.btn_reset.setObjectName("resetBtn")

        section = _CollapsibleSection(
            "Recherche", header_widgets=[self.btn_search, self.btn_reset]
        )

        # 1) Recherche textuelle ──────────────────────────────────────
        text_group = QGroupBox("Recherche par texte (contient)")
        text_grid = QGridLayout()
        text_grid.setSpacing(4)
        self.string_inputs = {}
        for i, field in enumerate(STRING_FIELDS):
            col = i % 3
            row = (i // 3) * 2
            text_grid.addWidget(QLabel(field), row, col)
            inp = QLineEdit()
            inp.setPlaceholderText("Rechercher…")
            self.string_inputs[field] = inp
            text_grid.addWidget(inp, row + 1, col)
        text_group.setLayout(text_grid)
        section.addWidget(text_group)

        # 2) Filtres de sélection ─────────────────────────────────────
        select_group = QGroupBox("Filtres de sélection")
        select_grid = QGridLayout()
        select_grid.setSpacing(4)

        col_idx, row_idx = 0, 0

        # Année
        select_grid.addWidget(QLabel("Année :"), row_idx, col_idx)
        self.combo_date = NoWheelComboBox()
        select_grid.addWidget(self.combo_date, row_idx + 1, col_idx)
        col_idx += 1

        # NB POLES
        select_grid.addWidget(QLabel("NB POLES :"), row_idx, col_idx)
        self.combo_nb_poles = NoWheelComboBox()
        self.combo_nb_poles.addItems(["Tous", "2", "4", ">4"])
        select_grid.addWidget(self.combo_nb_poles, row_idx + 1, col_idx)
        col_idx += 1

        # IP (deux listes déroulantes)
        select_grid.addWidget(QLabel("IP :"), row_idx, col_idx)
        ip_w = QWidget()
        ip_lay = QHBoxLayout(ip_w)
        ip_lay.setContentsMargins(0, 0, 0, 0)
        self.combo_ip_first = NoWheelComboBox()
        self.combo_ip_second = NoWheelComboBox()
        ip_lay.addWidget(self.combo_ip_first)
        ip_lay.addWidget(self.combo_ip_second)
        select_grid.addWidget(ip_w, row_idx + 1, col_idx)
        col_idx += 1

        # Tous les champs dropdown
        self.dropdown_inputs = {}
        for field in DROPDOWN_FIELDS:
            if col_idx >= 4:
                col_idx = 0
                row_idx += 2
            select_grid.addWidget(QLabel(field + " :"), row_idx, col_idx)
            combo = NoWheelComboBox()
            self.dropdown_inputs[field] = combo
            select_grid.addWidget(combo, row_idx + 1, col_idx)
            col_idx += 1

        select_group.setLayout(select_grid)
        section.addWidget(select_group)

        # 3) Valeurs numériques ───────────────────────────────────────
        num_group = QGroupBox("Valeurs numériques (± tolérance)")
        num_vbox = QVBoxLayout()

        tol_lay = QHBoxLayout()
        tol_lay.addWidget(QLabel("Tolérance :"))
        self.spin_tolerance = NoWheelSpinBox()
        self.spin_tolerance.setRange(5, 100)
        self.spin_tolerance.setValue(10)
        self.spin_tolerance.setSuffix(" %")
        self.spin_tolerance.setSingleStep(5)
        tol_lay.addWidget(self.spin_tolerance)
        tol_lay.addStretch()
        num_vbox.addLayout(tol_lay)

        num_grid = QGridLayout()
        num_grid.setSpacing(4)
        self.numeric_inputs = {}
        for i, field in enumerate(NUMERIC_FIELDS):
            col = i % 5
            row = (i // 5) * 2
            num_grid.addWidget(QLabel(field), row, col)
            inp = QLineEdit()
            inp.setPlaceholderText("—")
            self.numeric_inputs[field] = inp
            num_grid.addWidget(inp, row + 1, col)
        num_vbox.addLayout(num_grid)
        num_group.setLayout(num_vbox)
        section.addWidget(num_group)

        main_layout.addWidget(section)

        # ── Label résultats ──────────────────────────────────────────
        self.label_count = QLabel("")
        self.label_count.setObjectName("important")
        main_layout.addWidget(self.label_count)

        # ── Tableau de résultats ─────────────────────────────────────
        self.table_results = QTableWidget()
        self.table_results.setObjectName("machineResults")
        self.table_results.setAlternatingRowColors(True)
        self.table_results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_results.horizontalHeader().setStretchLastSection(False)
        self.table_results.horizontalHeader().setSectionsClickable(True)
        self.table_results.setSortingEnabled(True)
        # Pas de scrollbars internes : vertical géré par la scroll area,
        # horizontal géré par la scrollbar externe ci-dessous
        self.table_results.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_results.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )

        main_layout.addWidget(self.table_results)

        # ── Scrollbar horizontale externe (fixée en bas, hors scroll area) ──
        self.hscroll = QScrollBar(Qt.Orientation.Horizontal)
        self.hscroll.setVisible(False)
        outer.addWidget(self.hscroll)

        # Synchronisation bidirectionnelle avec la scrollbar interne du tableau
        table_hbar = self.table_results.horizontalScrollBar()
        self.hscroll.valueChanged.connect(table_hbar.setValue)
        table_hbar.valueChanged.connect(self.hscroll.setValue)
        table_hbar.rangeChanged.connect(self._sync_hscroll_range)

        # Raccourci : Entrée dans un champ → lancer la recherche
        for inp in list(self.string_inputs.values()) + list(self.numeric_inputs.values()):
            inp.returnPressed.connect(self.btn_search.click)

    def _sync_hscroll_range(self, min_val, max_val):
        """Met à jour la scrollbar externe quand le contenu du tableau change."""
        self.hscroll.setRange(min_val, max_val)
        self.hscroll.setPageStep(self.table_results.horizontalScrollBar().pageStep())
        self.hscroll.setSingleStep(self.table_results.horizontalScrollBar().singleStep())
        self.hscroll.setVisible(max_val > 0)

    # ── Helpers de remplissage ───────────────────────────────────────
    def populate_combo(self, combo: QComboBox, values: list, add_all: bool = True):
        combo.clear()
        if add_all:
            combo.addItem("Tous")
        combo.addItems([str(v) for v in values])

    def populate_combo_with_labels(self, combo: QComboBox, items: dict, add_all: bool = True):
        """Remplit un combo avec des labels affichés et des codes stockés comme données."""
        combo.blockSignals(True)
        combo.clear()
        if add_all:
            combo.addItem("Tous", None)
        for code, label in items.items():
            combo.addItem(label, code)
        combo.blockSignals(False)

    def populate_ip_combos(self, first_digits: list, second_digits: list):
        self.combo_ip_first.clear()
        self.combo_ip_first.addItem("x")
        self.combo_ip_first.addItems(first_digits)
        self.combo_ip_second.clear()
        self.combo_ip_second.addItem("x")
        self.combo_ip_second.addItems(second_digits)

    # ── Affichage des résultats ──────────────────────────────────────
    def set_results(self, df: pd.DataFrame, label_maps: dict = None):
        """Affiche les résultats. label_maps: dict[col_name → dict[code → label]]."""
        self.table_results.setSortingEnabled(False)
        self.table_results.clear()

        if df.empty:
            self.table_results.setRowCount(0)
            self.table_results.setColumnCount(0)
            self.label_count.setText("Aucun résultat")
            return

        # Retirer les colonnes masquées
        display_df = df.drop(columns=[c for c in HIDDEN_COLUMNS if c in df.columns], errors="ignore")

        if label_maps:
            for col, mapping in label_maps.items():
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda v, m=mapping: m.get(str(v).strip(), v) if pd.notna(v) else v
                    )

        columns = list(display_df.columns)
        self.table_results.setColumnCount(len(columns))
        self.table_results.setHorizontalHeaderLabels(columns)
        self.table_results.setRowCount(len(display_df))

        for row_idx in range(len(display_df)):
            for col_idx, col_name in enumerate(columns):
                value = display_df.iloc[row_idx, col_idx]

                # Formatage propre
                if pd.isna(value):
                    text = ""
                elif isinstance(value, pd.Timestamp):
                    text = value.strftime("%d/%m/%Y")
                elif isinstance(value, float):
                    text = str(int(value)) if value == int(value) else f"{value:.4g}"
                else:
                    text = str(value)

                item = _SortableItem(text)
                self.table_results.setItem(row_idx, col_idx, item)

        self.table_results.resizeColumnsToContents()
        self.table_results.setSortingEnabled(True)
        self._fit_table_height()
        self.label_count.setText(f"{len(display_df)} machine(s) trouvée(s)")

    def _fit_table_height(self):
        """Force la hauteur du tableau à sa taille naturelle pour éviter le scroll interne vertical."""
        t = self.table_results
        h = t.horizontalHeader().height() + 4  # header + border
        for i in range(t.rowCount()):
            h += t.rowHeight(i)
        # +20 pour la scrollbar horizontale toujours visible
        h += t.horizontalScrollBar().sizeHint().height()
        t.setMinimumHeight(h)
        t.setMaximumHeight(h)

    # ── Collecte des filtres ─────────────────────────────────────────
    def get_all_filters(self) -> dict:
        filters = {}

        for field, w in self.string_inputs.items():
            t = w.text().strip()
            if t:
                filters[field] = t

        if self.combo_date.currentText() != "Tous":
            filters[COL_DATE] = self.combo_date.currentText()

        if self.combo_nb_poles.currentText() != "Tous":
            filters[COL_NB_POLES] = self.combo_nb_poles.currentText()

        ip1 = self.combo_ip_first.currentText()
        ip2 = self.combo_ip_second.currentText()
        if ip1 != "x":
            filters["IP_first"] = ip1
        if ip2 != "x":
            filters["IP_second"] = ip2

        for field, combo in self.dropdown_inputs.items():
            if field in LABEL_MAP_COLUMNS:
                code = combo.currentData()
                if code is not None:
                    filters[field] = code
            else:
                val = combo.currentText()
                if val and val != "Tous":
                    filters[field] = val

        for field, w in self.numeric_inputs.items():
            t = w.text().strip()
            if t:
                try:
                    float(t)
                    filters[field] = t
                except ValueError:
                    pass

        return filters

    def get_tolerance(self) -> float:
        return self.spin_tolerance.value()

    def reset_filters(self):
        for w in self.string_inputs.values():
            w.clear()
        for w in self.numeric_inputs.values():
            w.clear()
        self.combo_date.setCurrentIndex(0)
        self.combo_nb_poles.setCurrentIndex(0)
        if self.combo_ip_first.count():
            self.combo_ip_first.setCurrentIndex(0)
        if self.combo_ip_second.count():
            self.combo_ip_second.setCurrentIndex(0)
        for combo in self.dropdown_inputs.values():
            combo.setCurrentIndex(0)
        self.spin_tolerance.setValue(10)


# =====================================================================
#  CONTRÔLEUR
# =====================================================================
class MachineSearchController:
    def __init__(self, model: Model, view: TabMachineSearch):
        self.model = model
        self.view = view
        self.db = MachineDatabase(model.app_data.rex_database_path)

        self.db.load()
        self._populate_filters()

        # Signaux
        self.view.btn_search.clicked.connect(self._on_search)
        self.view.btn_reset.clicked.connect(self._on_reset)
        self.model.project_changed.connect(self._on_project_changed)

        # Filtrage dynamique des combos dépendants
        self.view.dropdown_inputs[COL_TYPE_PRODUIT].currentIndexChanged.connect(
            self._update_produit_combo)
        self.view.dropdown_inputs[COL_DAS].currentIndexChanged.connect(
            self._update_secteur_combo)

    # ── Peuplement des combos ────────────────────────────────────────
    def _populate_filters(self):
        ad = self.model.app_data

        # Années, IP (depuis la base de données)
        if self.db.is_loaded:
            self.view.populate_combo(
                self.view.combo_date,
                self.db.unique_values.get(COL_DATE, []),
            )
            self.view.populate_ip_combos(
                self.db.unique_values.get("IP_first", []),
                self.db.unique_values.get("IP_second", []),
            )
            # IM, EEX : valeurs brutes de la base
            for field in (COL_IM, COL_EEX):
                combo = self.view.dropdown_inputs.get(field)
                if combo:
                    self.view.populate_combo(combo, self.db.unique_values.get(field, []))

        # Champs avec labels (depuis app_data)
        self.view.populate_combo_with_labels(
            self.view.dropdown_inputs[COL_TYPE_PRODUIT], ad.product_types)
        self.view.populate_combo_with_labels(
            self.view.dropdown_inputs[COL_TYPE_AFFAIRE], ad.types_affaires)
        self.view.populate_combo_with_labels(
            self.view.dropdown_inputs[COL_DAS], ad.das)

        # Produit et Secteur : peuplés dynamiquement selon Type produit et DAS
        self._update_produit_combo()
        self._update_secteur_combo()

    # ── Recherche ────────────────────────────────────────────────────
    def _on_search(self):
        if not self.db.is_loaded:
            self.view.label_count.setText("Base de données non chargée")
            return
        filters   = self.view.get_all_filters()
        tolerance = self.view.get_tolerance()
        results   = self.db.search(filters, tolerance)
        self.view.set_results(results, self._build_label_maps())

    def _build_label_maps(self) -> dict:
        """Construit les mappings code → label pour les colonnes à traduire."""
        ad = self.model.app_data
        maps = {}

        # Type produit : code → label (ex: "SYNCH" → "Synchrone")
        if ad.product_types:
            maps["Type produit"] = dict(ad.product_types)

        # Produit : flatten all product dicts
        all_products = {}
        for cat_products in ad.product.values():
            all_products.update(cat_products)
        if all_products:
            maps["Produit"] = all_products

        # Type affaire
        if ad.types_affaires:
            maps["Type affaire"] = dict(ad.types_affaires)

        # DAS
        if ad.das:
            maps["DAS"] = dict(ad.das)

        # Secteur : flatten all sector dicts
        all_secteurs = {}
        for das_secteurs in ad.secteurs.values():
            all_secteurs.update(das_secteurs)
        if all_secteurs:
            maps["Secteur"] = all_secteurs

        return maps

    def _on_reset(self):
        self.view.reset_filters()
        self._prefill_from_project()
        self.view.table_results.setRowCount(0)
        self.view.table_results.setColumnCount(0)
        self.view.label_count.setText("")

    # ── Filtrage dynamique des combos dépendants ─────────────────────
    def _update_produit_combo(self):
        """Met à jour la liste des produits selon le type de produit sélectionné."""
        ad = self.model.app_data
        type_code = self.view.dropdown_inputs[COL_TYPE_PRODUIT].currentData()
        if type_code:
            products = ad.product.get(type_code, {})
        else:
            products = {c: l for prods in ad.product.values() for c, l in prods.items()}
        self.view.populate_combo_with_labels(
            self.view.dropdown_inputs[COL_PRODUIT], products)

    def _update_secteur_combo(self):
        """Met à jour la liste des secteurs selon le DAS sélectionné."""
        ad = self.model.app_data
        das_code = self.view.dropdown_inputs[COL_DAS].currentData()
        if das_code:
            secteurs = ad.secteurs.get(das_code, {})
        else:
            secteurs = {c: l for sects in ad.secteurs.values() for c, l in sects.items()}
        self.view.populate_combo_with_labels(
            self.view.dropdown_inputs[COL_SECTEUR], secteurs)

    # ── Pré-remplissage depuis le projet ─────────────────────────────
    def _on_project_changed(self):
        self._prefill_from_project()

    def _prefill_from_project(self):
        """Pré-remplit Type produit, Produit et DAS depuis le projet courant."""
        prj = self.model.project

        # Ordre important : Type produit avant Produit (déclenche le filtrage dynamique)
        for field, code in [
            (COL_TYPE_PRODUIT, prj.machine_type),
            (COL_PRODUIT, prj.product),
            (COL_DAS, prj.das),
        ]:
            combo = self.view.dropdown_inputs.get(field)
            if not combo or not code:
                continue
            for i in range(combo.count()):
                if combo.itemData(i) == code:
                    combo.setCurrentIndex(i)
                    break
