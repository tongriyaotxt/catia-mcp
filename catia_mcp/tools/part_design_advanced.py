"""Advanced Part Design feature tools — pycatia-backed.

Includes Shell, Draft, Thickness, Boolean operations, Split, etc.
"""

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
    bodies = part.bodies
    if bodies.count == 0:
        body = bodies.add()
        try:
            body.name = "PartBody"
        except Exception:
            pass
        return body
    return bodies[0]


def _find_body(part, body_name: str):
    for body in part.bodies:
        if body.name == body_name:
            return body
    raise RuntimeError(f"Body '{body_name}' not found.")


def _try_get_face_ref(part, feature_name: str, face_index: int = 1):
    """Attempt to get a face reference from a feature via raw COM."""
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                try:
                    faces = shape.com_object.Faces
                    if faces.Count >= face_index:
                        face = faces.Item(face_index)
                        return part.create_reference_from_object(face)
                except Exception:
                    pass
                break
    raise RuntimeError(
        f"Could not get face {face_index} from '{feature_name}'. "
        "Face access may not be available in this CATIA locale."
    )


# ---------------------------------------------------------------------------
# Boolean operations
# ---------------------------------------------------------------------------

def create_boolean_add(source_body_name: str, target_body_name: str | None = None) -> dict[str, Any]:
    """Boolean add: insert one body into another.

    Args:
        source_body_name: Body to add.
        target_body_name: Destination body (main body if None).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    source = _find_body(part, source_body_name)
    target = _find_body(part, target_body_name) if target_body_name else _get_main_body(part)

    if source.com_object == target.com_object:
        raise RuntimeError(
            "Source and target body are the same. "
            "Create a separate body first (e.g. via add_new_body) before boolean operation."
        )

    sf = ShapeFactory(part.shape_factory.com_object)
    sf.add_new_add(source)
    part.update()
    return {"operation": "BooleanAdd", "source": source_body_name, "target": target.name}


def create_boolean_remove(source_body_name: str, target_body_name: str | None = None) -> dict[str, Any]:
    """Boolean remove: subtract one body from another."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    source = _find_body(part, source_body_name)
    target = _find_body(part, target_body_name) if target_body_name else _get_main_body(part)

    if source.com_object == target.com_object:
        raise RuntimeError(
            "Source and target body are the same. "
            "Create a separate body first (e.g. via add_new_body) before boolean operation."
        )

    sf = ShapeFactory(part.shape_factory.com_object)
    sf.add_new_remove(source)
    part.update()
    return {"operation": "BooleanRemove", "source": source_body_name, "target": target.name}


def create_boolean_intersect(source_body_name: str, target_body_name: str | None = None) -> dict[str, Any]:
    """Boolean intersect: intersect one body with another."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    source = _find_body(part, source_body_name)
    target = _find_body(part, target_body_name) if target_body_name else _get_main_body(part)

    if source.com_object == target.com_object:
        raise RuntimeError(
            "Source and target body are the same. "
            "Create a separate body first before boolean operation."
        )

    sf = ShapeFactory(part.shape_factory.com_object)
    sf.add_new_intersect(source)
    part.update()
    return {"operation": "BooleanIntersect", "source": source_body_name, "target": target.name}


# ---------------------------------------------------------------------------
# Dress-up features
# ---------------------------------------------------------------------------

def create_shell(
    feature_name: str,
    face_index: int = 1,
    internal_thickness: float = 1.0,
    external_thickness: float = 0.0,
) -> dict[str, Any]:
    """Create a Shell (hollow) feature.

    Args:
        feature_name: Name of the feature whose face to remove.
        face_index: Face index to remove (1-based).
        internal_thickness: Internal thickness in mm.
        external_thickness: External thickness in mm.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = _try_get_face_ref(part, feature_name, face_index)

    sf = ShapeFactory(part.shape_factory.com_object)
    shell = sf.add_new_shell(ref, float(internal_thickness), float(external_thickness))
    part.update()
    return {"feature": "Shell", "name": shell.name, "internal": internal_thickness, "external": external_thickness}


def create_draft(
    feature_name: str,
    face_index: int = 1,
    angle: float = 5.0,
    direction: list[float] | None = None,
) -> dict[str, Any]:
    """Create a Draft feature.

    Args:
        feature_name: Feature whose face to draft.
        face_index: Face index.
        angle: Draft angle in degrees.
        direction: [x, y, z] draft direction vector.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref_face = _try_get_face_ref(part, feature_name, face_index)

    # Use XY plane as neutral reference
    ref_neutral = part.create_reference_from_object(part.origin_elements.plane_xy)
    ref_parting = part.create_reference_from_object(part.origin_elements.plane_xy)
    dir_vec = direction or [0.0, 0.0, 1.0]

    sf = ShapeFactory(part.shape_factory.com_object)
    draft = sf.add_new_draft(
        ref_face, ref_neutral, 0, ref_parting,
        float(dir_vec[0]), float(dir_vec[1]), float(dir_vec[2]),
    )
    # Set draft angle if possible via raw COM
    try:
        draft.com_object.Angle.Value = float(angle)
    except Exception:
        pass

    part.update()
    return {"feature": "Draft", "name": draft.name, "angle": angle}


def create_thickness(
    feature_name: str,
    face_index: int = 1,
    offset: float = 1.0,
) -> dict[str, Any]:
    """Create a Thickness feature on a face."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = _try_get_face_ref(part, feature_name, face_index)

    sf = ShapeFactory(part.shape_factory.com_object)
    thickness = sf.add_new_thickness(ref, float(offset))
    part.update()
    return {"feature": "Thickness", "name": thickness.name, "offset": offset}


