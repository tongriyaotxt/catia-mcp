"""Generative Shape Design (GSD) surface tools — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from pycatia.hybrid_shape_interfaces.hybrid_shape_factory import HybridShapeFactory

from catia_mcp.connection import _get_pycatia_part_doc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_hybrid_body(part, body_name: str | None = None):
    """Return a HybridBody (create if needed)."""
    hybrid_bodies = part.hybrid_bodies
    if body_name:
        try:
            return hybrid_bodies.item(body_name)
        except Exception:
            pass
    if hybrid_bodies.count == 0:
        hb = hybrid_bodies.add()
        try:
            hb.name = body_name or "GeometricalSet.1"
        except Exception:
            pass
        return hb
    return hybrid_bodies[0]


def _find_ref(part, name: str):
    """Find a reference by name in bodies, sketches, hybrid bodies, or origin elements."""
    # Try bodies/shapes
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == name:
                return part.create_reference_from_object(shape)
        # Try sketches inside bodies
        for sketch in body.sketches:
            if sketch.name == name:
                return part.create_reference_from_object(sketch)
    # Try hybrid bodies/hybrid shapes
    for hb in part.hybrid_bodies:
        for hs in hb.hybrid_shapes:
            if hs.name == name:
                return part.create_reference_from_object(hs)
    # Try origin elements
    plane_map = {
        "plane_xy": part.origin_elements.plane_xy,
        "plane_yz": part.origin_elements.plane_yz,
        "plane_zx": part.origin_elements.plane_zx,
    }
    key = name.lower()
    if key in plane_map:
        return part.create_reference_from_object(plane_map[key])
    raise RuntimeError(f"Element '{name}' not found.")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def create_gsd_point(x: float, y: float, z: float, name: str = "Point") -> dict[str, Any]:
    """Create a 3D point in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    point = gsf.add_new_point_coord(float(x), float(y), float(z))
    point.name = name
    hb.append_hybrid_shape(point)
    part.update()
    return {"feature": "GSD_Point", "name": point.name, "coords": [x, y, z]}


