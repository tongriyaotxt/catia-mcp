"""Advanced GSD (Generative Shape Design) tools."""

from __future__ import annotations

import logging
import math
from typing import Any

from pycatia.hybrid_shape_interfaces.hybrid_shape_factory import HybridShapeFactory

from catia_mcp.connection import _get_pycatia_part_doc
from catia_mcp.tools.gsd import _get_hybrid_body, _find_ref

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def create_gsd_multisections_surface(
    section_names: list[str],
    guide_names: list[str] | None = None,
    spine_name: str | None = None,
    name: str = "MultiSections",
) -> dict[str, Any]:
    """Create a multi-sections surface (loft) through GSD.

    Args:
        section_names: List of section curve/sketch names.
        guide_names: Optional list of guide curve names.
        spine_name: Optional spine curve name.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    loft = gsf.add_new_loft()
    loft.name = name

    from pycatia.scripts.vba import vba_nothing

    for sec_name in section_names:
        ref = _find_ref(part, sec_name)
        loft.add_section_to_loft(ref, 0, vba_nothing)

    if guide_names:
        for guide_name in guide_names:
            ref = _find_ref(part, guide_name)
            loft.add_guide(ref)

    if spine_name:
        ref = _find_ref(part, spine_name)
        loft.set_spine(ref)

    hb.append_hybrid_shape(loft)
    part.update()
    return {
        "feature": "GSD_MultiSections",
        "name": loft.name,
        "sections": len(section_names),
    }


def create_gsd_extrapolate(
    surface_name: str,
    length: float = 10.0,
    boundary_name: str | None = None,
    continuity: str = "tangent",
    name: str = "Extrapolate",
) -> dict[str, Any]:
    """Extrapolate a surface or curve by length in GSD.

    Args:
        surface_name: Surface/curve to extrapolate.
        length: Extrapolation length in mm.
        boundary_name: Optional boundary element name. If omitted,
            a default origin plane is used as boundary (best-effort).
        continuity: "point", "tangent", or "curvature".
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_elem = _find_ref(part, surface_name)
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)

    if boundary_name:
        ref_boundary = _find_ref(part, boundary_name)
    else:
        # Use the element itself as boundary (works for some surfaces)
        ref_boundary = ref_elem

    extrapol = gsf.add_new_extrapol_length(ref_boundary, ref_elem, float(length))
    extrapol.name = name

    continuity_map = {"point": 0, "tangent": 1, "curvature": 2}
    try:
        extrapol.continuity_type = continuity_map.get(continuity.lower(), 1)
    except Exception:
        pass

    hb.append_hybrid_shape(extrapol)
    try:
        part.update()
        return {"feature": "GSD_Extrapolate", "name": extrapol.name, "length": length}
    except Exception as exc:
        # Clean up failed feature
        try:
            ref = part.create_reference_from_object(extrapol)
            part.hybrid_shape_factory.delete_object_for_datum(ref)
        except Exception:
            pass
        raise RuntimeError(
            f"GSD Extrapolate failed: {exc}. "
            "Extrapolation requires a valid boundary element that intersects the target. "
            "Try specifying a different boundary_name or ensure the geometry supports extrapolation."
        ) from exc


