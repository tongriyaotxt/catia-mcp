"""3D Part Design feature tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from pycatia.part_interfaces.shape_factory import ShapeFactory

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


def _ensure_body_in_work(part):
    """Make sure the in-work object is a Body before creating part-design
    features.

    GSD operations (points, curves, ...) leave a geometrical set as the
    in-work object; part-design features created in that state are silently
    discarded by CATIA. If the current in-work object is already one of the
    part's bodies (multi-body workflows), it is left untouched.
    """
    try:
        current = part.in_work_object
        for i in range(1, part.bodies.count + 1):
            if part.bodies.item(i).name == current.name:
                return  # already a body — respect multi-body workflows
    except Exception:
        pass
    part.in_work_object = _get_main_body(part)


def _get_sketch(part, sketch_name: str | None = None):
    """Return a sketch by name or the last one."""
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

def create_pad(length: float, sketch_name: str | None = None, reverse: bool = False) -> dict[str, Any]:
    """Create a Pad (extrusion) from a sketch profile."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    pad = sf.add_new_pad(sketch, float(length))
    if reverse:
        try:
            pad.direction_orientation = 1
        except Exception:
            pass

    part.update()
    return {"feature": "Pad", "length": length, "reverse": reverse, "sketch": sketch.name, "name": pad.name}


def create_pocket(length: float, sketch_name: str | None = None, reverse: bool = False) -> dict[str, Any]:
    """Create a Pocket (cut extrusion) from a sketch profile.

    CATIA's default pocket direction is opposite the sketch plane normal
    (i.e. into the material when the sketch lies on an outer face).
    Set reverse=True to cut the other way.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    pocket = sf.add_new_pocket(sketch, float(length))
    if reverse:
        try:
            pocket.direction_orientation = 0
        except Exception:
            logger.warning("Pocket reverse direction not applied.")

    part.update()
    return {"feature": "Pocket", "length": length, "sketch": sketch.name, "name": pocket.name}


def create_shaft(angle: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Shaft (revolution) from a sketch profile."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    shaft = sf.add_new_shaft(sketch)
    try:
        shaft.first_angle.value = float(angle)
    except Exception:
        pass

    part.update()
    return {"feature": "Shaft", "angle": angle, "sketch": sketch.name}


def _find_support_face(part_doc, part, point: tuple[float, float, float]):
    """Best-effort: find a planar face of the main body containing `point` (mm).

    Selects the body, searches CGM faces, and keeps the first planar face
    whose plane contains the point. Returns a pycatia Reference or None.
    """
    from catia_mcp.tools.measurement import _get_spa_workbench

    body = _get_main_body(part)
    spa = _get_spa_workbench(part_doc)
    sel = part_doc.selection
    px, py, pz = point
    sel.clear()
    try:
        sel.add(body)
        sel.search("Topology.CGMFace,sel")
        for i in range(1, sel.count + 1):
            fref = sel.item(i).reference
            measurable = spa.get_measurable(fref)
            try:
                plane = measurable.get_plane()
            except Exception:
                continue  # not a planar face
            o, d1, d2 = plane[0:3], plane[3:6], plane[6:9]
            n = (
                d1[1] * d2[2] - d1[2] * d2[1],
                d1[2] * d2[0] - d1[0] * d2[2],
                d1[0] * d2[1] - d1[1] * d2[0],
            )
            dist = abs((px - o[0]) * n[0] + (py - o[1]) * n[1] + (pz - o[2]) * n[2])
            if dist < 1e-6:
                return fref
    finally:
        sel.clear()
    return None


def create_hole(
    diameter: float,
    depth: float,
    point_x: float = 0.0,
    point_y: float = 0.0,
    point_z: float = 0.0,
    direction_x: float = 0.0,
    direction_y: float = 0.0,
    direction_z: float = 1.0,
    face_name: str | None = None,
) -> dict[str, Any]:
    """Create a Hole feature on the main body.

    The anchor point must lie on a planar face. The support face is located
    automatically (best-effort) unless `face_name` is given. The hole
    direction follows the support face normal (CATIA behavior); the
    direction_* arguments are currently informational only.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    if face_name:
        support = part.create_reference_from_name(face_name)
    else:
        support = _find_support_face(part_doc, part, (point_x, point_y, point_z))
        if support is None:
            raise RuntimeError(
                "No planar face found containing the anchor point "
                f"({point_x}, {point_y}, {point_z}). "
                "Provide face_name explicitly to choose the support face."
            )

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    # pycatia signature: (i_x, i_y, i_z, i_support_face_ref, i_depth)
    hole = sf.add_new_hole_from_point(
        float(point_x), float(point_y), float(point_z), support, float(depth)
    )
    # Hole.diameter is a read-only property returning a Length; set its value
    hole.diameter.value = float(diameter)

    part.update()
    return {"feature": "Hole", "diameter": diameter, "depth": depth, "name": hole.name}


