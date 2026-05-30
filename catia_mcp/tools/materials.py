"""Material tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_pycatia_part_doc, get_active_document

logger = logging.getLogger(__name__)


def apply_material(material_name: str, body_name: str | None = None) -> dict[str, Any]:
    """Apply a material to a body or the main body.

    Args:
        material_name: Name of the material (e.g. "Steel", "Aluminum").
        body_name: Target body name (main body if None).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    body = None
    for b in part.bodies:
        if body_name and b.name == body_name:
            body = b
            break
    if body is None:
        body = part.bodies[0]

    # Use raw COM to apply material via MaterialManager
    try:
        mat_manager = part_doc.com_object.GetItem("CATMatManagerVB")
    except Exception:
        raise RuntimeError("Material manager is not available in this CATIA installation.")

    try:
        mat_manager.ApplyMaterialOnBody(body.com_object, material_name)
    except Exception as e:
        raise RuntimeError(f"Failed to apply material '{material_name}': {e}") from e

    return {"material": material_name, "body": body.name}


def remove_material(body_name: str | None = None) -> dict[str, Any]:
    """Remove material from a body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    body = None
    for b in part.bodies:
        if body_name and b.name == body_name:
            body = b
            break
    if body is None:
        body = part.bodies[0]

    try:
        mat_manager = part_doc.com_object.GetItem("CATMatManagerVB")
        mat_manager.RemoveMaterialOnBody(body.com_object)
    except Exception as e:
        raise RuntimeError(f"Failed to remove material: {e}") from e

    return {"removed_from": body.name}


def list_materials() -> list[dict[str, Any]]:
    """List available materials in the active document."""
    try:
        from pycatia.cat_mat_interfaces.material_manager import MaterialManager
        doc = get_active_document()
        mm = MaterialManager(doc.com_object.GetItem("CATMatManagerVB"))
        families = mm.families
        result = []
        for fam in families:
            result.append({"family": fam.name})
        return result
    except Exception as e:
        raise RuntimeError("Material manager is not available.") from e


def get_material_properties(body_name: str | None = None) -> dict[str, Any]:
    """Get material properties of a body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    body = None
    for b in part.bodies:
        if body_name and b.name == body_name:
            body = b
            break
    if body is None:
        body = part.bodies[0]

    try:
        mat = body.com_object.Material
        return {
            "body": body.name,
            "material": mat.Name,
            "density": getattr(mat, "Density", None),
        }
    except Exception:
        return {"body": body.name, "material": "None"}