def create_gsd_line(
    point1_name: str,
    point2_name: str,
    name: str = "Line",
) -> dict[str, Any]:
    """Create a line through two points in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref1 = _find_ref(part, point1_name)
    ref2 = _find_ref(part, point2_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    line = gsf.add_new_line_pt_pt(ref1, ref2)
    line.name = name
    hb.append_hybrid_shape(line)
    part.update()
    return {"feature": "GSD_Line", "name": line.name}


def create_gsd_plane(
    reference_plane_name: str,
    offset: float = 0.0,
    name: str = "Plane",
) -> dict[str, Any]:
    """Create an offset plane in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref = _find_ref(part, reference_plane_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    plane = gsf.add_new_plane_offset(ref, float(offset), True)
    plane.name = name
    hb.append_hybrid_shape(plane)
    part.update()
    return {"feature": "GSD_Plane", "name": plane.name, "offset": offset}


def create_gsd_extrude(
    profile_name: str,
    length1: float = 10.0,
    length2: float = 0.0,
    direction: list[float] | None = None,
    name: str = "Extrude",
) -> dict[str, Any]:
    """Extrude a profile in GSD.

    Args:
        profile_name: Name of the profile (sketch or curve).
        length1: First limit length.
        length2: Second limit length.
        direction: [x, y, z] extrusion direction.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_profile = _find_ref(part, profile_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)

    dir_vec = direction or [0.0, 0.0, 1.0]
    dir_obj = gsf.add_new_direction_by_coord(float(dir_vec[0]), float(dir_vec[1]), float(dir_vec[2]))

    extrude = gsf.add_new_extrude(ref_profile, float(length1), float(length2), dir_obj)
    extrude.name = name
    hb.append_hybrid_shape(extrude)
    part.update()
    return {"feature": "GSD_Extrude", "name": extrude.name, "length1": length1}


def create_gsd_revol(
    profile_name: str,
    axis_name: str = "plane_xy",
    angle1: float = 0.0,
    angle2: float = 360.0,
    name: str = "Revol",
) -> dict[str, Any]:
    """Revolve a profile around an axis in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_profile = _find_ref(part, profile_name)
    ref_axis = _find_ref(part, axis_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    revol = gsf.add_new_revol(ref_profile, float(angle1), float(angle2), ref_axis)
    revol.name = name
    hb.append_hybrid_shape(revol)
    part.update()
    return {"feature": "GSD_Revol", "name": revol.name, "angle": angle2}


def create_gsd_offset(
    surface_name: str,
    offset: float = 1.0,
    name: str = "Offset",
) -> dict[str, Any]:
    """Offset a surface in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref = _find_ref(part, surface_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    offset_surf = gsf.add_new_offset(ref, float(offset), True, 0.001)
    offset_surf.name = name
    hb.append_hybrid_shape(offset_surf)
    part.update()
    return {"feature": "GSD_Offset", "name": offset_surf.name, "offset": offset}


def create_gsd_project(
    element_name: str,
    support_name: str,
    name: str = "Project",
) -> dict[str, Any]:
    """Project an element onto a support surface in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_elem = _find_ref(part, element_name)
    ref_support = _find_ref(part, support_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    proj = gsf.add_new_project(ref_elem, ref_support)
    proj.name = name
    hb.append_hybrid_shape(proj)
    part.update()
    return {"feature": "GSD_Project", "name": proj.name}


def create_gsd_intersect(
    element1_name: str,
    element2_name: str,
    name: str = "Intersect",
) -> dict[str, Any]:
    """Intersect two elements in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref1 = _find_ref(part, element1_name)
    ref2 = _find_ref(part, element2_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    inter = gsf.add_new_intersection(ref1, ref2)
    inter.name = name
    hb.append_hybrid_shape(inter)
    part.update()
    return {"feature": "GSD_Intersect", "name": inter.name}


def create_gsd_extract(
    element_name: str,
    name: str = "Extract",
) -> dict[str, Any]:
    """Extract a sub-element in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref = _find_ref(part, element_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    extract = gsf.add_new_extract(ref)
    extract.name = name
    hb.append_hybrid_shape(extract)
    part.update()
    return {"feature": "GSD_Extract", "name": extract.name}


def create_gsd_fill(
    boundary_name: str,
    name: str = "Fill",
) -> dict[str, Any]:
    """Create a fill surface from a closed boundary in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref = _find_ref(part, boundary_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    fill = gsf.add_new_fill()
    fill.name = name
    hb.append_hybrid_shape(fill)
    part.update()
    return {"feature": "GSD_Fill", "name": fill.name, "note": "May require boundary association post-creation."}


def create_gsd_sweep(
    guide_name: str,
    profile_name: str | None = None,
    sweep_type: str = "line",
    name: str = "Sweep",
) -> dict[str, Any]:
    """Create a sweep surface in GSD.

    Args:
        guide_name: Name of the guide curve.
        profile_name: Name of the profile (for explicit sweep).
        sweep_type: "circle", "conic", "explicit", or "line".
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_guide = _find_ref(part, guide_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)

    if sweep_type == "circle":
        sweep = gsf.add_new_sweep_circle(ref_guide)
    elif sweep_type == "conic":
        sweep = gsf.add_new_sweep_conic(ref_guide)
    elif sweep_type == "explicit" and profile_name:
        ref_profile = _find_ref(part, profile_name)
        sweep = gsf.add_new_sweep_explicit(ref_profile, ref_guide)
    else:
        sweep = gsf.add_new_sweep_line(ref_guide)

    sweep.name = name
    hb.append_hybrid_shape(sweep)
    part.update()
    return {"feature": "GSD_Sweep", "name": sweep.name, "type": sweep_type}


def create_gsd_split(
    element_name: str,
    splitting_name: str,
    name: str = "Split",
) -> dict[str, Any]:
    """Split an element by another in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_elem = _find_ref(part, element_name)
    ref_split = _find_ref(part, splitting_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    split = gsf.add_new_split(ref_elem, ref_split)
    split.name = name
    hb.append_hybrid_shape(split)
    part.update()
    return {"feature": "GSD_Split", "name": split.name}


def create_gsd_join(
    element1_name: str,
    element2_name: str,
    name: str = "Join",
) -> dict[str, Any]:
    """Join two elements in GSD."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref1 = _find_ref(part, element1_name)
    ref2 = _find_ref(part, element2_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    join = gsf.add_new_join(ref1, ref2)
    join.name = name
    hb.append_hybrid_shape(join)
    part.update()
    return {"feature": "GSD_Join", "name": join.name}


def create_gsd_trim(
    element1_name: str,
    element2_name: str,
    keep_side: int = 1,
    name: str = "Trim",
) -> dict[str, Any]:
    """Trim two elements in GSD.

    Args:
        element1_name: First element to trim.
        element2_name: Second element (trimming tool).
        keep_side: 1 = keep first side, -1 = keep second side.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref1 = _find_ref(part, element1_name)
    ref2 = _find_ref(part, element2_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    trim = gsf.add_new_hybrid_split(ref1, ref2, int(keep_side))
    trim.name = name
    hb.append_hybrid_shape(trim)
    part.update()
    return {"feature": "GSD_Trim", "name": trim.name}


def create_gsd_blend(
    curve1_name: str,
    curve2_name: str,
    continuity: str = "tangent",
    name: str = "Blend",
) -> dict[str, Any]:
    """Create a blend surface between two curves in GSD.

    Args:
        curve1_name: First boundary curve.
        curve2_name: Second boundary curve.
        continuity: "point", "tangent", or "curvature".
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref1 = _find_ref(part, curve1_name)
    ref2 = _find_ref(part, curve2_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    blend = gsf.add_new_blend(ref1, ref2)
    blend.name = name
    hb.append_hybrid_shape(blend)
    part.update()
    return {"feature": "GSD_Blend", "name": blend.name, "continuity": continuity}


def create_gsd_boundary(
    surface_name: str,
    name: str = "Boundary",
) -> dict[str, Any]:
    """Extract the boundary of a surface in GSD.

    Args:
        surface_name: Surface to extract boundary from.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref = _find_ref(part, surface_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    boundary = gsf.add_new_boundary(ref, True, 0.0)
    boundary.name = name
    hb.append_hybrid_shape(boundary)
    part.update()
    return {"feature": "GSD_Boundary", "name": boundary.name}
