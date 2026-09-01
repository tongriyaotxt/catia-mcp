"""Feature editing tools for CATIA Part Design — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_pycatia_part_doc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_shape(part, feature_name: str):
    """Find a shape by name across all bodies."""
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                return shape, body
    raise RuntimeError(f"Feature '{feature_name}' not found.")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def edit_feature_parameter(
    feature_name: str,
    parameter_name: str,
    value: float,
) -> dict[str, Any]:
    """Edit a parameter of an existing feature.

    Args:
        feature_name: Name of the feature to edit.
        parameter_name: Parameter name, e.g. "Length", "FirstAngle", "SecondAngle", "Diameter".
        value: New value.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    shape, _ = _find_shape(part, feature_name)

    # Try common attribute paths
    attr_map = {
        "length": ["first_limit.value", "firstlimit.value", "length.value"],
        "firstangle": ["first_angle.value", "firstangle.value"],
        "secondangle": ["second_angle.value", "secondangle.value"],
        "diameter": ["diameter.value", "diameter"],
        "depth": ["first_limit.value", "depth.value"],
    }

    key = parameter_name.lower().replace("_", "")
    candidates = attr_map.get(key, [parameter_name.lower()])

    for attr_path in candidates:
        try:
            obj = shape
            attrs = attr_path.split(".")
            for attr in attrs[:-1]:
                obj = getattr(obj, attr)
            setattr(obj, attrs[-1], float(value))
            part.update()
            return {
                "feature": feature_name,
                "parameter": parameter_name,
                "new_value": value,
            }
        except Exception:
            continue

    raise RuntimeError(
        f"Could not set parameter '{parameter_name}' on feature '{feature_name}'. "
        f"Known mappable parameters: {list(attr_map.keys())}"
    )


def delete_feature(feature_name: str) -> dict[str, Any]:
    """Delete a feature from the part."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    shape, _ = _find_shape(part, feature_name)

    try:
        # Datum features (planes, points, lines) are deleted via the factory
        ref = part.create_reference_from_object(shape)
        part.hybrid_shape_factory.delete_object_for_datum(ref)
    except Exception:
        # Solid shapes are deleted through the Selection
        sel = part_doc.selection
        sel.clear()
        sel.add(shape)
        sel.delete()

    part.update()
    return {"deleted": feature_name}


def get_feature_tree() -> list[dict[str, Any]]:
    """Return the full feature tree of the active part."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    tree = []
    for body in part.bodies:
        body_node = {
            "name": body.name,
            "type": "Body",
            "children": [],
        }
        for shape in body.shapes:
            body_node["children"].append({
                "name": shape.name,
                "type": type(shape).__name__,
            })
        tree.append(body_node)
    return tree


def reorder_feature(feature_name: str, new_index: int) -> dict[str, Any]:
    """Move a feature to a new position in the feature tree.

    Args:
        feature_name: Feature to move.
        new_index: 1-based target index within the body.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    shape, body = _find_shape(part, feature_name)

    # Try to use Body's Reorder feature if available via raw COM
    try:
        body.com_object.Shapes.Item(feature_name).Reorder(new_index)
    except Exception as e:
        logger.warning("Reorder via raw COM failed: %s", e)
        raise RuntimeError("Feature reordering is not supported in this CATIA version.") from e

    part.update()
    return {"feature": feature_name, "new_index": new_index}


def suppress_feature(feature_name: str) -> dict[str, Any]:
    """Suppress (deactivate) a feature."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    shape, _ = _find_shape(part, feature_name)

    try:
        shape.com_object.Active = False
    except Exception as e:
        raise RuntimeError(f"Could not suppress feature '{feature_name}'.") from e

    part.update()
    return {"suppressed": feature_name}


def activate_feature(feature_name: str) -> dict[str, Any]:
    """Activate a suppressed feature."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    shape, _ = _find_shape(part, feature_name)

    try:
        shape.com_object.Active = True
    except Exception as e:
        raise RuntimeError(f"Could not activate feature '{feature_name}'.") from e

    part.update()
    return {"activated": feature_name}
