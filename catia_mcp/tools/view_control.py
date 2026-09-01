"""View control and visibility tools for CATIA — raw COM backed."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import get_catia, _get_pycatia_part_doc

logger = logging.getLogger(__name__)


def set_view_mode(mode: str = "shading") -> dict[str, Any]:
    """Set the view display mode.

    Args:
        mode: "shading", "wireframe", "shading_with_edges", "hidden_remove".
    """
    catia = get_catia()
    viewer = catia.ActiveWindow.ActiveViewer
    view_mode_map = {
        "shading": 0,
        "shading_with_edges": 1,
        "wireframe": 2,
        "hidden_remove": 3,
    }
    code = view_mode_map.get(mode.lower(), 0)
    try:
        viewer.RenderingMode = code
    except Exception as e:
        raise RuntimeError(f"Failed to set view mode '{mode}': {e}") from e
    return {"view_mode": mode, "code": code}


def hide_show(element_name: str, hide: bool = True) -> dict[str, Any]:
    """Hide or show a geometric element.

    Args:
        element_name: Name of the element.
        hide: True to hide, False to show.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    element = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == element_name:
                element = shape
                break
        if element:
            break

    if element is None:
        raise RuntimeError(f"Element '{element_name}' not found.")

    # Visibility is controlled via Selection.VisProperties.SetShow (0=show, 1=hide)
    catia = get_catia()
    sel = catia.ActiveDocument.Selection
    try:
        sel.Clear()
        sel.Add(element.com_object)
        sel.VisProperties.SetShow(1 if hide else 0)
    except Exception as e:
        raise RuntimeError(f"Failed to hide/show '{element_name}': {e}") from e
    finally:
        sel.Clear()

    part.update()
    return {"element": element_name, "hidden": hide}


def isolate(element_name: str) -> dict[str, Any]:
    """Isolate a single element (hide all others in the body).

    Args:
        element_name: Name of the element to isolate.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    target_body = None
    target = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == element_name:
                target = shape
                target_body = body
                break
        if target:
            break

    if target is None:
        raise RuntimeError(f"Element '{element_name}' not found.")

    # Visibility is controlled via Selection.VisProperties.SetShow (0=show, 1=hide)
    catia = get_catia()
    sel = catia.ActiveDocument.Selection
    try:
        for shape in target_body.shapes:
            if shape.name != element_name:
                sel.Clear()
                sel.Add(shape.com_object)
                sel.VisProperties.SetShow(1)
        sel.Clear()
        sel.Add(target.com_object)
        sel.VisProperties.SetShow(0)
    finally:
        sel.Clear()

    part.update()
    return {"isolated": element_name}


def activate_view(view_name: str = "Front") -> dict[str, Any]:
    """Activate a standard view.

    Args:
        view_name: "Front", "Back", "Left", "Right", "Top", "Bottom", "Isometric".
    """
    catia = get_catia()
    viewer = catia.ActiveWindow.ActiveViewer
    camera_map = {
        "front": "*front",
        "back": "*back",
        "left": "*left",
        "right": "*right",
        "top": "*top",
        "bottom": "*bottom",
        "isometric": "*iso",
    }
    key = view_name.lower()
    if key not in camera_map:
        raise ValueError(f"Unknown view: {view_name}")

    try:
        viewer.Viewpoint3D = catia.Cameras.Item(camera_map[key])
    except Exception as e:
        raise RuntimeError(f"Failed to activate view '{view_name}': {e}") from e

    return {"view": view_name}
