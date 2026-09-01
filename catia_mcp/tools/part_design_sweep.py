"""Part Design sweep-like and transformation tools — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from pycatia.hybrid_shape_interfaces.hybrid_shape_factory import HybridShapeFactory
from pycatia.part_interfaces.shape_factory import ShapeFactory

from catia_mcp.connection import _get_pycatia_part_doc
from catia_mcp.tools.part_design import _ensure_body_in_work

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

def create_groove(sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Groove (swept cut) from a profile sketch."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    groove = sf.add_new_groove(sketch)
    part.update()
    return {"feature": "Groove", "sketch": sketch.name}


def create_scaling(
    feature_name: str,
    factor: float = 1.0,
) -> dict[str, Any]:
    """Create a Scaling transformation on a feature.

    Args:
        feature_name: Feature to scale.
        factor: Scale factor.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    feature = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                feature = shape
                break
        if feature:
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    ref = part.create_reference_from_object(feature)
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    scaling = sf.add_new_scaling(ref, float(factor))
    part.update()
    return {"feature": "Scaling", "name": scaling.name, "factor": factor}


def create_symmetry(
    feature_name: str,
    plane_name: str = "yz",
) -> dict[str, Any]:
    """Create a Symmetry transformation of a feature.

    Args:
        feature_name: Feature to mirror.
        plane_name: Mirror plane (xy/yz/zx).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    feature = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                feature = shape
                break
        if feature:
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    plane_map = {
        "xy": part.origin_elements.plane_xy,
        "yz": part.origin_elements.plane_yz,
        "zx": part.origin_elements.plane_zx,
    }
    plane = plane_map.get(plane_name.lower())
    if plane is None:
        raise ValueError(f"Unknown plane: {plane_name}")

    ref = part.create_reference_from_object(plane)

    # Symmetry acts on the current in-work object — make it the requested feature
    part.in_work_object = feature

    sf = ShapeFactory(part.shape_factory.com_object)
    sym = sf.add_new_symmetry_2(ref)
    part.update()
    return {"feature": "Symmetry", "name": sym.name, "mirrored": feature_name}


def create_affinity(
    x_ratio: float = 1.0,
    y_ratio: float = 1.0,
    z_ratio: float = 1.0,
) -> dict[str, Any]:
    """Create an Affinity transformation.

    Args:
        x_ratio: X scaling ratio.
        y_ratio: Y scaling ratio.
        z_ratio: Z scaling ratio.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    affinity = sf.add_new_affinity2(float(x_ratio), float(y_ratio), float(z_ratio))
    part.update()
    return {"feature": "Affinity", "x_ratio": x_ratio, "y_ratio": y_ratio, "z_ratio": z_ratio}


def create_blend() -> dict[str, Any]:
    """Create a Blend feature (placeholder — requires profile setup post-creation)."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    blend = sf.add_new_blend()
    part.update()
    return {"feature": "Blend", "name": blend.name, "note": "Requires further profile configuration in CATIA."}


def create_axis_to_axis(
    source_feature_name: str,
    target_feature_name: str,
) -> dict[str, Any]:
    """Create an Axis To Axis transformation.

    Args:
        source_feature_name: Source axis feature.
        target_feature_name: Target axis feature.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    source = None
    target = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == source_feature_name:
                source = shape
            if shape.name == target_feature_name:
                target = shape
    if source is None:
        raise RuntimeError(f"Source feature '{source_feature_name}' not found.")
    if target is None:
        raise RuntimeError(f"Target feature '{target_feature_name}' not found.")

    ref_source = part.create_reference_from_object(source)
    ref_target = part.create_reference_from_object(target)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    axis2axis = sf.add_new_axis_to_axis2(ref_source, ref_target)
    part.update()
    return {"feature": "AxisToAxis", "source": source_feature_name, "target": target_feature_name}


