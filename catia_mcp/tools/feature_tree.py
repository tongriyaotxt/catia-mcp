"""Feature tree and manipulation tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_pycatia_part_doc

logger = logging.getLogger(__name__)


def get_full_feature_tree() -> list[dict[str, Any]]:
    """Return the complete feature tree including all bodies and hybrid bodies."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    tree = []
    # Part bodies
    for body in part.bodies:
        node = {
            "name": body.name,
            "type": "Body",
            "children": [],
        }
        for shape in body.shapes:
            node["children"].append({
                "name": shape.name,
                "type": type(shape).__name__,
            })
        tree.append(node)

    # Hybrid bodies
    for hb in part.hybrid_bodies:
        node = {
            "name": hb.name,
            "type": "HybridBody",
            "children": [],
        }
        for hs in hb.hybrid_shapes:
            node["children"].append({
                "name": hs.name,
                "type": type(hs).__name__,
            })
        tree.append(node)

    return tree


def get_body_contents(body_name: str | None = None) -> dict[str, Any]:
    """Return the contents of a specific body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    body = None
    for b in part.bodies:
        if body_name and b.name == body_name:
            body = b
            break
    if body is None:
        body = part.bodies[0]

    shapes = []
    for shape in body.shapes:
        shapes.append({
            "name": shape.name,
            "type": type(shape).__name__,
        })
    return {"body": body.name, "shapes": shapes}


def rename_feature(old_name: str, new_name: str) -> dict[str, Any]:
    """Rename a feature in the active part."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    # Search in bodies
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == old_name:
                shape.name = new_name
                return {"old_name": old_name, "new_name": new_name}
        if body.name == old_name:
            body.name = new_name
            return {"old_name": old_name, "new_name": new_name}

    # Search in hybrid bodies
    for hb in part.hybrid_bodies:
        for hs in hb.hybrid_shapes:
            if hs.name == old_name:
                hs.name = new_name
                return {"old_name": old_name, "new_name": new_name}
        if hb.name == old_name:
            hb.name = new_name
            return {"old_name": old_name, "new_name": new_name}

    raise RuntimeError(f"Feature '{old_name}' not found.")


def copy_paste_feature(
    feature_name: str,
    target_body_name: str | None = None,
) -> dict[str, Any]:
    """Copy and paste a feature into a target body.

    .. note::
        This is a simplified placeholder. True copy-paste requires
        selection and clipboard operations via raw COM.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    feature = None
    source_body = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                feature = shape
                source_body = body
                break
        if feature:
            break

    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    target = None
    for body in part.bodies:
        if target_body_name and body.name == target_body_name:
            target = body
            break
    if target is None:
        target = source_body

    # Use raw COM copy-paste
    try:
        sel = part_doc.com_object.Selection
        sel.clear()
        sel.Add(feature.com_object)
        sel.Copy()
        sel.Clear()
        # Paste into target body
        # In CATIA, paste usually goes to the current InWorkObject
        part.in_work_object = target
        sel.Paste()
        sel.Clear()
        part.update()
    except Exception as e:
        raise RuntimeError(f"Copy-paste failed: {e}") from e

    return {"copied": feature_name, "target": target.name}
