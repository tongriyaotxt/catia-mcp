"""General utilities — search, graphic properties, layer, undo/redo."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import get_catia, get_active_document

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def search_elements(
    query: str,
    search_type: str = "name",
) -> list[dict[str, Any]]:
    """Search for elements in the active document using CATIA selection search.

    Args:
        query: Search string (supports wildcards, e.g., 'Pad*').
        search_type: "name", "type", or raw search string.
    """
    doc = get_active_document()
    sel = doc.Selection
    sel.Clear()

    if search_type.lower() == "name":
        search_str = f"Name={query},all"
    elif search_type.lower() == "type":
        search_str = f"Type={query},all"
    else:
        search_str = f"{query},all"

    try:
        sel.Search(search_str)
    except Exception as e:
        raise RuntimeError(f"Search failed: {e}") from e

    results = []
    for i in range(1, sel.Count2 + 1):
        try:
            item = sel.Item2(i)
            results.append({
                "name": getattr(item, "Name", "Unknown"),
                "type": getattr(item, "Type", "Unknown"),
            })
        except Exception:
            pass

    sel.Clear()
    return results


def set_graphic_properties(
    element_name: str,
    color: list[int] | None = None,
    line_type: int | None = None,
    width: int | None = None,
    show: bool | None = None,
    opacity: int | None = None,
) -> dict[str, Any]:
    """Set graphic properties (color, line type, width, show, opacity) of an element.

    Args:
        element_name: Name of the element.
        color: [R, G, B] values (0-255).
        line_type: Line type code (0=solid, etc.).
        width: Line width code.
        show: True to show, False to hide.
        opacity: Opacity percentage.
    """
    doc = get_active_document()
    sel = doc.Selection
    sel.Clear()

    try:
        sel.Search(f"Name={element_name},all")
    except Exception:
        raise RuntimeError(f"Element '{element_name}' not found.")

    if sel.Count2 == 0:
        raise RuntimeError(f"Element '{element_name}' not found.")

    vp = sel.VisProperties

    if color is not None:
        try:
            r, g, b = color
            vp.SetRealColor(int(r), int(g), int(b), 1.0)
            vp.SetVisibleColor(int(r), int(g), int(b), 1.0)
        except Exception as e:
            logger.warning("Failed to set color: %s", e)

    if line_type is not None:
        try:
            vp.SetRealLineType(int(line_type), 1.0)
            vp.SetVisibleLineType(int(line_type), 1.0)
        except Exception as e:
            logger.warning("Failed to set line type: %s", e)

    if width is not None:
        try:
            vp.SetRealWidth(int(width), 1.0)
            vp.SetVisibleWidth(int(width), 1.0)
        except Exception as e:
            logger.warning("Failed to set width: %s", e)

    if show is not None:
        try:
            vp.SetShow(int(show))
        except Exception as e:
            logger.warning("Failed to set show: %s", e)

    if opacity is not None:
        try:
            vp.SetRealOpacity(int(opacity), 1.0)
            vp.SetVisibleOpacity(int(opacity), 1.0)
        except Exception as e:
            logger.warning("Failed to set opacity: %s", e)

    sel.Clear()
    return {"element": element_name, "properties_updated": True}


def set_layer(element_name: str, layer: int) -> dict[str, Any]:
    """Set the layer of an element.

    Args:
        element_name: Name of the element.
        layer: Layer number.
    """
    doc = get_active_document()
    sel = doc.Selection
    sel.Clear()

    try:
        sel.Search(f"Name={element_name},all")
    except Exception:
        raise RuntimeError(f"Element '{element_name}' not found.")

    if sel.Count2 == 0:
        raise RuntimeError(f"Element '{element_name}' not found.")

    vp = sel.VisProperties
    try:
        vp.SetLayer(0, int(layer))
    except Exception as e:
        raise RuntimeError(f"Failed to set layer: {e}") from e
    finally:
        sel.Clear()

    return {"element": element_name, "layer": layer}


def undo() -> dict[str, Any]:
    """Undo the last operation (best effort).

    Note: CATIA COM automation has limited undo support. Use
    begin_undo_transaction / end_undo_transaction to group operations
    for manual undo in CATIA.
    """
    catia = get_catia()
    try:
        catia.StartCommand("Undo")
        return {
            "status": "undo_triggered",
            "note": "May require manual Ctrl+Z if COM undo is unavailable.",
        }
    except Exception as e:
        return {
            "status": "undo_failed",
            "error": str(e),
            "note": "Undo is not reliably available via COM automation. Please use Ctrl+Z in CATIA.",
        }


def redo() -> dict[str, Any]:
    """Redo the last undone operation (best effort).

    Note: CATIA COM automation has limited redo support.
    """
    catia = get_catia()
    try:
        catia.StartCommand("Redo")
        return {
            "status": "redo_triggered",
            "note": "May require manual Ctrl+Y if COM redo is unavailable.",
        }
    except Exception as e:
        return {
            "status": "redo_failed",
            "error": str(e),
            "note": "Redo is not reliably available via COM automation. Please use Ctrl+Y in CATIA.",
        }


def begin_undo_transaction() -> dict[str, Any]:
    """Begin a new undo-redo transaction group.

    Operations between begin/end can be undone together in CATIA.
    """
    catia = get_catia()
    try:
        catia.EnableNewUndoRedoTransaction()
        return {"status": "undo_transaction_enabled"}
    except Exception as e:
        raise RuntimeError(f"Failed to enable undo transaction: {e}") from e


def end_undo_transaction() -> dict[str, Any]:
    """End the current undo-redo transaction group."""
    catia = get_catia()
    try:
        catia.DisableNewUndoRedoTransaction()
        return {"status": "undo_transaction_disabled"}
    except Exception as e:
        raise RuntimeError(f"Failed to disable undo transaction: {e}") from e
