"""Sheet Metal Design tools for CATIA — raw COM backed with graceful fallback.

Requires the Sheet Metal Design workbench (SMT) to be available.
If SMT is not licensed, operations will return a clear error.
"""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import _get_pycatia_part_doc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_smt_factory(part):
    """Return the Sheet-Metal factory (Part::SheetMetalFactory) via raw COM."""
    try:
        return part.com_object.GetItem("CATSmfWksPart")
    except Exception:
        return None


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


def _smt_unavailable():
    raise RuntimeError(
        "Sheet Metal Design (SMT) workbench is not available or not licensed. "
        "Ensure the SMT license is active in CATIA."
    )


# ---------------------------------------------------------------------------
# Wall / Base features
# ---------------------------------------------------------------------------

def create_wall(
    sketch_name: str,
    thickness: float = 1.0,
    reverse: bool = False,
) -> dict[str, Any]:
    """Create a Sheet-Metal wall from a sketch profile.

    Args:
        sketch_name: Name of the profile sketch.
        thickness: Wall thickness in mm.
        reverse: Reverse material side.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    sketch = body.sketches.item(sketch_name)
    ref = part.create_reference_from_object(sketch)

    try:
        wall = smt.AddNewWall(ref, float(thickness), bool(reverse))
        part.update()
        return {"feature": "Wall", "name": wall.Name, "thickness": thickness}
    except Exception as e:
        raise RuntimeError(f"Failed to create wall: {e}") from e


def create_bend(
    wall1_name: str,
    wall2_name: str,
    radius: float = 1.0,
    angle: float = 90.0,
) -> dict[str, Any]:
    """Create a bend between two walls.

    Args:
        wall1_name: First wall feature name.
        wall2_name: Second wall feature name.
        radius: Bend inner radius in mm.
        angle: Bend angle in degrees.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    wall1 = None
    wall2 = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == wall1_name:
                wall1 = shape
            if shape.name == wall2_name:
                wall2 = shape
        if wall1 and wall2:
            break

    if wall1 is None or wall2 is None:
        raise RuntimeError(f"Walls '{wall1_name}' / '{wall2_name}' not found.")

    try:
        bend = smt.AddNewBend(
            part.create_reference_from_object(wall1),
            part.create_reference_from_object(wall2),
            float(radius),
            float(angle),
        )
        part.update()
        return {"feature": "Bend", "name": bend.Name, "radius": radius, "angle": angle}
    except Exception as e:
        raise RuntimeError(f"Failed to create bend: {e}") from e


def create_flat_pattern() -> dict[str, Any]:
    """Create a flat pattern of the current sheet-metal part."""
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    try:
        flat = smt.AddNewFlatPattern()
        part.update()
        return {"feature": "FlatPattern", "name": flat.Name}
    except Exception as e:
        raise RuntimeError(f"Failed to create flat pattern: {e}") from e


# ---------------------------------------------------------------------------
# Cutout / Flange / Hem / Joggle / Corner Relief
# ---------------------------------------------------------------------------

def create_cutout(
    sketch_name: str,
    depth: float = 10.0,
) -> dict[str, Any]:
    """Create a sheet-metal cutout (Pocket through wall).

    Args:
        sketch_name: Name of the cutout profile sketch.
        depth: Cut depth in mm (usually set to "Through All" via large value).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    body = _get_main_body(part)

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    sketch = body.sketches.item(sketch_name)
    ref = part.create_reference_from_object(sketch)

    try:
        cut = smt.AddNewCutout(ref, float(depth))
        part.update()
        return {"feature": "Cutout", "name": cut.Name, "depth": depth}
    except Exception as e:
        raise RuntimeError(f"Failed to create cutout: {e}") from e


def create_flange(
    wall_name: str,
    length: float = 10.0,
    angle: float = 90.0,
    radius: float = 1.0,
) -> dict[str, Any]:
    """Create a flange on a wall edge.

    Args:
        wall_name: Name of the base wall.
        length: Flange length in mm.
        angle: Flange angle in degrees.
        radius: Bend radius in mm.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    wall = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == wall_name:
                wall = shape
                break
        if wall:
            break
    if wall is None:
        raise RuntimeError(f"Wall '{wall_name}' not found.")

    try:
        flange = smt.AddNewFlange(
            part.create_reference_from_object(wall),
            float(length),
            float(angle),
            float(radius),
        )
        part.update()
        return {"feature": "Flange", "name": flange.Name, "length": length, "angle": angle}
    except Exception as e:
        raise RuntimeError(f"Failed to create flange: {e}") from e


def create_hem(
    wall_name: str,
    length: float = 5.0,
    radius: float = 1.0,
) -> dict[str, Any]:
    """Create a hem on a wall edge.

    Args:
        wall_name: Name of the base wall.
        length: Hem length in mm.
        radius: Bend radius in mm.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    wall = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == wall_name:
                wall = shape
                break
        if wall:
            break
    if wall is None:
        raise RuntimeError(f"Wall '{wall_name}' not found.")

    try:
        hem = smt.AddNewHem(
            part.create_reference_from_object(wall),
            float(length),
            float(radius),
        )
        part.update()
        return {"feature": "Hem", "name": hem.Name, "length": length}
    except Exception as e:
        raise RuntimeError(f"Failed to create hem: {e}") from e


def create_joggle(
    wall_name: str,
    depth: float = 2.0,
    radius: float = 1.0,
) -> dict[str, Any]:
    """Create a joggle on a wall.

    Args:
        wall_name: Name of the base wall.
        depth: Joggle depth in mm.
        radius: Bend radius in mm.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    wall = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == wall_name:
                wall = shape
                break
        if wall:
            break
    if wall is None:
        raise RuntimeError(f"Wall '{wall_name}' not found.")

    try:
        joggle = smt.AddNewJoggle(
            part.create_reference_from_object(wall),
            float(depth),
            float(radius),
        )
        part.update()
        return {"feature": "Joggle", "name": joggle.Name, "depth": depth}
    except Exception as e:
        raise RuntimeError(f"Failed to create joggle: {e}") from e


def create_corner_relief(
    wall1_name: str,
    wall2_name: str,
    relief_type: str = "circular",
    size: float = 5.0,
) -> dict[str, Any]:
    """Create a corner relief between two walls.

    Args:
        wall1_name: First wall feature name.
        wall2_name: Second wall feature name.
        relief_type: "circular" or "square".
        size: Relief size in mm.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    smt = _get_smt_factory(part)
    if smt is None:
        _smt_unavailable()

    wall1 = None
    wall2 = None
    for body in part.bodies:
        for shape in body.shapes:
            if shape.name == wall1_name:
                wall1 = shape
            if shape.name == wall2_name:
                wall2 = shape
        if wall1 and wall2:
            break
    if wall1 is None or wall2 is None:
        raise RuntimeError(f"Walls '{wall1_name}' / '{wall2_name}' not found.")

    try:
        relief = smt.AddNewCornerRelief(
            part.create_reference_from_object(wall1),
            part.create_reference_from_object(wall2),
            relief_type == "circular",
            float(size),
        )
        part.update()
        return {"feature": "CornerRelief", "name": relief.Name, "type": relief_type, "size": size}
    except Exception as e:
        raise RuntimeError(f"Failed to create corner relief: {e}") from e