def create_fillet(radius: float, edges: list[int] | None = None) -> dict[str, Any]:
    """Create a fillet on the main body.

    First tries Edge Fillet (if edge references are available);
    falls back to AutoFillet for localized CATIA where edge
    selection via COM is broken.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    edge_ref = _try_get_edge_ref(part, body, edges)
    if edge_ref is not None:
        fillet = sf.add_new_edge_fillet_with_constant_radius(edge_ref, 1, float(radius))
        part.update()
        return {"feature": "EdgeFillet", "radius": radius}

    # Fallback: AutoFillet (works on localized CATIA, applies to all edges)
    return create_auto_fillet(radius)


def create_auto_fillet(fillet_radius: float, round_radius: float = 0.0) -> dict[str, Any]:
    """Create an AutoFillet on the main body (no edge selection needed).

    Args:
        fillet_radius: Outer fillet radius in mm.
        round_radius: Inner round radius in mm (optional).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    auto_fillet = sf.add_new_auto_fillet(float(fillet_radius), float(round_radius))
    part.update()
    return {"feature": "AutoFillet", "fillet_radius": fillet_radius, "round_radius": round_radius}


def create_chamfer(length: float, edges: list[int] | None = None) -> dict[str, Any]:
    """Create a Chamfer on the main body.

    .. note::
        Edge selection via automation is limited in localized CATIA.
        If no valid edge reference can be obtained the tool raises
        a descriptive RuntimeError. Use `create_auto_fillet` as a
        workaround for rounded edges.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    edge_ref = _try_get_edge_ref(part, body, edges)
    if edge_ref is None:
        raise RuntimeError(
            "Could not obtain an edge reference for the chamfer. "
            "Chamfer requires edge selection which is unavailable in this CATIA locale. "
            "Use create_auto_fillet() instead for rounded edges."
        )

    chamfer = sf.add_new_chamfer(edge_ref, 1, 0, 0, float(length), float(length))
    part.update()
    return {"feature": "Chamfer", "length": length}


def _try_get_edge_ref(part, body, edges: list[int] | None = None):
    """Attempt to retrieve a Boundary/Edge reference for fillet/chamfer.

    .. note::
        In localized CATIA versions automated edge selection via COM is
        extremely limited.  This helper tries a few best-effort strategies
        but usually returns *None*.
    """
    shapes = body.shapes
    for label in ("Edge.1", "Vertex.1", "Border"):
        try:
            boundary = shapes.get_boundary(label)
            ref = part.create_reference_from_object(boundary)
            _ = ref.display_name
            return ref
        except Exception:
            pass
    return None


def create_mirror(feature_name: str, plane_name: str = "xy") -> dict[str, Any]:
    """Mirror a feature with respect to a plane."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    plane_map = {
        "xy": part.origin_elements.plane_xy,
        "yz": part.origin_elements.plane_yz,
        "zx": part.origin_elements.plane_zx,
    }
    plane = plane_map.get(plane_name.lower())
    if plane is None:
        raise ValueError(f"Unknown plane: {plane_name}")

    ref_plane = part.create_reference_from_object(plane)

    feature = None
    for shape in body.shapes:
        if shape.name == feature_name:
            feature = shape
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    part.in_work_object = feature
    mirror = sf.add_new_mirror(ref_plane)
    part.update()
    return {"feature": "Mirror", "mirrored": feature_name, "plane": plane_name}


