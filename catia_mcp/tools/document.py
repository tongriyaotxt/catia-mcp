"""Document management tools for CATIA."""

from __future__ import annotations

import logging
import os
from typing import Any

from catia_mcp.connection import get_catia, get_active_document, _get_doc_type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_info(doc: Any) -> dict[str, Any]:
    """Extract serialisable info from a Document COM object."""
    try:
        path = doc.FullName
    except Exception:
        path = None
    try:
        name = doc.Name
    except Exception:
        name = "Unknown"
    # doc.Type raises for never-saved documents; use extension fallback
    doc_type = _get_doc_type(doc)
    try:
        saved = doc.Saved
    except Exception:
        saved = None
    return {
        "name": name,
        "type": doc_type,
        "path": path,
        "saved": saved,
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def list_documents() -> list[dict[str, Any]]:
    """List all currently open CATIA documents."""
    catia = get_catia()
    docs = catia.Documents
    count = docs.Count
    result = []
    for i in range(1, count + 1):
        doc = docs.Item(i)
        result.append(_doc_info(doc))
    return result


def get_active_document_info() -> dict[str, Any]:
    """Return information about the active document."""
    doc = get_active_document()
    return _doc_info(doc)


def open_document(file_path: str) -> dict[str, Any]:
    """Open an existing CATIA document (.CATPart, .CATProduct, .CATDrawing, etc.)."""
    catia = get_catia()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    doc = catia.Documents.Open(file_path)
    return _doc_info(doc)


def new_document(doc_type: str = "Part") -> dict[str, Any]:
    """Create a new CATIA document.

    Args:
        doc_type: One of "Part", "Product", "Drawing".
    """
    catia = get_catia()
    if doc_type not in {"Part", "Product", "Drawing"}:
        raise ValueError(f"Unsupported document type: {doc_type}")
    doc = catia.Documents.Add(doc_type)
    return _doc_info(doc)


def save_document() -> dict[str, Any]:
    """Save the active document in place."""
    doc = get_active_document()
    doc.Save()
    return _doc_info(doc)


def save_as_document(file_path: str) -> dict[str, Any]:
    """Save the active document to a new file path."""
    doc = get_active_document()
    doc.SaveAs(file_path)
    return _doc_info(doc)


def close_document(save: bool = False) -> dict[str, Any]:
    """Close the active document.

    Args:
        save: Whether to save before closing.
    """
    doc = get_active_document()
    info = _doc_info(doc)
    if save:
        try:
            doc.Save()
        except Exception:
            pass
    try:
        doc.Close()
    except Exception:
        pass
    return {"closed": info}


def close_all_documents(save: bool = False) -> dict[str, Any]:
    """Close all open documents.

    Args:
        save: Whether to save each document before closing.
    """
    catia = get_catia()
    docs = catia.Documents
    closed = []
    # Iterate backwards because collection shrinks as we close
    for i in range(docs.Count, 0, -1):
        doc = docs.Item(i)
        closed.append(_doc_info(doc))
        if save:
            try:
                doc.Save()
            except Exception:
                pass
        try:
            doc.Close()
        except Exception:
            pass
    return {"closed": closed}


def get_document_type() -> str:
    """Return the type of the active document (Part / Product / Drawing)."""
    from catia_mcp.connection import _get_doc_type
    doc = get_active_document()
    return _get_doc_type(doc)
