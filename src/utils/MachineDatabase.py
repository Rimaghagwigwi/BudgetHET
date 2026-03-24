import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# ── Noms de colonnes (correspondant aux en-têtes Excel) ──────────────
COL_NUM_PROJET   = "N° Projet"
COL_DATE         = "Date"
COL_NOM_PROJET   = "Nom projet"
COL_NUM_MACHINE  = "N° Machine"
COL_CLIENT       = "Client"
COL_CLIENT_FINAL = "Client final"
COL_DESIGNATION  = "Désignation"
COL_REFERENCE    = "Référence"
COL_NBR_MACHINES = "Nbr machines"
COL_MW           = "MW"
COL_KV           = "KV"
COL_COS_PHI      = "Cos(phi)"
COL_HZ           = "Hz"
COL_TR_MIN       = "TR/MIN"
COL_DAL          = "DAL"
COL_LFER         = "LFER"
COL_NB_POLES     = "NB POLES"
COL_NB_ENCOCHES  = "NB ENCOCHES"
COL_IC           = "IC"
COL_IM           = "IM"
COL_IP           = "IP"
COL_EEX          = "EEX"
COL_TYPE_PRODUIT = "Type produit"
COL_PRODUIT      = "Produit"
COL_TYPE_AFFAIRE = "Type affaire"
COL_DAS          = "DAS"
COL_SECTEUR      = "Secteur"

# ── Catégories de recherche ──────────────────────────────────────────
STRING_FIELDS   = [COL_NUM_PROJET, COL_NOM_PROJET, COL_CLIENT, COL_CLIENT_FINAL, COL_DESIGNATION]
NUMERIC_FIELDS  = [COL_NBR_MACHINES, COL_MW, COL_KV, COL_COS_PHI, COL_HZ,
                   COL_TR_MIN, COL_DAL, COL_LFER, COL_NB_ENCOCHES]
DROPDOWN_FIELDS = [COL_IM, COL_EEX, COL_TYPE_PRODUIT, COL_PRODUIT,
                   COL_TYPE_AFFAIRE, COL_DAS, COL_SECTEUR]
PREFILL_FIELDS  = [COL_TYPE_PRODUIT, COL_PRODUIT, COL_TYPE_AFFAIRE, COL_DAS, COL_SECTEUR]

# Colonnes dont les codes doivent être traduits en labels dans l'affichage
LABEL_MAP_COLUMNS = [COL_TYPE_PRODUIT, COL_PRODUIT, COL_TYPE_AFFAIRE, COL_DAS, COL_SECTEUR]

# Colonne(s) à ne pas afficher dans les résultats
HIDDEN_COLUMNS = ["Heures projet"]


