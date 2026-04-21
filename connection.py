"""CATIA COM connection manager — supports both raw win32com and pycatia wrappers."""

from __future__ import annotations

import logging
import threading
from typing import Any

import win32com.client

logger = logging.getLogger(__name__)


class CatiaConnection:
    """Singleton connection manager for CATIA COM automation."""

    _instance: CatiaConnection | None = None
    _lock = threading.Lock()

    def __new__(cls) -> CatiaConnection:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._catia: Any | None = None
        return cls._instance

    @property
    def catia(self) -> Any:
        """Return the CATIA Application COM object, reconnecting if necessary."""
        if self._catia is None:
            self._connect()
        return self._catia

    def _connect(self) -> Any:
        """Connect to an existing CATIA instance or start a new one."""
        try:
            self._catia = win32com.client.GetActiveObject("CATIA.Application")
            logger.info("Connected to existing CATIA instance.")
        except Exception:
            logger.info("No running CATIA instance found; starting new one.")
            self._catia = win32com.client.Dispatch("CATIA.Application")
            self._catia.Visible = True
        return self._catia

    def disconnect(self) -> None:
        """Release the COM reference (does not close CATIA)."""
        self._catia = None
        logger.info("Disconnected from CATIA COM object.")

    def ensure_visible(self) -> None:
        """Make sure the CATIA window is visible."""
        self.catia.Visible = True

    @property
    def is_connected(self) -> bool:
        """Check whether we currently hold a COM reference."""
        return self._catia is not None


def get_catia() -> Any:
    """Convenience function: returns the CATIA Application object."""
    return CatiaConnection().catia


def _get_doc_type(doc: Any) -> str:
    """Safely determine document type via Type property or file extension fallback."""
    try:
        return doc.Type
    except Exception:
        pass
    try:
        name = doc.Name
        if name.upper().endswith(".CATPART"):
            return "Part"
        if name.upper().endswith(".CATPRODUCT"):
            return "Product"
        if name.upper().endswith(".CATDRAWING"):
            return "Drawing"
    except Exception:
        pass
    return "Unknown"


def get_active_document() -> Any:
    """Return the active CATIA document or raise an error."""
    catia = get_catia()
    try:
        return catia.ActiveDocument
    except Exception as exc:
        raise RuntimeError("No active document in CATIA.") from exc


def get_part_document() -> Any:
    """Return the active document asserting it is a Part document."""
    doc = get_active_document()
    doc_type = _get_doc_type(doc)
    if doc_type != "Part":
        raise RuntimeError(f"Active document is not a Part document (type={doc_type}).")
    return doc


def get_product_document() -> Any:
    """Return the active document asserting it is a Product document."""
    doc = get_active_document()
    doc_type = _get_doc_type(doc)
    if doc_type != "Product":
        raise RuntimeError(f"Active document is not a Product document (type={doc_type}).")
    return doc


# ---------------------------------------------------------------------------
# pycatia helpers (used by tools that need early-binding signatures)
# ---------------------------------------------------------------------------

def _get_pycatia_part_doc(doc: Any | None = None):
    """Wrap a raw Part Document COM object in pycatia's PartDocument."""
    from pycatia.mec_mod_interfaces.part_document import PartDocument
    if doc is None:
        doc = get_part_document()
    return PartDocument(doc.com_object if hasattr(doc, "com_object") else doc)


def _get_pycatia_product_doc(doc: Any | None = None):
    """Wrap a raw Product Document COM object in pycatia's ProductDocument."""
    from pycatia.product_structure_interfaces.product_document import ProductDocument
    if doc is None:
        doc = get_product_document()
    return ProductDocument(doc.com_object if hasattr(doc, "com_object") else doc)
