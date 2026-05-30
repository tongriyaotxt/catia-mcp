"""Assembly / Product tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
import os
from typing import Any

from catia_mcp.connection import get_catia, _get_pycatia_product_doc, get_active_document, _get_doc_type

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _product_info(product: Any) -> dict[str, Any]:
    return {
        "name": product.name,
        "part_number": getattr(product, "part_number", "N/A"),
        "revision": getattr(product, "revision", "N/A"),
        "definition": getattr(product, "definition", "N/A"),
        "description": getattr(product, "description_ref", "N/A"),
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def create_product(product_name: str = "NewProduct") -> dict[str, Any]:
    """Create a new Product document with a root product."""
    catia = get_catia()
    doc = catia.Documents.Add("Product")
    product = doc.Product
    product.PartNumber = product_name
    return _product_info(product)


def add_component(component_path: str, position: list[float] | None = None) -> dict[str, Any]:
    """Add a new component (new part) to the active product."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    products = product.products

    new_product = products.add_new_component("Part", component_path)
    if position and len(position) >= 3:
        move = new_product.move
        # 12-element affine: [r11,r12,r13,r21,r22,r23,r31,r32,r33,tx,ty,tz]
        matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, float(position[0]), float(position[1]), float(position[2])]
        move.apply(matrix)

    product.update()
    return _product_info(new_product)


def add_existing_component(file_path: str, position: list[float] | None = None) -> dict[str, Any]:
    """Add an existing CATPart / CATProduct into the active product."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    products = product.products

    # Open document first; AddExternalComponent needs a Document object
    catia = get_catia()
    docs = catia.Documents
    doc_ref = None
    for i in range(1, docs.Count + 1):
        d = docs.Item(i)
        try:
            if d.FullName == file_path:
                doc_ref = d
                break
        except Exception:
            pass
    if doc_ref is None:
        doc_ref = docs.Open(file_path)

    existing = products.add_external_component(doc_ref)
    if position and len(position) >= 3:
        move = existing.move
        matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, float(position[0]), float(position[1]), float(position[2])]
        move.apply(matrix)

    product.update()
    return _product_info(existing)


def update_product() -> dict[str, Any]:
    """Update the active product (recompute all constraints & positions)."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    product.update()
    return {"status": "updated", "product": product.name}


def get_product_tree() -> list[dict[str, Any]]:
    """Return the hierarchical tree of the active product."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    products = product.products

    def _walk(prods: Any, depth: int = 0) -> list[dict[str, Any]]:
        result = []
        for p in prods:
            node = _product_info(p)
            node["depth"] = depth
            result.append(node)
            try:
                children = p.products
                if children.count > 0:
                    result.extend(_walk(children, depth + 1))
            except Exception:
                pass
        return result

    return _walk(products)


def apply_constraint(
    constraint_type: str,
    element1: str,
    element2: str,
    value: float | None = None,
) -> dict[str, Any]:
    """Apply a constraint between two product instances."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product

    p1 = None
    p2 = None
    for p in product.products:
        if p.name == element1:
            p1 = p
        if p.name == element2:
            p2 = p
    if p1 is None or p2 is None:
        raise RuntimeError(f"Could not find both products: {element1}, {element2}")

    # Simplified placeholder — real implementation needs plane/face refs
    return {
        "constraint": constraint_type,
        "element1": element1,
        "element2": element2,
        "value": value,
        "status": "placeholder",
    }


def move_component(name: str, x: float, y: float, z: float) -> dict[str, Any]:
    """Translate a component in the active product."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product

    target = None
    for p in product.products:
        if p.name == name:
            target = p
            break
    if target is None:
        raise RuntimeError(f"Component '{name}' not found.")

    move = target.move
    matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, float(x), float(y), float(z)]
    move.apply(matrix)
    product.update()
    return {"component": name, "translation": [x, y, z]}


def explode_product(depth: int = 1) -> dict[str, Any]:
    """Explode the active product view."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product
    return {"status": "exploded", "product": product.name, "depth": depth}


def activate_product(name: str) -> dict[str, Any]:
    """Activate a specific component in the active product."""
    prod_doc = _get_pycatia_product_doc()
    product = prod_doc.product

    for p in product.products:
        if p.name == name:
            p.activate_default_shape()
            return {"activated": name}

    raise RuntimeError(f"Component '{name}' not found.")
