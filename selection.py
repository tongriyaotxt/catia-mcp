"""General selection tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import get_catia, _get_pycatia_part_doc

logger = logging.getLogger(__name__)


def clear_selection() -> dict[str, Any]:
    """Clear the current selection."""
    catia = get_catia()
    sel = catia.ActiveDocument.selection
    sel.clear()
    return {"selection_count": 0}


def get_selection_count() -> dict[str, Any]:
    """Return the number of items in the current selection."""
    catia = get_catia()
    sel = catia.ActiveDocument.selection
    return {"count": sel.count}


def select_element_by_name(element_name: str, append: bool = False) -> dict[str, Any]:
    """Select a geometric element by its name.

    Args:
        element_name: Name of the element (feature, body, plane, etc.).
        append: If True, add to current selection; otherwise replace.
    """
    catia = get_catia()
    doc = catia.ActiveDocument
    sel = doc.selection
    if not append:
        sel.clear()

    # Try to find element in the active document
    element = None
    try:
        # Try Part Bodies and Shapes
        part_doc = _get_pycatia_part_doc()
        part = part_doc.part
        for body in part.bodies:
            if body.name == element_name:
                element = body
                break
            for shape in body.shapes:
                if shape.name == element_name:
                    element = shape
                    break
            if element:
                break
        # Try origin elements
        if element is None:
            for plane in [part.origin_elements.plane_xy, part.origin_elements.plane_yz, part.origin_elements.plane_zx]:
                if plane.name == element_name:
                    element = plane
                    break
    except Exception:
        pass

    if element is None:
        raise RuntimeError(f"Element '{element_name}' not found in active document.")

    sel.selection.Add(element.com_object)
    return {"selected": element_name, "count": sel.count}


def select_face_by_index(
    feature_name: str,
    face_index: int = 1,
    append: bool = False,
) -> dict[str, Any]:
    """Select a face from a feature by index.

    .. note::
        Face selection relies on the Shape's Faces collection which may not
        be available in all CATIA locale/bindings. Falls back gracefully.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    catia = get_catia()
    sel = catia.ActiveDocument.selection
    if not append:
        sel.clear()

    # Find feature
    feature = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                feature = shape
                break
        if feature:
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    # Try to get face via raw COM
    try:
        faces = feature.com_object.Faces
        if faces.Count >= face_index:
            face = faces.Item(face_index)
            sel.selection.Add(face)
            return {"selected": f"{feature_name}.Face.{face_index}", "count": sel.count}
    except Exception:
        pass

    raise RuntimeError(
        f"Could not select face {face_index} from '{feature_name}'. "
        "Face access may not be available in this CATIA version."
    )


def select_edge_by_index(
    feature_name: str,
    edge_index: int = 1,
    append: bool = False,
) -> dict[str, Any]:
    """Select an edge from a feature by index.

    .. note::
        Edge selection relies on the Shape's Edges collection which may not
        be available in all CATIA locale/bindings. Falls back gracefully.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    catia = get_catia()
    sel = catia.ActiveDocument.selection
    if not append:
        sel.clear()

    feature = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                feature = shape
                break
        if feature:
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    try:
        edges = feature.com_object.Edges
        if edges.Count >= edge_index:
            edge = edges.Item(edge_index)
            sel.selection.Add(edge)
            return {"selected": f"{feature_name}.Edge.{edge_index}", "count": sel.count}
    except Exception:
        pass

    raise RuntimeError(
        f"Could not select edge {edge_index} from '{feature_name}'. "
        "Edge access may not be available in this CATIA version."
    )
