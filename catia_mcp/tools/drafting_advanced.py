"""Advanced Drafting tools — section views, detail views, BOM, GD&T, auto dimensions."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import get_catia, get_active_document

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_drawing_doc():
    doc = get_active_document()
    doc_type = getattr(doc, "Type", "Unknown")
    if doc_type not in ("Drawing", "CATDrawing"):
        try:
            name = doc.Name
            if not name.upper().endswith(".CATDRAWING"):
                raise RuntimeError(f"Active document is not a Drawing (type={doc_type}).")
        except Exception:
            raise RuntimeError(f"Active document is not a Drawing (type={doc_type}).")
    return doc


def _get_active_sheet(doc):
    sheets = doc.Sheets
    return sheets.ActiveSheet


def _get_view_by_name(sheet, view_name: str):
    views = sheet.Views
    for i in range(1, views.Count + 1):
        v = views.Item(i)
        if v.Name == view_name:
            return v
    raise RuntimeError(f"View '{view_name}' not found on active sheet.")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def create_section_view(
    parent_view_name: str,
    x: float,
    y: float,
    section_x1: float,
    section_y1: float,
    section_x2: float,
    section_y2: float,
    scale: float = 1.0,
    name: str = "SectionView",
    section_type: str = "Arrow",
    side_to_draw: int = 1,
) -> dict[str, Any]:
    """Create a section view from a parent view.

    Args:
        parent_view_name: Name of the parent view to section.
        x, y: Position of the new section view on the sheet.
        section_x1, section_y1, section_x2, section_y2: Section line coordinates in parent view space.
        scale: View scale.
        name: New view name.
        section_type: Section type string (e.g., "Arrow", "Offset").
        side_to_draw: 1 or -1 indicating which side to keep.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)

    parent_view = _get_view_by_name(sheet, parent_view_name)
    views = sheet.Views
    new_view = views.Add(name)
    new_view.x = float(x)
    new_view.y = float(y)
    new_view.Scale = float(scale)

    gen_behavior = new_view.GenerativeBehavior
    parent_gen = parent_view.GenerativeBehavior

    profile = (float(section_x1), float(section_y1), float(section_x2), float(section_y2))
    gen_behavior.DefineSectionView(profile, section_type, "Line", int(side_to_draw), parent_gen)

    doc.Update()
    return {"feature": "SectionView", "name": name, "parent": parent_view_name}


def create_detail_view(
    parent_view_name: str,
    x: float,
    y: float,
    center_x: float,
    center_y: float,
    radius: float = 10.0,
    scale: float = 2.0,
    name: str = "DetailView",
) -> dict[str, Any]:
    """Create a circular detail view from a parent view.

    Args:
        parent_view_name: Name of the parent view.
        x, y: Position of the detail view on the sheet.
        center_x, center_y: Center of the detail circle in parent view space.
        radius: Detail circle radius.
        scale: View scale.
        name: New view name.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)

    parent_view = _get_view_by_name(sheet, parent_view_name)
    views = sheet.Views
    new_view = views.Add(name)
    new_view.x = float(x)
    new_view.y = float(y)
    new_view.Scale = float(scale)

    gen_behavior = new_view.GenerativeBehavior
    parent_gen = parent_view.GenerativeBehavior

    gen_behavior.DefineCircularDetailView(float(center_x), float(center_y), float(radius), parent_gen)

    doc.Update()
    return {"feature": "DetailView", "name": name, "parent": parent_view_name}


def create_isometric_view(
    parent_view_name: str,
    x: float,
    y: float,
    scale: float = 1.0,
    name: str = "IsometricView",
) -> dict[str, Any]:
    """Create an isometric view from a parent view.

    Args:
        parent_view_name: Name of the parent view.
        x, y: Position on the sheet.
        scale: View scale.
        name: New view name.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)

    parent_view = _get_view_by_name(sheet, parent_view_name)
    views = sheet.Views
    new_view = views.Add(name)
    new_view.x = float(x)
    new_view.y = float(y)
    new_view.Scale = float(scale)

    gen_behavior = new_view.GenerativeBehavior
    gen_behavior.DefineIsometricView(1.0, 1.0, 1.0, 0.0, 1.0, 0.0)

    doc.Update()
    return {"feature": "IsometricView", "name": name, "parent": parent_view_name}


