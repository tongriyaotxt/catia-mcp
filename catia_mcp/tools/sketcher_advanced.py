"""Advanced 2D Sketcher tools — spline, ellipse, construction line, 3D projection."""

from __future__ import annotations

import logging
import math
from typing import Any

from catia_mcp.connection import _get_pycatia_part_doc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_main_body(part):
    bodies = part.bodies
    if bodies.count == 0:
        body = bodies.add()
        try:
            body.name = "PartBody"
        except Exception:
            pass
        return body
    return bodies[0]


def _get_sketch(part, sketch_name: str | None = None):
    body = _get_main_body(part)
    sketches = body.sketches
    if sketch_name:
        return sketches.item(sketch_name)
    if sketches.count == 0:
        raise RuntimeError("No sketches found.")
    return sketches[sketches.count - 1]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def add_spline(points: list[list[float]], sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D spline (open) to the active or named sketch.

    Args:
        points: List of [x, y] control points.
        sketch_name: Optional target sketch name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    point_objs = [factory_2d.create_point(float(x), float(y)) for x, y in points]
    factory_2d.create_spline(tuple(point_objs))
    sketch.close_edition()

    return {"type": "Spline", "points": len(points)}


def add_ellipse(
    center_x: float,
    center_y: float,
    major_radius: float,
    minor_radius: float,
    angle: float = 0.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a closed ellipse to the active or named sketch.

    Args:
        center_x, center_y: Ellipse center.
        major_radius: Major axis radius.
        minor_radius: Minor axis radius.
        angle: Rotation angle of major axis in degrees.
        sketch_name: Optional target sketch name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    rad = math.radians(angle)
    major_x = center_x + major_radius * math.cos(rad)
    major_y = center_y + major_radius * math.sin(rad)
    factory_2d.create_closed_ellipse(
        float(center_x),
        float(center_y),
        float(major_x),
        float(major_y),
        float(major_radius),
        float(minor_radius),
    )
    sketch.close_edition()

    return {
        "type": "Ellipse",
        "center_x": center_x,
        "center_y": center_y,
        "major_radius": major_radius,
        "minor_radius": minor_radius,
        "angle": angle,
    }


def add_construction_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a construction line (axis) to the active or named sketch.

    Args:
        x1, y1: Start point.
        x2, y2: End point.
        sketch_name: Optional target sketch name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    factory_2d.create_line(float(x1), float(y1), float(x2), float(y2))
    sketch.close_edition()

    # Try to set the last created line as construction
    geos = sketch.geometric_elements
    try:
        last_geo = geos[geos.count]
        if hasattr(last_geo, "construction"):
            last_geo.construction = True
        else:
            try:
                last_geo.com_object.Construction = True
            except Exception:
                pass
    except Exception:
        pass

    return {"type": "ConstructionLine", "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def project_3d_to_sketch(
    element_names: list[str],
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Project 3D element(s) onto the active or named sketch.

    Args:
        element_names: List of 3D element names to project.
        sketch_name: Optional target sketch name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    refs = []
    for name in element_names:
        ref = None
        # Search in bodies/shapes
        for body in part.bodies:
            for shape in body.shapes:
                if shape.name == name:
                    ref = part.create_reference_from_object(shape)
                    break
            if ref:
                break
            for sk in body.sketches:
                if sk.name == name:
                    ref = part.create_reference_from_object(sk)
                    break
            if ref:
                break
        # Search in hybrid bodies
        if not ref:
            for hb in part.hybrid_bodies:
                for hs in hb.hybrid_shapes:
                    if hs.name == name:
                        ref = part.create_reference_from_object(hs)
                        break
                if ref:
                    break
        # Origin elements
        if not ref:
            plane_map = {
                "plane_xy": part.origin_elements.plane_xy,
                "plane_yz": part.origin_elements.plane_yz,
                "plane_zx": part.origin_elements.plane_zx,
            }
            key = name.lower()
            if key in plane_map:
                ref = part.create_reference_from_object(plane_map[key])
        if not ref:
            raise RuntimeError(f"3D element '{name}' not found for projection.")
        refs.append(ref)

    factory_2d = sketch.open_edition()
    for ref in refs:
        factory_2d.create_projection(ref)
    sketch.close_edition()

    return {"type": "Projection3D", "projected": element_names}
