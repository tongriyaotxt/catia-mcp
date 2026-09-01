"""Additional Part Design tools — stiffener, advanced fillets."""

from __future__ import annotations

import logging
from typing import Any

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
# Tools
# ---------------------------------------------------------------------------


def create_stiffener(
    sketch_name: str | None = None,
    thickness: float = 1.0,
    reverse: bool = False,
) -> dict[str, Any]:
    """Create a Stiffener (rib with thickness) from a profile sketch.

    Args:
        sketch_name: Name of the sketch to use (last sketch if None).
        thickness: Stiffener thickness in mm.
        reverse: Reverse direction.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    sketch = _get_sketch(part, sketch_name)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    ref = part.create_reference_from_object(sketch)
    stiffener = sf.add_new_stiffener_from_ref(ref)
    try:
        stiffener.com_object.Thickness.Value = float(thickness)
    except Exception:
        pass
    if reverse:
        try:
            stiffener.com_object.IsFromTop = True
        except Exception:
            pass

    try:
        part.update()
        return {
            "feature": "Stiffener",
            "sketch": sketch.name,
            "thickness": thickness,
            "reverse": reverse,
            "name": getattr(stiffener, "name", "Stiffener"),
        }
    except Exception as exc:
        # Remove the failed feature to keep the document healthy
        try:
            sel = part_doc.selection
            sel.clear()
            sel.add(stiffener)
            sel.delete()
        except Exception:
            pass
        raise RuntimeError(
            f"Stiffener creation failed: {exc}. "
            "Stiffener requires an open-profile sketch that crosses an existing solid. "
            "In some localized CATIA versions, Stiffener via COM automation is not supported."
        ) from exc


def create_face_fillet(
    feature_name: str,
    radius: float,
    face1_index: int = 1,
    face2_index: int = 2,
) -> dict[str, Any]:
    """Create a Face-to-Face Fillet between two faces.

    Args:
        feature_name: Feature containing the faces.
        radius: Fillet radius in mm.
        face1_index: First face index (1-based).
        face2_index: Second face index (1-based).
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref1 = _try_get_face_ref(part, feature_name, face1_index)
    ref2 = _try_get_face_ref(part, feature_name, face2_index)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    fillet = sf.add_new_face_fillet(ref1, ref2, float(radius))
    part.update()
    return {"feature": "FaceFillet", "radius": radius, "name": getattr(fillet, "name", "FaceFillet")}


def create_tritangent_fillet(
    feature_name: str,
    remove_face_index: int = 1,
    face1_index: int = 2,
    face2_index: int = 3,
) -> dict[str, Any]:
    """Create a Tritangent Fillet (removes one face, rounds between two others).

    Args:
        feature_name: Feature containing the faces.
        remove_face_index: Face to remove (index).
        face1_index: First support face index.
        face2_index: Second support face index.
    """
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part
    ref_remove = _try_get_face_ref(part, feature_name, remove_face_index)
    ref1 = _try_get_face_ref(part, feature_name, face1_index)
    ref2 = _try_get_face_ref(part, feature_name, face2_index)

    sf = ShapeFactory(part.shape_factory.com_object)
    _ensure_body_in_work(part)
    fillet = sf.add_new_tritangent_fillet(ref1, ref2, ref_remove)
    part.update()
    return {"feature": "TritangentFillet", "name": getattr(fillet, "name", "TritangentFillet")}
