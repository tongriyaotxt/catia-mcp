"""Measurement and analysis tools for CATIA — pycatia + raw COM hybrid.

Unit notes (verified empirically against CATIA V5):
- SPA Measurable scalar properties (Length/Area/Volume/GetMinimumDistance)
  return SI units: m, m^2, m^3. We convert to mm before returning.
- Coordinate arrays (e.g. GetMinimumDistancePoints) are already in mm.
"""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import (
    get_active_document,
    _get_pycatia_part_doc,
    _get_doc_type,
)

logger = logging.getLogger(__name__)

_M_TO_MM = 1e3
_M2_TO_MM2 = 1e6
_M3_TO_MM3 = 1e9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_spa_measurable(ref: Any) -> Any:
    """Obtain a measurable object via SPA workbench using raw COM."""
    doc = get_active_document()
    doc_com = doc.com_object if hasattr(doc, "com_object") else doc
    try:
        spa = doc_com.GetWorkbench("SPAWorkbench")
    except Exception as exc:
        raise RuntimeError("SPA workbench is not available in this CATIA installation.") from exc
    try:
        # ref is a pycatia Reference; pass its underlying COM object
        ref_com = ref.com_object if hasattr(ref, "com_object") else ref
        return spa.GetMeasurable(ref_com)
    except Exception as exc:
        raise RuntimeError("GetMeasurable failed — ensure the reference is valid.") from exc


def _get_spa_workbench(doc: Any = None) -> Any:
    """Return a pycatia SPAWorkbench wrapper for the given (or active) document."""
    from pycatia.space_analyses_interfaces.spa_workbench import SPAWorkbench
    if doc is None:
        doc = get_active_document()
    doc_com = doc.com_object if hasattr(doc, "com_object") else doc
    try:
        return SPAWorkbench(doc_com)
    except Exception as exc:
        raise RuntimeError("SPA workbench is not available in this CATIA installation.") from exc


def _get_body_ref(part):
    """Return a reference to the main body."""
    bodies = part.bodies
    if bodies.count == 0:
        raise RuntimeError("Part has no bodies.")
    body = bodies[0]
    return part.create_reference_from_object(body)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def measure_distance(element1: str, element2: str) -> dict[str, Any]:
    """Measure the minimum distance between two named elements."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    ref1 = part.create_reference_from_name(element1)
    ref2 = part.create_reference_from_name(element2)

    measurable = _get_spa_measurable(ref1)
    distance = measurable.GetMinimumDistance(ref2.com_object)  # SI: meters

    return {"distance_mm": distance * _M_TO_MM, "element1": element1, "element2": element2}


def measure_length(element_name: str) -> dict[str, Any]:
    """Measure the length of a curve or edge."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = part.create_reference_from_name(element_name)

    measurable = _get_spa_measurable(ref)
    length = measurable.Length  # SI: meters

    return {"length_mm": length * _M_TO_MM, "element": element_name}


def measure_area(element_name: str | None = None) -> dict[str, Any]:
    """Measure the surface area of a face or body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    if element_name:
        ref = part.create_reference_from_name(element_name)
    else:
        ref = _get_body_ref(part)

    measurable = _get_spa_measurable(ref)
    area = measurable.Area  # SI: square meters

    return {"area_mm2": area * _M2_TO_MM2, "element": element_name or "main_body"}


def measure_volume() -> dict[str, Any]:
    """Measure the volume of the active main body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = _get_body_ref(part)

    measurable = _get_spa_measurable(ref)
    volume = measurable.Volume  # SI: cubic meters

    return {"volume_mm3": volume * _M3_TO_MM3}


def measure_inertia(element_name: str | None = None) -> dict[str, Any]:
    """Compute inertia (mass properties) of a body or product.

    Uses the SPA workbench Inertia analysis object (pycatia wrapper), which
    works for both Part and Product documents. Values: mass in kg, COG in mm,
    inertia matrix in kg*m^2. Note: without an applied material CATIA assumes
    the default density (1000 kg/m^3).
    """
    doc = get_active_document()
    doc_type = _get_doc_type(doc)
    if doc_type == "Part":
        prod = _get_pycatia_part_doc(doc).product
    elif doc_type == "Product":
        from catia_mcp.connection import _get_pycatia_product_doc
        prod = _get_pycatia_product_doc(doc).product
    else:
        raise RuntimeError("Inertia only supported for Part or Product documents.")

    spa = _get_spa_workbench(doc)
    inertias = spa.inertias
    index = None
    try:
        inertia = inertias.add(prod)
        index = inertias.count
        result = {
            "mass_kg": inertia.mass,
            "cog_mm": [c * _M_TO_MM for c in inertia.get_cog_position()],
            "inertia_matrix_kg_m2": list(inertia.get_inertia_matrix()),
        }
    finally:
        # Remove the temporary analysis object so the tree stays clean
        if index is not None:
            try:
                inertias.remove(index)
            except Exception:
                logger.debug("Failed to remove temporary Inertia object.")

    return {"inertia": result, "element": element_name or "active"}


def get_bounding_box(element_name: str | None = None) -> dict[str, Any]:
    """Return the axis-aligned bounding box of a body, in mm.

    CATIA V5 automation exposes no usable GetBoundingBox on Measurable/Inertia
    (verified empirically), so this computes the box from six extremum points
    (one min/max per axis) created temporarily through the HybridShapeFactory.
    Extremum coordinates are read via Measurable.GetMinimumDistancePoints,
    the only call that works on datum extremum points.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    if element_name:
        ref = part.create_reference_from_name(element_name)
    else:
        ref = _get_body_ref(part)

    hsf = part.hybrid_shape_factory
    spa = _get_spa_workbench()

    mins = [0.0, 0.0, 0.0]
    maxs = [0.0, 0.0, 0.0]
    created = []
    try:
        for axis in range(3):
            vec = [0.0, 0.0, 0.0]
            vec[axis] = 1.0
            direction = hsf.add_new_direction_by_coord(*vec)
            created.append(direction)
            for which in (0, 1):  # 0 = min, 1 = max
                extremum = hsf.add_new_extremum(ref, direction, which)
                created.append(extremum)
                part.update_object(extremum)
                ext_ref = part.create_reference_from_object(extremum)
                measurable = spa.get_measurable(ext_ref)
                # Self-distance is zero; the returned point is the extremum
                # coordinate itself (mm).
                pts = measurable.get_minimum_distance_points(ext_ref)
                coords = list(pts)[:3]
                if which == 0:
                    mins[axis] = coords[axis]
                else:
                    maxs[axis] = coords[axis]
    finally:
        for feature in reversed(created):
            try:
                hsf.delete_object_for_datum(part.create_reference_from_object(feature))
            except Exception:
                logger.debug("Failed to delete temporary feature %s", feature)
        try:
            part.update()
        except Exception:
            pass

    return {
        "min_mm": mins,
        "max_mm": maxs,
        "size_mm": [maxs[i] - mins[i] for i in range(3)],
    }
