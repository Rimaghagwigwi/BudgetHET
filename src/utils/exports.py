from __future__ import annotations
from copy import copy as ccopy
from typing import TYPE_CHECKING, Dict, List, Any

import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Alignment

if TYPE_CHECKING:
    from src.model import Model, Project


# ── Helpers bas-niveau pour la feuille Excel ────────────────────────

def _save_row_style(ws, row_num: int) -> Dict[int, dict]:
    styles = {}
    for col in range(2, 7):
        cell = ws.cell(row=row_num, column=col)
        styles[col] = {
            'font': ccopy(cell.font),
            'fill': ccopy(cell.fill),
            'border': ccopy(cell.border),
            'alignment': ccopy(cell.alignment),
            'number_format': cell.number_format,
        }
    return styles


def _apply_style(ws, row_num: int, style: Dict[int, dict]):
    for col, s in style.items():
        cell = ws.cell(row=row_num, column=col)
        cell.font = s['font']
        cell.fill = s['fill']
        cell.border = s['border']
        cell.alignment = s['alignment']
        cell.number_format = s['number_format']


def _clear_dynamic_zone(ws, start_row: int):
    merges_to_remove = [mc for mc in ws.merged_cells.ranges if mc.min_row >= start_row]
    for mc in merges_to_remove:
        ws.unmerge_cells(str(mc))

    for r in range(start_row, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(row=r, column=c)
            cell.value = None
            cell.font = Font()
            cell.fill = PatternFill()
            cell.border = Border()
            cell.alignment = Alignment()


def _merge_col_b(ws, start: int, end: int, label: str):
    ws.cell(row=start, column=2).value = label
    if end > start:
        ws.merge_cells(start_row=start, start_column=2, end_row=end, end_column=2)


def _auto_hours(task, ctx: dict) -> float:
    saved = task.manual_hours
    task.manual_hours = None
    h = task.effective_hours(ctx)
    task.manual_hours = saved
    return h


# ── Écriture d'une ligne ────────────────────────────────────────────

def _write_hours_cells(ws, row_num: int, auto: float, effective: float, rex: float):
    ws.cell(row=row_num, column=4).value = auto
    if effective != auto:
        ws.cell(row=row_num, column=5).value = effective - auto
    ws.cell(row=row_num, column=6).value = effective * rex


def _write_task_row(ws, row_num: int, task, ctx: dict, rex: float, style):
    _apply_style(ws, row_num, style)
    auto = _auto_hours(task, ctx)
    effective = task.effective_hours(ctx)
    ws.cell(row=row_num, column=3).value = task.label
    _write_hours_cells(ws, row_num, auto, effective, rex)


def _write_group_row(ws, row_num: int, label: str, tasks: list, ctx: dict, rex: float, style):
    _apply_style(ws, row_num, style)
    total_auto = sum(_auto_hours(t, ctx) for t in tasks)
    total_eff = sum(t.effective_hours(ctx) for t in tasks)
    ws.cell(row=row_num, column=3).value = label
    _write_hours_cells(ws, row_num, total_auto, total_eff, rex)


# ── Sections individuelles ──────────────────────────────────────────

def _write_task_section(ws, row: int, tasks: list, section_label: str, ctx: dict, rex: float, style) -> int:
    start = row
    for task in tasks:
        _write_task_row(ws, row, task, ctx, rex, style)
        row += 1
    if row > start:
        _merge_col_b(ws, start, row - 1, section_label)
    return row


def _write_grouped_section(ws, row: int, categories: Dict[str, str], grouped: dict,
                           section_label: str, ctx: dict, rex: float, style,
                           filter_fn=None) -> int:
    start = row
    for cat_code, cat_label in categories.items():
        items = grouped.get(cat_code, [])
        if filter_fn:
            items = filter_fn(items, ctx)
        _write_group_row(ws, row, cat_label, items, ctx, rex, style)
        row += 1
    if row > start:
        _merge_col_b(ws, start, row - 1, section_label)
    return row


def _write_plans_fab(ws, row: int, plans_data: dict, ctx: dict, rex: float, style) -> int:
    for subcat_name, task_list in plans_data.items():
        non_zero = [t for t in task_list if t.effective_hours(ctx) > 0]
        if not non_zero:
            continue
        cat_start = row
        for task in non_zero:
            _write_task_row(ws, row, task, ctx, rex, style)
            row += 1
        _merge_col_b(ws, cat_start, row - 1, f"Plans FAB: {subcat_name}")
    return row


def _write_options(ws, row: int, categories: Dict[str, str], grouped: dict,
                   ctx: dict, rex: float, style) -> int:
    start = row
    for cat_code, cat_label in categories.items():
        selected = [o for o in grouped.get(cat_code, []) if o.is_selected]
        if not selected:
            continue
        _write_group_row(ws, row, cat_label, selected, ctx, rex, style)
        row += 1
    if row > start:
        _merge_col_b(ws, start, row - 1, "Options")
    return row


# ── En-tête projet ──────────────────────────────────────────────────

def _header_fields(project: "Project"):
    secteur_labels = {code: label for das, sectors in project.app_data.secteurs.items() for code, label in sectors.items()}
    product_labels = {code: label for mt, products in project.app_data.product.items() for code, label in products.items()}
    # row, attr, label_map
    return [
        (3,  "crm_number", None),
        (4,  "client", None),
        (5,  "affaire", project.app_data.types_affaires),
        (6,  "das", project.app_data.das),
        (7,  "secteur", secteur_labels),
        (8,  "machine_type", project.app_data.product_types),
        (9,  "product", product_labels),
        (10, "designation", None),
        (11, "quantity", None),
        (12, "revision", None),
        (13, "date", None),
        (14, "created_by", None),
        (15, "validated_by", None),
    ]


def _write_header(ws, project: "Project"):
    for row, attr, label_map in _header_fields(project):
        if label_map:
            value = getattr(project, attr)
            ws[f"C{row}"] = label_map.get(value, value)
        else:
            ws[f"C{row}"] = getattr(project, attr)
    ws["D4"] = project.description


# ── Points d'entrée publics ─────────────────────────────────────────

def export_ortems_excel(project: "Project", path: str):
    repartition = project.make_ortems_repartition()

    template_path = project.app_data.ortems_template_path
    wb = openpyxl.load_workbook(template_path)
    ws_ortems = wb["prepa ORTEMS"]
    col = 3
    job_labels = project.app_data.jobs
    for job, hours in repartition.items():
        ws_ortems.cell(row=1, column=col).value = job_labels.get(job, job)
        ws_ortems.cell(row=2, column=col).value = hours
        col += 1

    delai = project.compute_delai_etude()
    ws_ortems["B2"] = delai["delai_reel"]

    wb.active = ws_ortems
    wb.save(path)


def export_excel_report(project: "Project", path: str):
    template_path = project.app_data.excel_report_template_path
    wb = openpyxl.load_workbook(template_path)
    ws = wb['chiffrage']
    ctx = project.context()
    rex = project.manual_rex_coeff
    app = project.app_data

    # Recalcul des totaux
    project.compute_first_machine_subtotal()
    project.compute_first_machine_total()
    project.compute_n_machines_total()
    project.calculate_total_with_rex()

    _write_header(ws, project)

    # Sauvegarde des styles de référence du template
    ref = {k: _save_row_style(ws, r) for k, r in [
        ('enclenchement', 17), ('calculs', 21), ('plans_fab', 26),
        ('options', 27), ('lpdc', 28), ('labo', 30), ('suivi', 32),
        ('divers', 38), ('machine1', 39), ('total', 40), ('ref_affaire', 41),
    ]}

    _clear_dynamic_zone(ws, start_row=17)

    # ── Sections ──
    row = 17

    enclenchement = project.tasks.get('Gestion de projet', {}).get('Enclenchement', [])
    row = _write_task_section(ws, row, enclenchement, "Enclenchement", ctx, rex, ref['enclenchement'])

    row = _write_grouped_section(
        ws, row, app.calcul_categories, project.grouped_calculs(),
        "Calculs de définition de la machine", ctx, rex, ref['calculs'],
        filter_fn=lambda items, c: [x for x in items if x.is_active(c)],
    )

    plans_data = project.tasks.get("Plans / Specs / LDN", {})
    row = _write_plans_fab(ws, row, plans_data, ctx, rex, ref['plans_fab'])

    row = _write_options(ws, row, app.option_categories, project.grouped_options(), ctx, rex, ref['options'])

    row = _write_grouped_section(
        ws, row, app.lpdc_categories, project.grouped_lpdc(),
        "LPDC", ctx, rex, ref['lpdc'],
        filter_fn=lambda items, c: [d for d in items if d.is_active(c)],
    )

    row = _write_grouped_section(
        ws, row, app.labo_categories, project.grouped_labo(),
        "LABO", ctx, rex, ref['labo'],
        filter_fn=lambda items, c: [l for l in items if l.is_active(c)],
    )

    suivi = project.tasks.get('Gestion de projet', {}).get('Suivi', [])
    row = _write_task_section(ws, row, suivi, "Suivi", ctx, rex, ref['suivi'])

    # Divers
    _apply_style(ws, row, ref['divers'])
    ws.cell(row=row, column=2).value = "DIVERS"
    ws.cell(row=row, column=3).value = "Risques techniques"
    divers_hours = (project.first_machine_subtotal or 0) * project.divers_percent
    ws.cell(row=row, column=4).value = divers_hours
    ws.cell(row=row, column=6).value = divers_hours * rex
    row += 1

    # Machine N°1
    _apply_style(ws, row, ref['machine1'])
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    ws.cell(row=row, column=2).value = "Machine N°1"
    if project.first_machine_total is not None:
        ws.cell(row=row, column=6).value = project.first_machine_total * rex
    row += 1

    # Total N machines
    _apply_style(ws, row, ref['total'])
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    ws.cell(row=row, column=2).value = "TOTAL pour N machines"
    if project.total_with_rex is not None:
        ws.cell(row=row, column=6).value = project.total_with_rex
    row += 1

    # Pied de page
    _apply_style(ws, row, ref['ref_affaire'])
    ws.cell(row=row, column=2).value = "Affaire de référence:"
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
    ws.cell(row=row, column=4).value = "Heures REX"

    wb.save(path)


def quick_export(model: "Model") -> Dict[str, str]:
    prj = model.project
    file_name = f"{prj.crm_number}{prj.revision}"
    excel_path = prj.app_data.quick_export_path
    rapport_path = excel_path + file_name + "_rapport.xlsx"
    ortems_path = excel_path + file_name + "_ortems.xlsx"
    export_excel_report(prj, rapport_path)
    export_ortems_excel(prj, ortems_path)
    return {"rapport": rapport_path, "ortems": ortems_path}