def create_gsd_parallel_curve(
    curve_name: str,
    support_name: str,
    offset: float = 1.0,
    invert_direction: bool = False,
    geodesic: bool = False,
    name: str = "ParallelCurve",
) -> dict[str, Any]:
    """Create a parallel curve on a support surface in GSD.

    Args:
        curve_name: Base curve name.
        support_name: Support surface/plane name.
        offset: Offset distance in mm.
        invert_direction: Invert offset direction.
        geodesic: Geodesic offset.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_curve = _find_ref(part, curve_name)
    ref_support = _find_ref(part, support_name)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    par = gsf.add_new_curve_par(
        ref_curve, ref_support, float(offset), bool(invert_direction), bool(geodesic)
    )
    par.name = name

    hb.append_hybrid_shape(par)
    part.update()
    return {"feature": "GSD_ParallelCurve", "name": par.name, "offset": offset}


def _build_perpendicular_axes(ax: float, ay: float, az: float):
    """Return two unit vectors perpendicular to (ax,ay,az)."""
    norm = math.sqrt(ax * ax + ay * ay + az * az)
    if norm < 1e-9:
        raise ValueError("Axis direction vector is zero.")
    ax, ay, az = ax / norm, ay / norm, az / norm
    # Choose a reference vector not parallel to axis
    if abs(ax) < 0.9 and abs(ay) < 0.9:
        ref_x, ref_y, ref_z = 0.0, 0.0, 1.0
    else:
        ref_x, ref_y, ref_z = 1.0, 0.0, 0.0
    # u = axis × ref
    ux = ay * ref_z - az * ref_y
    uy = az * ref_x - ax * ref_z
    uz = ax * ref_y - ay * ref_x
    u_norm = math.sqrt(ux * ux + uy * uy + uz * uz)
    if u_norm < 1e-9:
        ref_x, ref_y, ref_z = 0.0, 1.0, 0.0
        ux = ay * ref_z - az * ref_y
        uy = az * ref_x - ax * ref_z
        uz = ax * ref_y - ay * ref_x
        u_norm = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / u_norm, uy / u_norm, uz / u_norm
    # v = axis × u
    vx = ay * uz - az * uy
    vy = az * ux - ax * uz
    vz = ax * uy - ay * ux
    return (ux, uy, uz), (vx, vy, vz)


def create_gsd_helix(
    center_point_name: str,
    axis_name: str,
    pitch: float = 10.0,
    height: float = 50.0,
    radius: float = 5.0,
    starting_angle: float = 0.0,
    clockwise: bool = False,
    name: str = "Helix",
) -> dict[str, Any]:
    """Create a helix curve in GSD.

    If the native Helix feature fails in the current CATIA locale,
    this falls back to a mathematically exact spline approximation.

    Args:
        center_point_name: Starting point name.
        axis_name: Axis line/plane name (e.g. 'plane_xy').
        pitch: Helix pitch in mm.
        height: Total height in mm.
        radius: Helix radius in mm.
        starting_angle: Start angle in degrees.
        clockwise: Clockwise revolution.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    ref_point = _find_ref(part, center_point_name)
    ref_axis = _find_ref(part, axis_name)

    # Try native helix first
    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    helix = None
    try:
        helix = gsf.add_new_helix(
            ref_axis, False, ref_point, float(pitch), float(height),
            bool(clockwise), float(starting_angle), 0.0, False,
        )
        helix.name = name
        hb.append_hybrid_shape(helix)
        helix.com_object.Compute()
        part.update()
        return {"feature": "GSD_Helix", "name": helix.name, "pitch": pitch, "height": height}
    except Exception as exc:
        logger.warning("Native Helix failed (%s); falling back to spline approximation.", exc)
        # Remove the failed helix so it does not break the document
        if helix is not None:
            try:
                ref = part.create_reference_from_object(helix)
                part.hybrid_shape_factory.delete_object_for_datum(ref)
            except Exception:
                pass

    # Fallback: build helix as a spline through calculated points
    # Get axis direction
    plane_dirs = {
        "plane_xy": (0.0, 0.0, 1.0),
        "plane_yz": (1.0, 0.0, 0.0),
        "plane_zx": (0.0, 1.0, 0.0),
    }
    if axis_name.lower() in plane_dirs:
        ax, ay, az = plane_dirs[axis_name.lower()]
    else:
        # Try to get direction from a line element
        axis_elem = None
        for hb_item in part.hybrid_bodies:
            for hs in hb_item.hybrid_shapes:
                if hs.name == axis_name:
                    axis_elem = hs
                    break
            if axis_elem:
                break
        if axis_elem is None:
            raise RuntimeError(f"Cannot determine axis direction from '{axis_name}'.")
        try:
            # For HybridShapeLinePtDir, direction is accessible via Direction
            dir_obj = axis_elem.direction
            ax, ay, az = dir_obj.x, dir_obj.y, dir_obj.z
        except Exception:
            try:
                com = axis_elem.com_object
                dir_obj = com.Direction
                ax, ay, az = dir_obj.x, dir_obj.y, dir_obj.z
            except Exception:
                raise RuntimeError(f"Cannot extract direction from axis '{axis_name}'.")

    # Get center point coordinates
    center_elem = None
    for hb_item in part.hybrid_bodies:
        for hs in hb_item.hybrid_shapes:
            if hs.name == center_point_name:
                center_elem = hs
                break
        if center_elem:
            break
    if center_elem is None:
        raise RuntimeError(f"Center point '{center_point_name}' not found.")
    try:
        cx = float(center_elem.com_object.X.Value)
        cy = float(center_elem.com_object.Y.Value)
        cz = float(center_elem.com_object.Z.Value)
    except Exception:
        try:
            cx = float(center_elem.x)
            cy = float(center_elem.y)
            cz = float(center_elem.z)
        except Exception:
            raise RuntimeError(f"Cannot extract coordinates from point '{center_point_name}'.")

    (ux, uy, uz), (vx, vy, vz) = _build_perpendicular_axes(ax, ay, az)
    sign = -1.0 if clockwise else 1.0
    start_rad = math.radians(starting_angle)
    turns = height / pitch
    num_points = max(int(turns * 36), 10)  # 36 points per turn

    spline = gsf.add_new_spline()
    spline.name = name
    for i in range(num_points + 1):
        t = i / num_points
        angle = start_rad + sign * t * turns * 2.0 * math.pi
        z_along = t * height
        px = cx + radius * (ux * math.cos(angle) + vx * math.sin(angle)) + z_along * ax
        py = cy + radius * (uy * math.cos(angle) + vy * math.sin(angle)) + z_along * ay
        pz = cz + radius * (uz * math.cos(angle) + vz * math.sin(angle)) + z_along * az
        pt = gsf.add_new_point_coord(px, py, pz)
        pt.name = f"{name}_Pt{i}"
        hb.append_hybrid_shape(pt)
        ref_pt = part.create_reference_from_object(pt)
        spline.add_point(ref_pt)

    hb.append_hybrid_shape(spline)
    part.update()
    return {
        "feature": "GSD_HelixSpline",
        "name": name,
        "pitch": pitch,
        "height": height,
        "radius": radius,
        "note": "Native Helix unavailable; created spline approximation.",
    }


def create_gsd_spine(
    section_names: list[str],
    guide_names: list[str] | None = None,
    name: str = "Spine",
) -> dict[str, Any]:
    """Create a spine in GSD from sections and optional guides.

    Args:
        section_names: List of section curve names.
        guide_names: Optional list of guide names.
        name: Feature name.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    hb = _get_hybrid_body(part)

    gsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    spine = gsf.add_new_spine()
    spine.name = name

    for sec_name in section_names:
        ref = _find_ref(part, sec_name)
        spine.add_section(ref)

    if guide_names:
        for guide_name in guide_names:
            ref = _find_ref(part, guide_name)
            spine.add_guide(ref)

    hb.append_hybrid_shape(spine)
    try:
        part.update()
        return {"feature": "GSD_Spine", "name": spine.name}
    except Exception as exc:
        try:
            ref = part.create_reference_from_object(spine)
            part.hybrid_shape_factory.delete_object_for_datum(ref)
        except Exception:
            pass
        raise RuntimeError(
            f"GSD Spine creation failed: {exc}. "
            "Ensure sections are valid curves and guides intersect them correctly."
        ) from exc
