"""Sketcher constraint tools for CATIA — pycatia-backed.

Provides dimensional and geometric constraints for 2D sketches.
"""

from __future__ import annotations

import logging
from typing import Any

from pycatia.enumeration.enums import CatConstraintType

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


def _get_geo_ref(part, sketch, element_name: str | None = None, index: int | None = None):
    """Return a Reference to a geometric element inside a sketch.

    Supports numeric strings as indices (e.g. "2" picks the 2nd element).
    """
    geos = sketch.geometric_elements
    if element_name:
        # Try numeric index first
        try:
            idx = int(element_name)
            if 1 <= idx <= geos.count:
                geo = geos.item(idx)
                return part.create_reference_from_object(geo)
        except ValueError:
            pass
        # Fall back to name lookup
        geo = geos.item(element_name)
    elif index is not None:
        geo = geos.item(index)
    else:
        if geos.count == 0:
            raise RuntimeError("No geometric elements in sketch.")
        geo = geos.item(geos.count)
    return part.create_reference_from_object(geo)


# ---------------------------------------------------------------------------
# Dimensional constraints
# ---------------------------------------------------------------------------

def add_length_constraint(
    element1: str | None = None,
    element2: str | None = None,
    value: float = 10.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a length/distance constraint between two sketch elements.

    Args:
        element1: Name of first geometric element (or None for single-element length).
        element2: Name of second geometric element (distance if provided).
        value: Constraint value in mm.
        sketch_name: Target sketch name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        if element2:
            ref2 = _get_geo_ref(part, sketch, element2)
            cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeDistance, ref1, ref2)
        else:
            cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeLength, ref1)
        cst.dimension.value = float(value)
    finally:
        sketch.close_edition()
    return {"constraint": "Length/Distance", "value": value, "type": cst.type}


def add_angle_constraint(
    element1: str,
    element2: str,
    value: float = 90.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add an angle constraint between two sketch elements."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        ref2 = _get_geo_ref(part, sketch, element2)
        cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeAngle, ref1, ref2)
        cst.dimension.value = float(value)
    finally:
        sketch.close_edition()
    return {"constraint": "Angle", "value": value}


def add_radius_constraint(
    element: str,
    value: float = 5.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a radius constraint to a circle or arc."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref = _get_geo_ref(part, sketch, element)
        cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeRadius, ref)
        cst.dimension.value = float(value)
    finally:
        sketch.close_edition()
    return {"constraint": "Radius", "value": value}


def add_diameter_constraint(
    element: str,
    value: float = 10.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a diameter constraint to a circle or arc."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref = _get_geo_ref(part, sketch, element)
        # CATIA has no diameter constraint type; emulate it with a radius
        # constraint set to half the requested diameter.
        cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeRadius, ref)
        cst.dimension.value = float(value) / 2.0
    finally:
        sketch.close_edition()
    return {
        "constraint": "Diameter",
        "value": value,
        "note": "CATIA only supports radius constraints; a radius constraint "
                "of value/2 was created to represent this diameter.",
    }


# ---------------------------------------------------------------------------
# Geometric constraints
# ---------------------------------------------------------------------------

def add_coincidence_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a coincidence constraint between two sketch elements."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        ref2 = _get_geo_ref(part, sketch, element2)
        cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeOn, ref1, ref2)
    finally:
        sketch.close_edition()
    return {"constraint": "Coincidence"}


def add_parallelism_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a parallelism constraint between two lines."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        ref2 = _get_geo_ref(part, sketch, element2)
        cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeParallelism, ref1, ref2)
    finally:
        sketch.close_edition()
    return {"constraint": "Parallelism"}


def add_perpendicularity_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a perpendicularity constraint between two lines."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        ref2 = _get_geo_ref(part, sketch, element2)
        cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypePerpendicularity, ref1, ref2)
    finally:
        sketch.close_edition()
    return {"constraint": "Perpendicularity"}


def add_concentricity_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a concentricity constraint between two circles/arcs."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        ref2 = _get_geo_ref(part, sketch, element2)
        cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeConcentricity, ref1, ref2)
    finally:
        sketch.close_edition()
    return {"constraint": "Concentricity"}


def add_tangency_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a tangency constraint between two curves."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref1 = _get_geo_ref(part, sketch, element1)
        ref2 = _get_geo_ref(part, sketch, element2)
        cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeTangency, ref1, ref2)
    finally:
        sketch.close_edition()
    return {"constraint": "Tangency"}


def add_horizontality_constraint(
    element: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a horizontal constraint to a line."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref = _get_geo_ref(part, sketch, element)
        cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeHorizontality, ref)
    finally:
        sketch.close_edition()
    return {"constraint": "Horizontality"}


def add_verticality_constraint(
    element: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a vertical constraint to a line."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref = _get_geo_ref(part, sketch, element)
        cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeVerticality, ref)
    finally:
        sketch.close_edition()
    return {"constraint": "Verticality"}


def add_fix_constraint(
    element: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a fix constraint to a sketch element."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    sketch.open_edition()
    try:
        ref = _get_geo_ref(part, sketch, element)
        cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeReference, ref)
    finally:
        sketch.close_edition()
    return {"constraint": "Fix"}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def list_constraints(sketch_name: str | None = None) -> list[dict[str, Any]]:
    """List all constraints in a sketch."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)
    constraints = sketch.constraints

    result = []
    for cst in constraints:
        val = None
        try:
            val = cst.dimension.value
        except Exception:
            pass
        result.append({
            "name": cst.name,
            "type": cst.type,
            "status": cst.status,
            "value": val,
        })
    return result