def create_broken_view(
    view_name: str,
    break_x1: float,
    break_y1: float,
    break_x2: float,
    break_y2: float,
    gap: float = 5.0,
    orientation: str = "horizontal",
) -> dict[str, Any]:
    """Create a broken view on an existing view.

    Args:
        view_name: View to break.
        break_x1, break_y1, break_x2, break_y2: Break line coordinates.
        gap: Gap between broken sections.
        orientation: "horizontal" or "vertical".
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)
    view = _get_view_by_name(sheet, view_name)

    gen_behavior = view.GenerativeBehavior
    lines = (float(break_x1), float(break_y1), float(break_x2), float(break_y2))
    dir_x = 1.0 if orientation.lower() == "horizontal" else 0.0
    dir_y = 0.0 if orientation.lower() == "horizontal" else 1.0

    try:
        gen_behavior.DefineBrokenView(lines, dir_x, dir_y)
    except Exception as exc:
        raise RuntimeError(
            f"Broken view creation failed: {exc}. "
            "Broken view may require a specific view type or is not supported via COM in this CATIA locale."
        ) from exc

    doc.Update()
    return {"feature": "BrokenView", "name": view_name}


def generate_dimensions() -> dict[str, Any]:
    """Generate dimensions automatically on the active drawing sheet.

    Uses the DrawingSheet.GenerateDimensions method.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)

    try:
        sheet.GenerateDimensions()
    except Exception as e:
        raise RuntimeError(f"Failed to generate dimensions: {e}") from e

    return {"status": "dimensions_generated"}


def add_bom_table(
    x: float,
    y: float,
    rows: int = 10,
    columns: int = 4,
    row_height: float = 5.0,
    column_width: float = 30.0,
    headers: list[str] | None = None,
) -> dict[str, Any]:
    """Add a BOM-like table to the active drawing sheet.

    Args:
        x, y: Table position.
        rows: Number of rows.
        columns: Number of columns.
        row_height: Row height in mm.
        column_width: Column width in mm.
        headers: Optional header strings for first row.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)

    view = sheet.Views.Item(1)
    tables = view.Tables
    table = tables.Add(float(x), float(y), int(rows), int(columns), float(row_height), float(column_width))

    if headers:
        for col, header in enumerate(headers[:columns], start=1):
            try:
                table.SetCellString(1, col, str(header))
            except Exception:
                pass

    return {"feature": "Table", "name": table.Name, "rows": rows, "columns": columns}


def add_gdt(
    view_name: str,
    leader_x: float,
    leader_y: float,
    text_x: float,
    text_y: float,
    symbol: int = 0,
    text: str = "A",
) -> dict[str, Any]:
    """Add a GD&T (geometric tolerance) symbol to a drawing view.

    Args:
        view_name: Target view name.
        leader_x, leader_y: Leader anchor point.
        text_x, text_y: Text position.
        symbol: GDT symbol integer code.
        text: Tolerance text.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)
    view = _get_view_by_name(sheet, view_name)

    gdts = view.GDTs
    gdt = gdts.Add(float(leader_x), float(leader_y), float(text_x), float(text_y), int(symbol), str(text))

    return {"feature": "GDT", "name": gdt.Name, "symbol": symbol, "text": text}


def add_roughness(
    view_name: str,
    x: float,
    y: float,
    value: str = "Ra 1.6",
) -> dict[str, Any]:
    """Add a surface roughness annotation (approximated as text) to a drawing view.

    Args:
        view_name: Target view name.
        x, y: Text position.
        value: Roughness value string.
    """
    doc = _get_drawing_doc()
    sheet = _get_active_sheet(doc)
    view = _get_view_by_name(sheet, view_name)

    texts = view.Texts
    text_obj = texts.Add(str(value), float(x), float(y))

    return {"feature": "RoughnessText", "name": text_obj.Name, "value": value}