def create_pattern(
    feature_name: str,
    instances_x: int,
    spacing_x: float,
    instances_y: int = 1,
    spacing_y: float = 0.0,
) -> dict[str, Any]:
    """Create a rectangular pattern of a feature."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    feature = None
    for shape in body.shapes:
        if shape.name == feature_name:
            feature = shape
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    ref_feature = part.create_reference_from_object(feature)
    ref_dir1 = part.create_reference_from_object(part.origin_elements.plane_yz)
    ref_dir2 = part.create_reference_from_object(part.origin_elements.plane_zx)

    pattern = sf.add_new_rect_pattern(
        ref_feature,
        int(instances_x),
        int(instances_y),
        float(spacing_x),
        float(spacing_y),
        1,
        1,
        ref_dir1,
        ref_dir2,
        False,
        False,
        0.0,
    )

    part.update()
    return {
        "feature": "RectPattern",
        "source": feature_name,
        "instances_x": instances_x,
        "spacing_x": spacing_x,
        "instances_y": instances_y,
        "spacing_y": spacing_y,
    }


def create_rib(sketch_name: str | None = None, center_curve_name: str | None = None) -> dict[str, Any]:
    """Create a Rib (sweep) from a profile sketch and a center-curve sketch.

    Args:
        sketch_name: Profile sketch name (last sketch if None).
        center_curve_name: Center-curve sketch name (required, must differ
            from the profile).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    profile = _get_sketch(part, sketch_name)
    center = _get_sketch(part, center_curve_name)
    if profile.name == center.name:
        raise RuntimeError("Rib requires distinct profile and center-curve sketches.")

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    rib = sf.add_new_rib(profile, center)
    part.update()
    return {"feature": "Rib", "profile": profile.name, "center_curve": center.name}


def create_slot(sketch_name: str | None = None, center_curve_name: str | None = None) -> dict[str, Any]:
    """Create a Slot (groove sweep) from a profile sketch and a center curve.

    Args:
        sketch_name: Profile sketch name (last sketch if None).
        center_curve_name: Center-curve sketch name (required, must differ
            from the profile).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    profile = _get_sketch(part, sketch_name)
    center = _get_sketch(part, center_curve_name)
    if profile.name == center.name:
        raise RuntimeError("Slot requires distinct profile and center-curve sketches.")

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    slot = sf.add_new_slot(profile, center)
    part.update()
    return {"feature": "Slot", "profile": profile.name, "center_curve": center.name}


def add_body(body_name: str = "NewBody") -> dict[str, Any]:
    """Add a new geometric body to the active part."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = part.bodies.add()
    body.name = body_name
    part.update()
    return {"feature": "Body", "name": body_name}


def insert_in_body(source_body_name: str, target_body_name: str = "PartBody") -> dict[str, Any]:
    """Insert one body into another (Boolean add)."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    bodies = part.bodies

    source = None
    target = None
    for b in bodies:
        if b.name == source_body_name:
            source = b
        if b.name == target_body_name:
            target = b

    if source is None:
        raise RuntimeError(f"Source body '{source_body_name}' not found.")
    if target is None:
        target = bodies[0]

    try:
        target.insert_in_body(source)
    except Exception:
        sf = ShapeFactory(part.shape_factory.com_object)
        _ensure_body_in_work(part)
        sf.add_new_add(target)

    part.update()
    return {"operation": "InsertInBody", "source": source_body_name, "target": target.name}
