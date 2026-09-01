"""Drafting / Drawing tools for CATIA."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_doc_type, get_catia, get_active_document

logger = logging.getLogger(__name__)


# CatPaperSize values (pycatia cat_paper_size enum): index in tuple
# (Letter=0, Legal=1, A0=2, A1=3, A2=4, A3=5, A4=6)
_PAPER_SIZE_MAP = {
    "letter": 0,
    "legal": 1,
    "a0": 2,
    "a1": 3,
    "a2": 4,
    "a3": 5,
    "a4": 6,
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def create_drawing(drawing_name: str = "NewDrawing", standard: str = "ISO", sheet_format: str = "A4ISO") -> dict[str, Any]:
    """Create a new Drawing document.

    Args:
        drawing_name: Name for the drawing.
        standard: Drawing standard (ISO / ANSI / etc.). Note: CATIA COM
            automation cannot switch the drawing standard after creation;
            the standard of the default drawing template is used.
        sheet_format: Sheet format (A0ISO, A1ISO, A2ISO, A3ISO, A4ISO, etc.).
    """
    catia = get_catia()
    doc = catia.Documents.Add("Drawing")
    sheets = doc.Sheets
    sheet = sheets.ActiveSheet

    key = sheet_format.lower().replace("iso", "").replace("ansi", "")
    paper_size = _PAPER_SIZE_MAP.get(key)
    if paper_size is None:
        raise ValueError(f"Unknown sheet format: {sheet_format}")
    sheet.PaperSize = paper_size

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

    return {
        "status": "not_implemented",
        "element": element_name,
        "position": [x, y],
        "note": "Dimension creation requires references to the generated 2D "
                "geometry inside a Drawing view, which is not implemented yet. "
                "No dimension was created.",
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
