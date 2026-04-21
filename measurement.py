"""Measurement and analysis tools for CATIA — pycatia + raw COM hybrid."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import (
    get_active_document,
    _get_pycatia_part_doc,
    _get_doc_type,
)

logger = logging.getLogger(__name__)


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
    distance = measurable.GetMinimumDistance(ref2.com_object)

    return {"distance_mm": distance, "element1": element1, "element2": element2}


def measure_length(element_name: str) -> dict[str, Any]:
    """Measure the length of a curve or edge."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = part.create_reference_from_name(element_name)

    measurable = _get_spa_measurable(ref)
    length = measurable.Length

    return {"length_mm": length, "element": element_name}


def measure_area(element_name: str | None = None) -> dict[str, Any]:
    """Measure the surface area of a face or body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    if element_name:
        ref = part.create_reference_from_name(element_name)
    else:
        ref = _get_body_ref(part)

    measurable = _get_spa_measurable(ref)
    area = measurable.Area

    return {"area_mm2": area, "element": element_name or "main_body"}


def measure_volume() -> dict[str, Any]:
    """Measure the volume of the active main body."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = _get_body_ref(part)

    measurable = _get_spa_measurable(ref)
    volume = measurable.Volume

    return {"volume_mm3": volume}


def measure_inertia(element_name: str | None = None) -> dict[str, Any]:
    """Compute inertia (mass properties) of a body or product."""
    doc = get_active_document()
    doc_type = _get_doc_type(doc)
    if doc_type == "Part":
        part_doc = _get_pycatia_part_doc(doc)
        part = part_doc.part
        if element_name:
            ref = part.create_reference_from_name(element_name)
        else:
            ref = _get_body_ref(part)
        try:
            inertia = part.get_inertia(ref)
        except Exception as exc:
            inertia = f"GetInertia not available: {exc}"
    elif doc_type == "Product":
        inertia = {"mass": 0.0, "com": [0.0, 0.0, 0.0]}
    else:
        raise RuntimeError("Inertia only supported for Part or Product documents.")

    return {"inertia": inertia, "element": element_name or "active"}


def get_bounding_box(element_name: str | None = None) -> dict[str, Any]:
    """Return the axis-aligned bounding box of a body or product."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    if element_name:
        ref = part.create_reference_from_name(element_name)
    else:
        ref = _get_body_ref(part)

    measurable = _get_spa_measurable(ref)
    bbox = measurable.GetBoundingBox()
    return {
        "min": [bbox[0], bbox[1], bbox[2]],
        "max": [bbox[3], bbox[4], bbox[5]],
    }
