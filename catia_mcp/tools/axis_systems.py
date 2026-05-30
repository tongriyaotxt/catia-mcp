"""Axis system (coordinate frame) tools for CATIA Part Design.

Essential for robotics / kinematics — each joint needs a defined coordinate frame.
"""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_pycatia_part_doc

logger = logging.getLogger(__name__)


def create_axis_system(
    name: str = "AxisSystem",
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    origin_z: float = 0.0,
    x_axis: list[float] | None = None,
    y_axis: list[float] | None = None,
    z_axis: list[float] | None = None,
) -> dict[str, Any]:
    """Create a new axis system (coordinate frame) in the active Part.

    Args:
        name: Name for the axis system.
        origin_x, origin_y, origin_z: Origin coordinates in mm.
        x_axis, y_axis, z_axis: Optional [dx, dy, dz] direction vectors.
            If omitted the axis system keeps the default XYZ orientation.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    axis_systems = part.axis_systems
    axis = axis_systems.add()
    axis.name = name

    com = axis.com_object
    com.PutOrigin((float(origin_x), float(origin_y), float(origin_z)))

    # Attempt to set custom orientation if all three vectors are supplied
    if x_axis and y_axis and z_axis:
        try:
            com.PutVectors(
                [float(v) for v in x_axis],
                [float(v) for v in y_axis],
                [float(v) for v in z_axis],
            )
        except Exception:
            # Some CATIA locales do not expose PutVectors via standard dispatch
            logger.debug("PutVectors not available; axis system uses default orientation.")

    return {
        "axis_system": name,
        "origin": [origin_x, origin_y, origin_z],
    }


def list_axis_systems() -> list[dict[str, Any]]:
    """List all axis systems in the active Part."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    result = []
    for axis in part.axis_systems:
        # GetOrigin/OriginPoint often fail on localized CATIA; skip gracefully
        result.append({
            "name": axis.name,
        })
    return result


def set_axis_system_origin(
    name: str,
    x: float,
    y: float,
    z: float,
) -> dict[str, Any]:
    """Move an existing axis system to a new origin."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    for axis in part.axis_systems:
        if axis.name == name:
            axis.com_object.PutOrigin((float(x), float(y), float(z)))
            return {"axis_system": name, "new_origin": [x, y, z]}

    raise RuntimeError(f"Axis system '{name}' not found.")
