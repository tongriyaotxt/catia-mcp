"""Export, view control and screenshot tools for CATIA."""

from __future__ import annotations

import logging
import os
from typing import Any

from catia_mcp.connection import _get_doc_type, get_active_document, get_catia

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def export_to_stl(file_path: str, binary: bool = True, tolerance: float = 0.1) -> dict[str, Any]:
    """Export the active Part or Product to STL.

    Args:
        file_path: Output .stl path.
        binary: Not supported — CATIA ExportData always writes ASCII STL.
            Kept for interface compatibility.
        tolerance: Not supported — tessellation is controlled by CATIA's own
            STL export settings. Kept for interface compatibility.
    """
    doc = get_active_document()
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    doc.ExportData(file_path, "stl")

    return {
        "exported_to": file_path,
        "format": "STL",
        "note": "CATIA ExportData always writes ASCII STL; 'binary' and 'tolerance' are ignored.",
    }


def export_to_step(file_path: str, schema: str = "AP214") -> dict[str, Any]:
    """Export the active document to STEP.

    Args:
        file_path: Output .stp/.step path.
        schema: STEP schema (AP203, AP214, AP242).
    """
    doc = get_active_document()
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    doc.ExportData(file_path, "stp")
    return {"exported_to": file_path, "format": "STEP", "schema": schema}


def export_to_iges(file_path: str) -> dict[str, Any]:
    """Export the active document to IGES.

    Args:
        file_path: Output .igs/.iges path.
    """
    doc = get_active_document()
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    doc.ExportData(file_path, "igs")
    return {"exported_to": file_path, "format": "IGES"}


def export_to_pdf(file_path: str) -> dict[str, Any]:
    """Export the active Drawing to PDF.

    Args:
        file_path: Output .pdf path.
    """
    doc = get_active_document()
    if _get_doc_type(doc) != "Drawing":
        raise RuntimeError("Active document is not a Drawing.")
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    doc.ExportData(file_path, "pdf")
    return {"exported_to": file_path, "format": "PDF"}


def capture_screenshot(file_path: str, width: int = 1920, height: int = 1080) -> dict[str, Any]:
    """Capture the active 3D view to an image file.

    Args:
        file_path: Output image path (.bmp, .png, .jpg).
        width: Not supported — Viewer.CaptureToFile captures at the current
            viewer resolution. Kept for interface compatibility.
        height: Not supported — see width.
    """
    catia = get_catia()
    viewer = catia.ActiveWindow.ActiveViewer
    # Capture to file
    viewer.CaptureToFile(0, file_path)  # 0 = BMP; adjust per CATIA version
    return {
        "screenshot": file_path,
        "note": "CaptureToFile does not support custom resolution; 'width' and 'height' are ignored.",
    }


def fit_all_in() -> dict[str, Any]:
    """Fit all geometry into the active view."""
    catia = get_catia()
    viewer = catia.ActiveWindow.ActiveViewer
    viewer.Reframe()
    return {"status": "fit_all"}


def update_view() -> dict[str, Any]:
    """Update (redraw) the active viewer."""
    catia = get_catia()
    viewer = catia.ActiveWindow.ActiveViewer
    viewer.Update()
    return {"status": "view_updated"}
