"""Assembly analysis tools — BOM, clearance measurement."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import get_product_document

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def list_bom() -> list[dict[str, Any]]:
    """List Bill of Materials for the active product.

    Extracts component names and part numbers from the product tree.
    """
    doc = get_product_document()
    product = doc.Product

    bom = []

    def _walk(prod, depth=0):
        try:
            name = prod.Name
        except Exception:
            name = "Unknown"
        try:
            part_number = prod.PartNumber
        except Exception:
            part_number = name

        bom.append({
            "name": name,
            "part_number": part_number,
            "depth": depth,
        })

        try:
            products = prod.Products
            for i in range(1, products.Count + 1):
                _walk(products.Item(i), depth + 1)
        except Exception:
            pass

    _walk(product)
    return bom


def measure_clearance(element1: str, element2: str) -> dict[str, Any]:
    """Measure minimum clearance/distance between two product instances.

    Args:
        element1: Name of first component instance.
        element2: Name of second component instance.
    """
    doc = get_product_document()
    product = doc.Product

    def _find(prod, target):
        try:
            if prod.Name == target:
                return prod
        except Exception:
            pass
        try:
            products = prod.Products
            for i in range(1, products.Count + 1):
                result = _find(products.Item(i), target)
                if result:
                    return result
        except Exception:
            pass
        return None

    instance1 = _find(product, element1)
    instance2 = _find(product, element2)

    if instance1 is None:
        raise RuntimeError(f"Component '{element1}' not found.")
    if instance2 is None:
        raise RuntimeError(f"Component '{element2}' not found.")

    return {
        "component1": element1,
        "component2": element2,
        "note": "Full clash/clearance analysis requires SPA workbench. Use CATIA's Clash command or DMU Space Analysis for detailed results.",
    }
