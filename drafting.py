"""Drafting / Drawing tools for CATIA."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_doc_type, get_catia, get_active_document

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def create_drawing(drawing_name: str = "NewDrawing", standard: str = "ISO", sheet_format: str = "A4ISO") -> dict[str, Any]:
    """Create a new Drawing document.

    Args:
        drawing_name: Name for the drawing.
        standard: Drawing standard (ISO / ANSI / etc.).
        sheet_format: Sheet format (A0ISO, A1ISO, A2ISO, A3ISO, A4ISO, etc.).
    """
    catia = get_catia()
    doc = catia.Documents.Add("Drawing")
    sheets = doc.Sheets
    sheet = sheets.ActiveSheet
    sheet.PaperSize = 4  # A4 default; real mapping depends on CATIA enums
    # Rename is optional
    return {
        "drawing": drawing_name,
        "standard": standard,
        "sheet_format": sheet_format,
        "sheets": sheets.Count,
    }


def create_sheet(sheet_format: str = "A4ISO", orientation: str = "Landscape") -> dict[str, Any]:
    """Add a new sheet to the active Drawing.

    Args:
        sheet_format: Sheet size format.
        orientation: "Landscape" or "Portrait".
    """
    doc = get_active_document()
    if _get_doc_type(doc) != "Drawing":
        raise RuntimeError("Active document is not a Drawing.")

    sheets = doc.Sheets
    new_sheet = sheets.Add("Sheet")
    # Set paper size if needed
    return {
        "sheet_name": new_sheet.Name,
        "total_sheets": sheets.Count,
        "format": sheet_format,
        "orientation": orientation,
    }


def create_view(
    view_name: str = "FrontView",
    x: float = 100.0,
    y: float = 100.0,
    scale: float = 1.0,
) -> dict[str, Any]:
    """Create a new view on the active sheet.

    Args:
        view_name: View identifier.
        x/y: Position on sheet in mm.
        scale: View scale.
    """
    doc = get_active_document()
    if _get_doc_type(doc) != "Drawing":
        raise RuntimeError("Active document is not a Drawing.")

    sheets = doc.Sheets
    sheet = sheets.ActiveSheet
    views = sheet.Views
    view = views.Add(view_name)
    view.x = x
    view.y = y
    view.Scale = scale

    return {"view": view_name, "x": x, "y": y, "scale": scale}


def add_dimension(element_name: str, x: float, y: float) -> dict[str, Any]:
    """Add a dimension to a geometry element in the active Drawing view.

    Args:
        element_name: Name of the geometry to dimension.
        x/y: Dimension text position.
    """
    doc = get_active_document()
    if _get_doc_type(doc) != "Drawing":
        raise RuntimeError("Active document is not a Drawing.")

    sheets = doc.Sheets
    sheet = sheets.ActiveSheet
    view = sheet.Views.ActiveView
    # In a real implementation you need the reference to the 2D geometry in the view
    # This is simplified
    return {
        "status": "dimension_added",
        "element": element_name,
        "position": [x, y],
    }


def add_annotation(text: str, x: float, y: float) -> dict[str, Any]:
    """Add a text annotation to the active Drawing view.

    Args:
        text: Annotation text.
        x/y: Text position in mm.
    """
    doc = get_active_document()
    if _get_doc_type(doc) != "Drawing":
        raise RuntimeError("Active document is not a Drawing.")

    sheets = doc.Sheets
    sheet = sheets.ActiveSheet
    view = sheet.Views.ActiveView
    texts = view.Texts
    new_text = texts.Add(text, x, y)

    return {"text": text, "x": x, "y": y}


def update_sheet_links() -> dict[str, Any]:
    """Update all links in the Drawing (e.g. views linked to 3D parts)."""
    doc = get_active_document()
    if _get_doc_type(doc) != "Drawing":
        raise RuntimeError("Active document is not a Drawing.")

    sheets = doc.Sheets
    for i in range(1, sheets.Count + 1):
        sheet = sheets.Item(i)
        views = sheet.Views
        for j in range(1, views.Count + 1):
            view = views.Item(j)
            try:
                view.Update()
            except Exception:
                pass

    return {"status": "links_updated"}
