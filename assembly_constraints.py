"""Assembly constraint tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from pycatia.enumeration.enums import CatConstraintType

from catia_mcp.connection import _get_pycatia_product_doc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_constraints(product):
    """Return the Constraints collection for a product."""
    return product.constraints()


def _find_product(products, name: str):
    """Find a product by name in a Products collection."""
    for p in products:
        if p.name == name:
            return p
    raise RuntimeError(f"Product instance '{name}' not found.")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def add_assembly_fix_constraint(component_name: str) -> dict[str, Any]:
    """Fix a component in space."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp = _find_product(product.products, component_name)
    ref = product.create_reference_from_name(comp.name)
    cst = constraints.add_mono_elt_cst(CatConstraintType.catCstTypeReference, ref)

    product.update()
    return {"constraint": "Fix", "component": component_name}


def add_assembly_offset_constraint(
    component1: str,
    component2: str,
    offset: float = 0.0,
) -> dict[str, Any]:
    """Add an offset constraint between two components."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp1 = _find_product(product.products, component1)
    comp2 = _find_product(product.products, component2)
    ref1 = product.create_reference_from_name(comp1.name)
    ref2 = product.create_reference_from_name(comp2.name)
    cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeDistance, ref1, ref2)
    try:
        cst.dimension.value = float(offset)
    except Exception:
        pass

    product.update()
    return {"constraint": "Offset", "component1": component1, "component2": component2, "offset": offset}


def add_assembly_angle_constraint(
    component1: str,
    component2: str,
    angle: float = 90.0,
) -> dict[str, Any]:
    """Add an angle constraint between two components."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp1 = _find_product(product.products, component1)
    comp2 = _find_product(product.products, component2)
    ref1 = product.create_reference_from_name(comp1.name)
    ref2 = product.create_reference_from_name(comp2.name)
    cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeAngle, ref1, ref2)
    try:
        cst.dimension.value = float(angle)
    except Exception:
        pass

    product.update()
    return {"constraint": "Angle", "component1": component1, "component2": component2, "angle": angle}


def add_assembly_coincidence_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a coincidence constraint between two components."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp1 = _find_product(product.products, component1)
    comp2 = _find_product(product.products, component2)
    ref1 = product.create_reference_from_name(comp1.name)
    ref2 = product.create_reference_from_name(comp2.name)
    cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeOn, ref1, ref2)

    product.update()
    return {"constraint": "Coincidence", "component1": component1, "component2": component2}


def add_assembly_parallelism_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a parallelism constraint between two components."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp1 = _find_product(product.products, component1)
    comp2 = _find_product(product.products, component2)
    ref1 = product.create_reference_from_name(comp1.name)
    ref2 = product.create_reference_from_name(comp2.name)
    cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeParallelism, ref1, ref2)

    product.update()
    return {"constraint": "Parallelism", "component1": component1, "component2": component2}


def add_assembly_perpendicularity_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a perpendicularity constraint between two components."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp1 = _find_product(product.products, component1)
    comp2 = _find_product(product.products, component2)
    ref1 = product.create_reference_from_name(comp1.name)
    ref2 = product.create_reference_from_name(comp2.name)
    cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypePerpendicularity, ref1, ref2)

    product.update()
    return {"constraint": "Perpendicularity", "component1": component1, "component2": component2}


def add_assembly_contact_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a surface contact constraint between two components."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    comp1 = _find_product(product.products, component1)
    comp2 = _find_product(product.products, component2)
    ref1 = product.create_reference_from_name(comp1.name)
    ref2 = product.create_reference_from_name(comp2.name)
    cst = constraints.add_bi_elt_cst(CatConstraintType.catCstTypeSurfContact, ref1, ref2)

    product.update()
    return {"constraint": "Contact", "component1": component1, "component2": component2}


def list_assembly_constraints() -> list[dict[str, Any]]:
    """List all assembly constraints."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

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


def delete_assembly_constraint(constraint_name: str) -> dict[str, Any]:
    """Delete an assembly constraint by name."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    constraints = _get_constraints(product)

    for i in range(1, constraints.count + 1):
        cst = constraints.item(i)
        if cst.name == constraint_name:
            constraints.remove(i)
            product.update()
            return {"deleted": constraint_name}

    raise RuntimeError(f"Constraint '{constraint_name}' not found.")


def update_assembly_constraints() -> dict[str, Any]:
    """Update the assembly constraints."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    product.update()
    return {"status": "updated", "product": product.name}
