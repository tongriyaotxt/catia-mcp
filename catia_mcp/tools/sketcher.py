"""2D Sketcher tools for CATIA Part Design — pycatia-backed."""

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
    """Return the first body of the part (handles localized CATIA names)."""
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
    """Return a sketch by name or the last one."""
    body = _get_main_body(part)
    sketches = body.sketches
    if sketch_name:
        return sketches.item(sketch_name)
    if sketches.count == 0:
        raise RuntimeError("No sketches found. Create one first.")
    return sketches[sketches.count - 1]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def create_sketch_on_plane(plane_name: str = "xy") -> dict[str, Any]:
    """Create a new sketch on a reference plane.

    Args:
        plane_name: One of "xy", "yz", "zx".
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    plane_map = {
        "xy": part.origin_elements.plane_xy,
        "yz": part.origin_elements.plane_yz,
        "zx": part.origin_elements.plane_zx,
    }
    key = plane_name.lower()
    if key not in plane_map:
        raise ValueError(f"Unknown plane: {plane_name}")

    body = _get_main_body(part)
    # Ensure a unique sketch name: a second sketch on the same plane must not
    # collide with an existing one, otherwise name-based lookup
    # (_get_sketch / sketches.item(name)) would silently resolve to the
    # FIRST sketch and draw into / extrude the wrong profile.
    base = f"Sketch_{plane_name.upper()}"
    existing = {body.sketches.item(i).name for i in range(1, body.sketches.count + 1)}
    name = base
    n = 2
    while name in existing:
        name = f"{base}_{n}"
        n += 1
    sketch = body.sketches.add(plane_map[key])
    try:
        sketch.name = name
    except Exception:
        pass  # keep CATIA-generated (unique) name
    return {"sketch_name": sketch.name, "plane": plane_name.upper(), "is_open": True}


def add_point(x: float, y: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D point to the active or named sketch."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    factory_2d.create_point(x, y)
    sketch.close_edition()

    return {"type": "Point", "x": x, "y": y}


def add_line(x1: float, y1: float, x2: float, y2: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D line to the active or named sketch."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    factory_2d.create_line(x1, y1, x2, y2)
    sketch.close_edition()

    return {"type": "Line", "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def add_circle(center_x: float, center_y: float, radius: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D circle to the active or named sketch."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    factory_2d.create_closed_circle(center_x, center_y, radius)
    sketch.close_edition()

    return {"type": "Circle", "center_x": center_x, "center_y": center_y, "radius": radius}


def add_rectangle(x1: float, y1: float, x2: float, y2: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add an axis-aligned rectangle to the active or named sketch.

    Uses four explicit lines whose end-points coincide; CATIA treats
    coincident end-points as a closed profile for Pad / Pocket.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()
    factory_2d.create_line(x1, y1, x2, y1)
    factory_2d.create_line(x2, y1, x2, y2)
    factory_2d.create_line(x2, y2, x1, y2)
    factory_2d.create_line(x1, y2, x1, y1)
    sketch.close_edition()

    return {"type": "Rectangle", "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def add_arc(
    center_x: float,
    center_y: float,
    radius: float,
    start_angle: float,
    end_angle: float,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a circular arc to the active or named sketch (angles in degrees).

    Uses a 5-point spline to approximate the arc — sufficient for Pad / Pocket
    profiles in CATIA.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    factory_2d = sketch.open_edition()

    # Build 5 control points along the arc for a smooth spline approximation
    angles = [start_angle + (end_angle - start_angle) * t for t in [0.0, 0.25, 0.5, 0.75, 1.0]]
    points = []
    for a in angles:
        px = center_x + radius * math.cos(math.radians(a))
        py = center_y + radius * math.sin(math.radians(a))
        points.append(factory_2d.create_point(px, py))

    factory_2d.create_spline(points)
    sketch.close_edition()

    return {
        "type": "Arc",
        "center_x": center_x,
        "center_y": center_y,
        "radius": radius,
        "start_angle": start_angle,
        "end_angle": end_angle,
    }


def close_sketch(sketch_name: str | None = None) -> dict[str, Any]:
    """Close the sketch edition (commit changes)."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    sketch.close_edition()
    return {"sketch_name": sketch.name, "is_open": False}


def get_sketch_elements(sketch_name: str | None = None) -> list[dict[str, Any]]:
    """List geometric elements in a sketch."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    elements = []
    geos = sketch.geometric_elements
    for i in range(1, geos.count + 1):
        geo = geos.item(i)
        elements.append({
            "name": geo.name,
            "type": getattr(geo, "geometric_type", "Unknown"),
        })
    return elements
