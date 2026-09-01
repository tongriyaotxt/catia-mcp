"""Parameters, formulas and knowledge tools for CATIA — pycatia-backed."""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import get_active_document, _get_doc_type, _get_pycatia_part_doc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_params_and_updater(doc: Any):
    """Return (parameters_collection, updater_callable) for Part or Product."""
    doc_type = _get_doc_type(doc)
    if doc_type == "Part":
        part_doc = _get_pycatia_part_doc(doc)
        part = part_doc.part
        return part.parameters, part.update
    elif doc_type == "Product":
        prod = doc.Product
        return prod.parameters, prod.update
    else:
        raise RuntimeError("Parameters only available for Part or Product documents.")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def list_parameters() -> list[dict[str, Any]]:
    """List all parameters in the active Part or Product."""
    doc = get_active_document()
    params, _ = _get_params_and_updater(doc)

    result = []
    for p in params:
        try:
            val = p.value
        except Exception:
            val = None
        result.append({
            "name": p.name,
            "value": val,
            # pycatia returns typed Parameter subclasses (Length, BoolParam, ...)
            "type": type(p).__name__,
        })
    return result


def get_parameter_value(name: str) -> dict[str, Any]:
    """Get the value of a named parameter."""
    doc = get_active_document()
    params, _ = _get_params_and_updater(doc)
    param = params.item(name)
    return {
        "name": param.name,
        "value": param.value,
        "type": type(param).__name__,
    }


def set_parameter_value(name: str, value: float | int | str) -> dict[str, Any]:
    """Set the value of a named parameter."""
    doc = get_active_document()
    params, updater = _get_params_and_updater(doc)
    param = params.item(name)
    param.value = value
    updater()
    return {"name": name, "new_value": value}


def add_parameter(
    name: str,
    value: float | int | str,
    param_type: str = "Length",
) -> dict[str, Any]:
    """Create a new user parameter."""
    doc = get_active_document()
    params, _ = _get_params_and_updater(doc)

    param = None
    if param_type in ("Length", "Angle"):
        param = params.create_dimension(name, param_type.upper(), float(value))
    elif param_type == "Real":
        param = params.create_real(name, float(value))
    elif param_type == "Integer":
        param = params.create_integer(name, int(value))
    elif param_type == "String":
        param = params.create_string(name, str(value))
    elif param_type == "Boolean":
        param = params.create_boolean(name, bool(value))
    else:
        param = params.create_dimension(name, "LENGTH", float(value))

    return {"name": param.name, "value": param.value, "type": param_type}


def add_formula(parameter_name: str, formula: str) -> dict[str, Any]:
    """Attach a design formula to an existing parameter."""
    doc = get_active_document()
    doc_type = _get_doc_type(doc)
    param = None
    if doc_type == "Part":
        part_doc = _get_pycatia_part_doc(doc)
        part = part_doc.part
        params = part.parameters
        param = params.item(parameter_name)
        relations = part.relations
    elif doc_type == "Product":
        prod = doc.Product
        params = prod.parameters
        param = params.item(parameter_name)
        relations = prod.relations
    else:
        raise RuntimeError("Formulas only available for Part or Product documents.")

    new_formula = relations.create_formula(
        f"Formula_{parameter_name}",
        "",
        param,
        formula,
    )
    if doc_type == "Part":
        part.update()
    else:
        prod.update()

    return {
        "parameter": parameter_name,
        "formula": formula,
        "result": param.value,
    }


def update() -> dict[str, Any]:
    """Force update (recompute) the active document."""
    doc = get_active_document()
    _, updater = _get_params_and_updater(doc)
    updater()
    return {"status": "updated", "document": doc.Name}