class MachineDatabase:
    """Charge et interroge la base de machines à partir d'un fichier Excel."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df: pd.DataFrame = pd.DataFrame()
        self.unique_values: Dict[str, List[str]] = {}
        self._loaded = False

    # ── Chargement ───────────────────────────────────────────────────
    def load(self) -> bool:
        path = Path(self.filepath)
        if not path.exists():
            print(f"Fichier base machines non trouvé : {self.filepath}")
            return False
        try:
            self.df = pd.read_excel(self.filepath, sheet_name="Machines")
            self._normalize_ip()
            self._extract_unique_values()
            self._loaded = True
            return True
        except Exception as e:
            print(f"Erreur lors du chargement de la base machines : {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded and not self.df.empty

    def _normalize_ip(self):
        """Convertit la colonne IP en chaînes propres ('23', '55', …)."""
        if COL_IP not in self.df.columns:
            return
        def _to_ip_str(v):
            if pd.isna(v):
                return v          # garder NaN
            if isinstance(v, float):
                return str(int(v))
            return str(v).strip()
        self.df[COL_IP] = self.df[COL_IP].apply(_to_ip_str)

    def _extract_unique_values(self):
        """Prépare les listes de valeurs uniques pour les filtres."""
        # Champs dropdown
        for col in DROPDOWN_FIELDS:
            if col in self.df.columns:
                vals = self.df[col].dropna().astype(str).str.strip()
                vals = sorted(vals[vals != ""].unique())
                self.unique_values[col] = vals

        # Années
        if COL_DATE in self.df.columns:
            dates = pd.to_datetime(self.df[COL_DATE], errors="coerce")
            years = dates.dt.year.dropna().astype(int).unique().tolist()
            years.sort(reverse=True)
            self.unique_values[COL_DATE] = [str(y) for y in years]

        # Chiffres IP
        if COL_IP in self.df.columns:
            ips = self.df[COL_IP].dropna().astype(str)
            ips = ips[ips.str.len() >= 2]
            self.unique_values["IP_first"]  = sorted({ip[0] for ip in ips if ip[0].isdigit()})
            self.unique_values["IP_second"] = sorted({ip[1] for ip in ips if ip[1].isdigit()})

    # ── Recherche ────────────────────────────────────────────────────
    def search(self, filters: Dict[str, Any], tolerance_percent: float = 10.0) -> pd.DataFrame:
        """Filtre la base selon *filters*.

        Règle : si une cellule de la base est vide/NaN pour un champ filtré,
        la ligne n'est **pas** exclue (les cases vides sont toujours incluses).
        """
        if self.df.empty:
            return self.df.copy()

        mask = pd.Series(True, index=self.df.index)

        for field, value in filters.items():
            if value is None or (isinstance(value, str) and value.strip() in ("", "Tous")):
                continue

            # Déterminer la colonne réelle
            col = COL_IP if field in ("IP_first", "IP_second") else field
            if col not in self.df.columns:
                continue

            if field in STRING_FIELDS:
                is_empty = self.df[col].isna() | (self.df[col].astype(str).str.strip() == "")
                matches  = self.df[col].astype(str).str.lower().str.contains(
                    str(value).lower(), na=False, regex=False
                )
                mask &= is_empty | matches

            elif field == COL_DATE:
                dates    = pd.to_datetime(self.df[col], errors="coerce")
                is_empty = dates.isna()
                try:
                    matches = dates.dt.year == int(value)
                except (ValueError, TypeError):
                    continue
                mask &= is_empty | matches

            elif field in NUMERIC_FIELDS:
                try:
                    target = float(value)
                except (ValueError, TypeError):
                    continue
                col_num  = pd.to_numeric(self.df[col], errors="coerce")
                is_empty = col_num.isna()
                tol      = abs(target) * tolerance_percent / 100.0
                matches  = (col_num >= target - tol) & (col_num <= target + tol)
                mask &= is_empty | matches

            elif field == COL_NB_POLES:
                col_num  = pd.to_numeric(self.df[col], errors="coerce")
                is_empty = col_num.isna()
                if value == ">4":
                    matches = col_num > 4
                else:
                    try:
                        matches = col_num == int(value)
                    except (ValueError, TypeError):
                        continue
                mask &= is_empty | matches

            elif field == "IP_first":
                if value == "x":
                    continue
                ip_str   = self.df[col].astype(str)
                is_empty = self.df[col].isna() | (ip_str.isin(["", "nan"]))
                matches  = ip_str.str[0] == str(value)
                mask &= is_empty | matches

            elif field == "IP_second":
                if value == "x":
                    continue
                ip_str   = self.df[col].astype(str)
                is_empty = self.df[col].isna() | (ip_str.isin(["", "nan"]))
                matches  = ip_str.str[1] == str(value)
                mask &= is_empty | matches

            elif field in DROPDOWN_FIELDS:
                col_vals = self.df[col].astype(str).str.strip()
                is_empty = self.df[col].isna() | col_vals.isin(["", "nan"])
                matches  = col_vals == str(value)
                mask &= is_empty | matches

        return self.df[mask].reset_index(drop=True)