def create_circ_pattern(
    feature_name: str,
    instances: int = 3,
    angular_spacing: float = 120.0,
    total_angle: float = 360.0,
) -> dict[str, Any]:
    """Create a circular pattern of a feature.

    Args:
        feature_name: Feature to pattern.
        instances: Number of instances.
        angular_spacing: Angle between instances in degrees.
        total_angle: Total angle in degrees (360 = full circle).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    feature = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == feature_name:
                feature = shape
                break
        if feature:
            break
    if feature is None:
        raise RuntimeError(f"Feature '{feature_name}' not found.")

    ref = part.create_reference_from_object(feature)
    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)

    # Use the XY origin plane as rotation center and axis
    ref_center = part.create_reference_from_object(part.origin_elements.plane_xy)
    ref_axis = part.create_reference_from_object(part.origin_elements.plane_xy)

    pattern = sf.add_new_circ_pattern(
        ref,
        1,                       # copies in radial direction
        int(instances),          # copies in angular direction
        0.0,                     # step in radial direction
        float(angular_spacing),  # step in angular direction (degrees)
        1,                       # position along radial direction
        1,                       # position along angular direction
        ref_center,
        ref_axis,
        False,                   # reversed rotation axis
        0.0,                     # rotation angle
        False,                   # radius aligned
    )
    part.update()
    return {
        "feature": "CircPattern",
        "source": feature_name,
        "instances": instances,
        "angular_spacing": angular_spacing,
    }


def create_loft(
    section1_name: str,
    section2_name: str,
    section3_name: str | None = None,
    name: str = "Loft",
) -> dict[str, Any]:
    """Create a Loft (multi-sections surface) between sketches via GSD.

    The resulting surface can be turned into a solid with CloseSurface
    or ThickSurface afterwards.

    Args:
        section1_name: Name of first sketch/section.
        section2_name: Name of second sketch/section.
        section3_name: Optional third sketch/section.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)

    sketch1 = body.sketches.item(section1_name)
    sketch2 = body.sketches.item(section2_name)

    # Use HybridShapeFactory (GSD) for loft — Part Design ShapeFactory lacks section methods
    hsf_com = part.hybrid_shape_factory.com_object
    loft = hsf_com.AddNewLoft()
    loft.AddSectionToLoft(part.create_reference_from_object(sketch1).com_object, 1, None)
    loft.AddSectionToLoft(part.create_reference_from_object(sketch2).com_object, 1, None)
    if section3_name:
        sketch3 = body.sketches.item(section3_name)
        loft.AddSectionToLoft(part.create_reference_from_object(sketch3).com_object, 1, None)
    loft.Name = name

    # Append to first hybrid body (or create one)
    hybrid_bodies = part.hybrid_bodies
    if hybrid_bodies.count == 0:
        hb = hybrid_bodies.add()
        hb.name = "GeometricalSet.1"
    else:
        hb = hybrid_bodies.item(1)
    hb.com_object.AppendHybridShape(loft)

    part.update()
    return {"feature": "Loft", "name": loft.Name, "sections": [section1_name, section2_name] + ([section3_name] if section3_name else [])}


def create_helix(
    sketch_name: str,
    axis_name: str = "plane_xy",
    pitch: float = 10.0,
    height: float = 50.0,
    starting_angle: float = 0.0,
    name: str = "Helix",
) -> dict[str, Any]:
    """Create a Helix curve in GSD from a center point / axis.

    Args:
        sketch_name: Name of the sketch containing the helix center point.
        axis_name: Name of the axis/line for helix center.
        pitch: Helix pitch in mm.
        height: Helix height in mm.
        starting_angle: Starting angle in degrees.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)

    sketch = body.sketches.item(sketch_name)
    ref_point = part.create_reference_from_object(sketch)

    # Resolve the helix axis: origin planes or a named hybrid element
    plane_map = {
        "plane_xy": part.origin_elements.plane_xy,
        "plane_yz": part.origin_elements.plane_yz,
        "plane_zx": part.origin_elements.plane_zx,
    }
    axis_obj = plane_map.get(axis_name.lower())
    if axis_obj is None:
        for hb_item in part.hybrid_bodies:
            for hs in hb_item.hybrid_shapes:
                if hs.name == axis_name:
                    axis_obj = hs
                    break
            if axis_obj is not None:
                break
    if axis_obj is None:
        raise RuntimeError(f"Axis '{axis_name}' not found.")
    ref_axis = part.create_reference_from_object(axis_obj)

    # Use HybridShapeFactory for helix
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    try:
        helix = gsf.add_new_helix(
            ref_axis,
            False,  # invert axis
            ref_point,
            float(pitch),
            float(height),
            False,  # clockwise revolution
            float(starting_angle),
            0.0,    # taper angle
            False,  # taper outward
        )
        helix.name = name
    except Exception as e:
        raise RuntimeError(
            f"Helix creation failed (likely a COM type-conversion issue in this CATIA locale): {e}"
        ) from e

    hybrid_bodies = part.hybrid_bodies
    if hybrid_bodies.count == 0:
        hb = hybrid_bodies.add()
        hb.name = "GeometricalSet.1"
    else:
        hb = hybrid_bodies.item(1)
    hb.append_hybrid_shape(helix)

    part.update()
    return {"feature": "Helix", "name": helix.name, "pitch": pitch, "height": height}