# ---------------------------------------------------------------------------
# Surface-based features
# ---------------------------------------------------------------------------

def create_close_surface(surface_name: str) -> dict[str, Any]:
    """Close an open surface to create a solid.

    Args:
        surface_name: Name of the surface (GSD feature) to close.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    # Find surface in hybrid bodies or shapes
    ref = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == surface_name:
                ref = part.create_reference_from_object(shape)
                break
        if ref:
            break

    if ref is None:
        raise RuntimeError(f"Surface '{surface_name}' not found.")

    sf = ShapeFactory(part.shape_factory.com_object)
    close_surf = sf.add_new_close_surface(ref)
    part.update()
    return {"feature": "CloseSurface", "name": close_surf.name}


def create_sew_surface(surface_name: str, sewing_side: int = 1) -> dict[str, Any]:
    """Sew a surface onto a solid body.

    Args:
        surface_name: Name of the sewing surface.
        sewing_side: 1 = positive side, -1 = negative side.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    ref = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == surface_name:
                ref = part.create_reference_from_object(shape)
                break
        if ref:
            break

    if ref is None:
        raise RuntimeError(f"Surface '{surface_name}' not found.")

    sf = ShapeFactory(part.shape_factory.com_object)
    sew = sf.add_new_sew_surface(ref, int(sewing_side))
    part.update()
    return {"feature": "SewSurface", "name": sew.name}


def create_split(
    splitting_element_name: str,
    split_side: int = 1,
) -> dict[str, Any]:
    """Split a body with a surface or plane.

    Args:
        splitting_element_name: Name of the splitting surface/plane.
        split_side: 1 = keep positive side, -1 = keep negative side.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    ref = None
    # Try to find in bodies/shapes
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == splitting_element_name:
                ref = part.create_reference_from_object(shape)
                break
        if ref:
            break
    # Try origin planes
    if ref is None:
        plane_map = {
            "plane_xy": part.origin_elements.plane_xy,
            "plane_yz": part.origin_elements.plane_yz,
            "plane_zx": part.origin_elements.plane_zx,
        }
        key = splitting_element_name.lower()
        if key in plane_map:
            ref = part.create_reference_from_object(plane_map[key])

    if ref is None:
        raise RuntimeError(f"Splitting element '{splitting_element_name}' not found.")

    sf = ShapeFactory(part.shape_factory.com_object)
    split = sf.add_new_split(ref, int(split_side))
    part.update()
    return {"feature": "Split", "name": split.name}


def create_thick_surface(
    surface_name: str,
    top_offset: float = 1.0,
    bottom_offset: float = 1.0,
    offset_direction: int = 1,
) -> dict[str, Any]:
    """Thicken a surface into a solid.

    Args:
        surface_name: Name of the surface to thicken.
        top_offset: Top offset in mm.
        bottom_offset: Bottom offset in mm.
        offset_direction: 1 = normal, -1 = inverse.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    ref = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == surface_name:
                ref = part.create_reference_from_object(shape)
                break
        if ref:
            break

    if ref is None:
        raise RuntimeError(f"Surface '{surface_name}' not found.")

    sf = ShapeFactory(part.shape_factory.com_object)
    thick = sf.add_new_thick_surface(ref, int(offset_direction), float(top_offset), float(bottom_offset))
    part.update()
    return {"feature": "ThickSurface", "name": thick.name}


def create_remove_face(
    feature_name: str,
    face_index: int = 1,
) -> dict[str, Any]:
    """Remove a face from a solid body.

    Args:
        feature_name: Feature whose face to remove.
        face_index: Face index (1-based).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref = _try_get_face_ref(part, feature_name, face_index)

    sf = ShapeFactory(part.shape_factory.com_object)
    remove = sf.add_new_remove_faces(ref)
    part.update()
    return {"feature": "RemoveFace", "name": remove.name}


def create_replace_face(
    feature_name: str,
    surface_name: str,
    face_index: int = 1,
) -> dict[str, Any]:
    """Replace a face with a surface.

    Args:
        feature_name: Feature whose face to replace.
        surface_name: Name of the replacement surface.
        face_index: Face index (1-based).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref_face = _try_get_face_ref(part, feature_name, face_index)

    ref_surf = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == surface_name:
                ref_surf = part.create_reference_from_object(shape)
                break
        if ref_surf:
            break
    if ref_surf is None:
        for hb in part.hybrid_bodies:
            for hs in hb.hybrid_shapes:
                if hs.name == surface_name:
                    ref_surf = part.create_reference_from_object(hs)
                    break
            if ref_surf:
                break
    if ref_surf is None:
        raise RuntimeError(f"Surface '{surface_name}' not found.")

    sf = ShapeFactory(part.shape_factory.com_object)
    replace = sf.add_new_replace_face(ref_face, ref_surf)
    part.update()
    return {"feature": "ReplaceFace", "name": replace.name}
