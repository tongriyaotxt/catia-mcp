"""CATIA MCP Server — FastMCP entry point with all tool registrations."""

from __future__ import annotations

import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
from catia_mcp.connection import (
    CatiaConnection,
    get_active_document,
    get_part_document,
    get_product_document,
)

# ---------------------------------------------------------------------------
# Tool modules
# ---------------------------------------------------------------------------
from catia_mcp.tools import document
from catia_mcp.tools import sketcher
from catia_mcp.tools import sketcher_constraints
from catia_mcp.tools import part_design
from catia_mcp.tools import feature_edit
from catia_mcp.tools import selection
from catia_mcp.tools import assembly
from catia_mcp.tools import assembly_constraints
from catia_mcp.tools import part_design_advanced
from catia_mcp.tools import part_design_sweep
from catia_mcp.tools import gsd
from catia_mcp.tools import materials
from catia_mcp.tools import feature_tree
from catia_mcp.tools import view_control
from catia_mcp.tools import measurement
from catia_mcp.tools import parameters
from catia_mcp.tools import drafting
from catia_mcp.tools import export
from catia_mcp.tools import sheet_metal
from catia_mcp.tools import axis_systems
from catia_mcp.tools import sketcher_advanced
from catia_mcp.tools import part_design_more
from catia_mcp.tools import gsd_advanced
from catia_mcp.tools import drafting_advanced
from catia_mcp.tools import general_tools
from catia_mcp.tools import assembly_analysis

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server instantiation
# ---------------------------------------------------------------------------
mcp = FastMCP("catia-mcp", json_response=True)


# ---------------------------------------------------------------------------
# Lifecycle / meta
# ---------------------------------------------------------------------------
@mcp.tool()
def catia_status() -> dict[str, Any]:
    """Return the current CATIA connection status."""
    conn = CatiaConnection()
    return {
        "connected": conn.is_connected,
        "visible": conn.catia.Visible if conn.is_connected else None,
    }


@mcp.tool()
def ensure_catia_visible() -> dict[str, Any]:
    """Make sure the CATIA application window is visible."""
    CatiaConnection().ensure_visible()
    return {"status": "visible"}


# ===========================================================================
# DOCUMENT TOOLS
# ===========================================================================
@mcp.tool()
def list_documents() -> list[dict[str, Any]]:
    """List all currently open CATIA documents."""
    return document.list_documents()


@mcp.tool()
def get_active_document_info() -> dict[str, Any]:
    """Return information about the active document (name, type, path, saved state)."""
    return document.get_active_document_info()


@mcp.tool()
def open_document(file_path: str) -> dict[str, Any]:
    """Open an existing CATIA document (.CATPart, .CATProduct, .CATDrawing, etc.).

    Args:
        file_path: Absolute path to the file.
    """
    return document.open_document(file_path)


@mcp.tool()
def new_document(doc_type: str = "Part") -> dict[str, Any]:
    """Create a new CATIA document.

    Args:
        doc_type: One of "Part", "Product", "Drawing".
    """
    return document.new_document(doc_type)


@mcp.tool()
def save_document() -> dict[str, Any]:
    """Save the active document in place."""
    return document.save_document()


@mcp.tool()
def save_as_document(file_path: str) -> dict[str, Any]:
    """Save the active document to a new file path.

    Args:
        file_path: Target absolute path.
    """
    return document.save_as_document(file_path)


@mcp.tool()
def close_document(save: bool = False) -> dict[str, Any]:
    """Close the active document.

    Args:
        save: Save before closing.
    """
    return document.close_document(save)


@mcp.tool()
def close_all_documents(save: bool = False) -> dict[str, Any]:
    """Close all open documents.

    Args:
        save: Save each document before closing.
    """
    return document.close_all_documents(save)


@mcp.tool()
def get_document_type() -> str:
    """Return the type of the active document: Part, Product, or Drawing."""
    return document.get_document_type()


# ===========================================================================
# SKETCHER TOOLS
# ===========================================================================
@mcp.tool()
def create_sketch_on_plane(plane_name: str = "xy") -> dict[str, Any]:
    """Create a new sketch on a reference plane (xy, yz, or zx).

    Args:
        plane_name: One of "xy", "yz", "zx".
    """
    return sketcher.create_sketch_on_plane(plane_name)


@mcp.tool()
def add_point(x: float, y: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D point to the active or named sketch.

    Args:
        x: X coordinate in mm.
        y: Y coordinate in mm.
        sketch_name: Optional target sketch name.
    """
    return sketcher.add_point(x, y, sketch_name)


@mcp.tool()
def add_line(x1: float, y1: float, x2: float, y2: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D line to the active or named sketch.

    Args:
        x1, y1: Start point.
        x2, y2: End point.
        sketch_name: Optional target sketch name.
    """
    return sketcher.add_line(x1, y1, x2, y2, sketch_name)


@mcp.tool()
def add_circle(center_x: float, center_y: float, radius: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D circle to the active or named sketch.

    Args:
        center_x, center_y: Circle center.
        radius: Radius in mm.
        sketch_name: Optional target sketch name.
    """
    return sketcher.add_circle(center_x, center_y, radius, sketch_name)


@mcp.tool()
def add_rectangle(x1: float, y1: float, x2: float, y2: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Add an axis-aligned rectangle to the active or named sketch.

    Args:
        x1, y1: First corner.
        x2, y2: Opposite corner.
        sketch_name: Optional target sketch name.
    """
    return sketcher.add_rectangle(x1, y1, x2, y2, sketch_name)


@mcp.tool()
def add_arc(
    center_x: float,
    center_y: float,
    radius: float,
    start_angle: float,
    end_angle: float,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a circular arc to the active or named sketch (angles in degrees).

    Args:
        center_x, center_y: Arc center.
        radius: Radius in mm.
        start_angle: Start angle in degrees.
        end_angle: End angle in degrees.
        sketch_name: Optional target sketch name.
    """
    return sketcher.add_arc(center_x, center_y, radius, start_angle, end_angle, sketch_name)


@mcp.tool()
def close_sketch(sketch_name: str | None = None) -> dict[str, Any]:
    """Close a sketch edition (commit changes).

    Args:
        sketch_name: Optional sketch name (last sketch if None).
    """
    return sketcher.close_sketch(sketch_name)


@mcp.tool()
def get_sketch_elements(sketch_name: str | None = None) -> list[dict[str, Any]]:
    """List geometric elements in a sketch.

    Args:
        sketch_name: Optional sketch name (last sketch if None).
    """
    return sketcher.get_sketch_elements(sketch_name)


# ===========================================================================
# PART DESIGN TOOLS
# ===========================================================================
@mcp.tool()
def create_pad(length: float, sketch_name: str | None = None, reverse: bool = False) -> dict[str, Any]:
    """Create a Pad (extrusion) from a sketch profile.

    Args:
        length: Extrusion length in mm.
        sketch_name: Name of the sketch to use (last sketch if None).
        reverse: Extrude in reverse direction.
    """
    return part_design.create_pad(length, sketch_name, reverse)


@mcp.tool()
def create_pocket(length: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Pocket (cut extrusion) from a sketch profile.

    Args:
        length: Cut depth in mm.
        sketch_name: Name of the sketch to use (last sketch if None).
    """
    return part_design.create_pocket(length, sketch_name)


@mcp.tool()
def create_shaft(angle: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Shaft (revolution) from a sketch profile.

    Args:
        angle: Revolution angle in degrees (0-360).
        sketch_name: Name of the sketch to use.
    """
    return part_design.create_shaft(angle, sketch_name)


@mcp.tool()
def create_hole(
    diameter: float,
    depth: float,
    point_x: float = 0.0,
    point_y: float = 0.0,
    point_z: float = 0.0,
    direction_x: float = 0.0,
    direction_y: float = 0.0,
    direction_z: float = 1.0,
) -> dict[str, Any]:
    """Create a Hole feature on the main body.

    Args:
        diameter: Hole diameter in mm.
        depth: Hole depth in mm.
        point_x/y/z: Anchor point coordinates.
        direction_x/y/z: Hole axis direction vector.
    """
    return part_design.create_hole(
        diameter, depth, point_x, point_y, point_z, direction_x, direction_y, direction_z
    )


@mcp.tool()
def create_fillet(radius: float, edges: list[int] | None = None) -> dict[str, Any]:
    """Create an Edge Fillet on the main body.

    Args:
        radius: Fillet radius in mm.
        edges: Optional list of edge indices (all edges if None).
    """
    return part_design.create_fillet(radius, edges)


@mcp.tool()
def create_auto_fillet(fillet_radius: float, round_radius: float = 0.0) -> dict[str, Any]:
    """Create an AutoFillet on the main body (no edge selection needed).

    Args:
        fillet_radius: Outer fillet radius in mm.
        round_radius: Inner round radius in mm (optional).
    """
    return part_design.create_auto_fillet(fillet_radius, round_radius)


@mcp.tool()
def create_chamfer(length: float, edges: list[int] | None = None) -> dict[str, Any]:
    """Create a Chamfer on the main body.

    Args:
        length: Chamfer length in mm.
        edges: Optional list of edge indices.
    """
    return part_design.create_chamfer(length, edges)


@mcp.tool()
def create_mirror(feature_name: str, plane_name: str = "xy") -> dict[str, Any]:
    """Mirror a feature with respect to a plane.

    Args:
        feature_name: Name of the feature to mirror.
        plane_name: Mirror plane (xy/yz/zx).
    """
    return part_design.create_mirror(feature_name, plane_name)


@mcp.tool()
def create_pattern(
    feature_name: str,
    instances_x: int,
    spacing_x: float,
    instances_y: int = 1,
    spacing_y: float = 0.0,
) -> dict[str, Any]:
    """Create a rectangular pattern of a feature.

    Args:
        feature_name: Feature to pattern.
        instances_x: Number of instances in X.
        spacing_x: X spacing in mm.
        instances_y: Number of instances in Y.
        spacing_y: Y spacing in mm.
    """
    return part_design.create_pattern(feature_name, instances_x, spacing_x, instances_y, spacing_y)


@mcp.tool()
def create_rib(length: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Rib (sweep) from a profile sketch.

    Args:
        length: Rib length in mm.
        sketch_name: Center-curve sketch name.
    """
    return part_design.create_rib(length, sketch_name)


@mcp.tool()
def create_slot(length: float, sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Slot (groove sweep) from a profile sketch.

    Args:
        length: Slot length in mm.
        sketch_name: Center-curve sketch name.
    """
    return part_design.create_slot(length, sketch_name)


@mcp.tool()
def add_body(body_name: str = "NewBody") -> dict[str, Any]:
    """Add a new geometric body to the active part.

    Args:
        body_name: Name for the new body.
    """
    return part_design.add_body(body_name)


@mcp.tool()
def insert_in_body(source_body_name: str, target_body_name: str = "PartBody") -> dict[str, Any]:
    """Insert one body into another (Boolean add).

    Args:
        source_body_name: Body to insert.
        target_body_name: Destination body.
    """
    return part_design.insert_in_body(source_body_name, target_body_name)


# ===========================================================================
# ASSEMBLY TOOLS
# ===========================================================================
@mcp.tool()
def create_product(product_name: str = "NewProduct") -> dict[str, Any]:
    """Create a new Product document with a root product.

    Args:
        product_name: PartNumber for the root product.
    """
    return assembly.create_product(product_name)


@mcp.tool()
def add_component(component_path: str, position: list[float] | None = None) -> dict[str, Any]:
    """Add a new component (new part) to the active product.

    Args:
        component_path: Desired save path for the new CATPart.
        position: Optional [x, y, z] insertion position.
    """
    return assembly.add_component(component_path, position)


@mcp.tool()
def add_existing_component(file_path: str, position: list[float] | None = None) -> dict[str, Any]:
    """Add an existing CATPart / CATProduct into the active product.

    Args:
        file_path: Path to existing file.
        position: Optional [x, y, z] insertion position.
    """
    return assembly.add_existing_component(file_path, position)


@mcp.tool()
def update_product() -> dict[str, Any]:
    """Update the active product (recompute constraints & positions)."""
    return assembly.update_product()


@mcp.tool()
def get_product_tree() -> list[dict[str, Any]]:
    """Return the hierarchical component tree of the active product."""
    return assembly.get_product_tree()


@mcp.tool()
def apply_constraint(
    constraint_type: str,
    element1: str,
    element2: str,
    value: float | None = None,
) -> dict[str, Any]:
    """Apply a constraint between two product instances.

    Args:
        constraint_type: e.g. "Offset", "Angle", "Coincidence", "Contact".
        element1: Name of first product instance.
        element2: Name of second product instance.
        value: Constraint value where applicable.
    """
    return assembly.apply_constraint(constraint_type, element1, element2, value)


@mcp.tool()
def move_component(name: str, x: float, y: float, z: float) -> dict[str, Any]:
    """Translate a component in the active product.

    Args:
        name: Component instance name.
        x, y, z: Translation vector in mm.
    """
    return assembly.move_component(name, x, y, z)


@mcp.tool()
def explode_product(depth: int = 1) -> dict[str, Any]:
    """Explode the active product view.

    Args:
        depth: Explosion depth level.
    """
    return assembly.explode_product(depth)


@mcp.tool()
def activate_product(name: str) -> dict[str, Any]:
    """Activate a specific component in the active product (open in its own window).

    Args:
        name: Component instance name.
    """
    return assembly.activate_product(name)


# ===========================================================================
# MEASUREMENT TOOLS
# ===========================================================================
@mcp.tool()
def measure_distance(element1: str, element2: str) -> dict[str, Any]:
    """Measure the minimum distance between two named elements.

    Args:
        element1: Name of first geometric element.
        element2: Name of second geometric element.
    """
    return measurement.measure_distance(element1, element2)


@mcp.tool()
def measure_length(element_name: str) -> dict[str, Any]:
    """Measure the length of a curve or edge.

    Args:
        element_name: Name of the curve/edge.
    """
    return measurement.measure_length(element_name)


@mcp.tool()
def measure_area(element_name: str | None = None) -> dict[str, Any]:
    """Measure the surface area of a face or body.

    Args:
        element_name: Named face (measures PartBody if None).
    """
    return measurement.measure_area(element_name)


@mcp.tool()
def measure_volume() -> dict[str, Any]:
    """Measure the volume of the active PartBody."""
    return measurement.measure_volume()


@mcp.tool()
def measure_inertia(element_name: str | None = None) -> dict[str, Any]:
    """Compute inertia (mass properties) of a body or product.

    Args:
        element_name: Optional named element; otherwise active body/product.
    """
    return measurement.measure_inertia(element_name)


@mcp.tool()
def get_bounding_box(element_name: str | None = None) -> dict[str, Any]:
    """Return the axis-aligned bounding box of a body or product.

    Args:
        element_name: Optional named element.
    """
    return measurement.get_bounding_box(element_name)


# ===========================================================================
# PARAMETERS TOOLS
# ===========================================================================
@mcp.tool()
def list_parameters() -> list[dict[str, Any]]:
    """List all parameters in the active Part or Product."""
    return parameters.list_parameters()


@mcp.tool()
def get_parameter_value(name: str) -> dict[str, Any]:
    """Get the value of a named parameter.

    Args:
        name: Parameter name.
    """
    return parameters.get_parameter_value(name)


@mcp.tool()
def set_parameter_value(name: str, value: float | int | str) -> dict[str, Any]:
    """Set the value of a named parameter and update the document.

    Args:
        name: Parameter name.
        value: New value.
    """
    return parameters.set_parameter_value(name, value)


@mcp.tool()
def add_parameter(
    name: str,
    value: float | int | str,
    param_type: str = "Length",
) -> dict[str, Any]:
    """Create a new user parameter.

    Args:
        name: Parameter name.
        value: Initial value.
        param_type: "Length", "Angle", "Real", "Integer", "String", "Boolean".
    """
    return parameters.add_parameter(name, value, param_type)


@mcp.tool()
def add_formula(parameter_name: str, formula: str) -> dict[str, Any]:
    """Attach a design formula to an existing parameter.

    Args:
        parameter_name: Parameter to drive.
        formula: Formula expression (e.g. "Length_1 * 2 + 5mm").
    """
    return parameters.add_formula(parameter_name, formula)


@mcp.tool()
def update() -> dict[str, Any]:
    """Force update (recompute) the active document."""
    return parameters.update()


# ===========================================================================
# DRAFTING TOOLS
# ===========================================================================
@mcp.tool()
def create_drawing(
    drawing_name: str = "NewDrawing",
    standard: str = "ISO",
    sheet_format: str = "A4ISO",
) -> dict[str, Any]:
    """Create a new Drawing document.

    Args:
        drawing_name: Name for the drawing.
        standard: Drawing standard.
        sheet_format: Sheet format (A0ISO, A1ISO, A2ISO, A3ISO, A4ISO, etc.).
    """
    return drafting.create_drawing(drawing_name, standard, sheet_format)


@mcp.tool()
def create_sheet(sheet_format: str = "A4ISO", orientation: str = "Landscape") -> dict[str, Any]:
    """Add a new sheet to the active Drawing.

    Args:
        sheet_format: Sheet size format.
        orientation: "Landscape" or "Portrait".
    """
    return drafting.create_sheet(sheet_format, orientation)


@mcp.tool()
def create_view(
    view_name: str = "FrontView",
    x: float = 100.0,
    y: float = 100.0,
    scale: float = 1.0,
) -> dict[str, Any]:
    """Create a new view on the active sheet.

    Args:
        view_name: View identifier.
        x, y: Position on sheet in mm.
        scale: View scale.
    """
    return drafting.create_view(view_name, x, y, scale)


@mcp.tool()
def add_dimension(element_name: str, x: float, y: float) -> dict[str, Any]:
    """Add a dimension to a geometry element in the active Drawing view.

    Args:
        element_name: Name of the geometry to dimension.
        x, y: Dimension text position.
    """
    return drafting.add_dimension(element_name, x, y)


@mcp.tool()
def add_annotation(text: str, x: float, y: float) -> dict[str, Any]:
    """Add a text annotation to the active Drawing view.

    Args:
        text: Annotation text.
        x, y: Text position in mm.
    """
    return drafting.add_annotation(text, x, y)


@mcp.tool()
def update_sheet_links() -> dict[str, Any]:
    """Update all links in the Drawing (e.g. views linked to 3D parts)."""
    return drafting.update_sheet_links()


# ===========================================================================
# EXPORT TOOLS
# ===========================================================================
@mcp.tool()
def export_to_stl(file_path: str, binary: bool = True, tolerance: float = 0.1) -> dict[str, Any]:
    """Export the active Part or Product to STL.

    Args:
        file_path: Output .stl path.
        binary: Binary format (True) or ASCII (False).
        tolerance: Tessellation tolerance in mm.
    """
    return export.export_to_stl(file_path, binary, tolerance)


@mcp.tool()
def export_to_step(file_path: str, schema: str = "AP214") -> dict[str, Any]:
    """Export the active document to STEP.

    Args:
        file_path: Output .stp/.step path.
        schema: STEP schema (AP203, AP214, AP242).
    """
    return export.export_to_step(file_path, schema)


@mcp.tool()
def export_to_iges(file_path: str) -> dict[str, Any]:
    """Export the active document to IGES.

    Args:
        file_path: Output .igs/.iges path.
    """
    return export.export_to_iges(file_path)


@mcp.tool()
def export_to_pdf(file_path: str) -> dict[str, Any]:
    """Export the active Drawing to PDF.

    Args:
        file_path: Output .pdf path.
    """
    return export.export_to_pdf(file_path)


@mcp.tool()
def capture_screenshot(file_path: str, width: int = 1920, height: int = 1080) -> dict[str, Any]:
    """Capture the active 3D view to an image file.

    Args:
        file_path: Output image path (.bmp, .png, .jpg).
        width: Image width in pixels.
        height: Image height in pixels.
    """
    return export.capture_screenshot(file_path, width, height)


@mcp.tool()
def fit_all_in() -> dict[str, Any]:
    """Fit all geometry into the active view."""
    return export.fit_all_in()


@mcp.tool()
def update_view() -> dict[str, Any]:
    """Update (redraw) the active viewer."""
    return export.update_view()


# ===========================================================================
# SKETCHER CONSTRAINTS TOOLS
# ===========================================================================
@mcp.tool()
def add_length_constraint(
    element1: str | None = None,
    element2: str | None = None,
    value: float = 10.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a length or distance constraint to sketch elements."""
    return sketcher_constraints.add_length_constraint(element1, element2, value, sketch_name)


@mcp.tool()
def add_angle_constraint(
    element1: str,
    element2: str,
    value: float = 90.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add an angle constraint between two sketch elements."""
    return sketcher_constraints.add_angle_constraint(element1, element2, value, sketch_name)


@mcp.tool()
def add_radius_constraint(
    element: str,
    value: float = 5.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a radius constraint to a circle or arc."""
    return sketcher_constraints.add_radius_constraint(element, value, sketch_name)


@mcp.tool()
def add_diameter_constraint(
    element: str,
    value: float = 10.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a diameter constraint to a circle or arc."""
    return sketcher_constraints.add_diameter_constraint(element, value, sketch_name)


@mcp.tool()
def add_coincidence_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a coincidence constraint between two sketch elements."""
    return sketcher_constraints.add_coincidence_constraint(element1, element2, sketch_name)


@mcp.tool()
def add_parallelism_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a parallelism constraint between two lines."""
    return sketcher_constraints.add_parallelism_constraint(element1, element2, sketch_name)


@mcp.tool()
def add_perpendicularity_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a perpendicularity constraint between two lines."""
    return sketcher_constraints.add_perpendicularity_constraint(element1, element2, sketch_name)


@mcp.tool()
def add_concentricity_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a concentricity constraint between two circles/arcs."""
    return sketcher_constraints.add_concentricity_constraint(element1, element2, sketch_name)


@mcp.tool()
def add_tangency_constraint(
    element1: str,
    element2: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a tangency constraint between two curves."""
    return sketcher_constraints.add_tangency_constraint(element1, element2, sketch_name)


@mcp.tool()
def add_horizontality_constraint(
    element: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a horizontal constraint to a line."""
    return sketcher_constraints.add_horizontality_constraint(element, sketch_name)


@mcp.tool()
def add_verticality_constraint(
    element: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a vertical constraint to a line."""
    return sketcher_constraints.add_verticality_constraint(element, sketch_name)


@mcp.tool()
def add_fix_constraint(
    element: str,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a fix constraint to a sketch element."""
    return sketcher_constraints.add_fix_constraint(element, sketch_name)


@mcp.tool()
def list_constraints(sketch_name: str | None = None) -> list[dict[str, Any]]:
    """List all constraints in a sketch."""
    return sketcher_constraints.list_constraints(sketch_name)


# ===========================================================================
# FEATURE EDIT TOOLS
# ===========================================================================
@mcp.tool()
def edit_feature_parameter(
    feature_name: str,
    parameter_name: str,
    value: float,
) -> dict[str, Any]:
    """Edit a parameter of an existing feature (e.g. Length, FirstAngle)."""
    return feature_edit.edit_feature_parameter(feature_name, parameter_name, value)


@mcp.tool()
def delete_feature(feature_name: str) -> dict[str, Any]:
    """Delete a feature from the active part."""
    return feature_edit.delete_feature(feature_name)


@mcp.tool()
def get_feature_tree() -> list[dict[str, Any]]:
    """Return the hierarchical feature tree of the active part."""
    return feature_edit.get_feature_tree()


@mcp.tool()
def suppress_feature(feature_name: str) -> dict[str, Any]:
    """Suppress (deactivate) a feature."""
    return feature_edit.suppress_feature(feature_name)


@mcp.tool()
def activate_feature(feature_name: str) -> dict[str, Any]:
    """Activate a suppressed feature."""
    return feature_edit.activate_feature(feature_name)


# ===========================================================================
# SELECTION TOOLS
# ===========================================================================
@mcp.tool()
def clear_selection() -> dict[str, Any]:
    """Clear the current selection."""
    return selection.clear_selection()


@mcp.tool()
def get_selection_count() -> dict[str, Any]:
    """Return the number of items in the current selection."""
    return selection.get_selection_count()


@mcp.tool()
def select_element_by_name(element_name: str, append: bool = False) -> dict[str, Any]:
    """Select a geometric element by its name."""
    return selection.select_element_by_name(element_name, append)


@mcp.tool()
def select_face_by_index(
    feature_name: str,
    face_index: int = 1,
    append: bool = False,
) -> dict[str, Any]:
    """Select a face from a feature by index."""
    return selection.select_face_by_index(feature_name, face_index, append)


@mcp.tool()
def select_edge_by_index(
    feature_name: str,
    edge_index: int = 1,
    append: bool = False,
) -> dict[str, Any]:
    """Select an edge from a feature by index."""
    return selection.select_edge_by_index(feature_name, edge_index, append)


# ===========================================================================
# ASSEMBLY CONSTRAINT TOOLS
# ===========================================================================
@mcp.tool()
def add_assembly_fix_constraint(component_name: str) -> dict[str, Any]:
    """Fix a component in space within the active product."""
    return assembly_constraints.add_assembly_fix_constraint(component_name)


@mcp.tool()
def add_assembly_offset_constraint(
    component1: str,
    component2: str,
    offset: float = 0.0,
) -> dict[str, Any]:
    """Add an offset constraint between two components."""
    return assembly_constraints.add_assembly_offset_constraint(component1, component2, offset)


@mcp.tool()
def add_assembly_angle_constraint(
    component1: str,
    component2: str,
    angle: float = 90.0,
) -> dict[str, Any]:
    """Add an angle constraint between two components."""
    return assembly_constraints.add_assembly_angle_constraint(component1, component2, angle)


@mcp.tool()
def add_assembly_coincidence_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a coincidence constraint between two components."""
    return assembly_constraints.add_assembly_coincidence_constraint(component1, component2)


@mcp.tool()
def add_assembly_parallelism_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a parallelism constraint between two components."""
    return assembly_constraints.add_assembly_parallelism_constraint(component1, component2)


@mcp.tool()
def add_assembly_perpendicularity_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a perpendicularity constraint between two components."""
    return assembly_constraints.add_assembly_perpendicularity_constraint(component1, component2)


@mcp.tool()
def add_contact_constraint(
    component1: str,
    component2: str,
) -> dict[str, Any]:
    """Add a surface contact constraint between two components."""
    return assembly_constraints.add_assembly_contact_constraint(component1, component2)


@mcp.tool()
def list_assembly_constraints() -> list[dict[str, Any]]:
    """List all assembly constraints in the active product."""
    return assembly_constraints.list_assembly_constraints()


@mcp.tool()
def delete_constraint(constraint_name: str) -> dict[str, Any]:
    """Delete an assembly constraint by name."""
    return assembly_constraints.delete_assembly_constraint(constraint_name)


@mcp.tool()
def update_constraints() -> dict[str, Any]:
    """Update the assembly constraints."""
    return assembly_constraints.update_assembly_constraints()


# ===========================================================================
# ADVANCED PART DESIGN TOOLS
# ===========================================================================
@mcp.tool()
def create_boolean_add(source_body_name: str, target_body_name: str | None = None) -> dict[str, Any]:
    """Boolean add: insert one body into another."""
    return part_design_advanced.create_boolean_add(source_body_name, target_body_name)


@mcp.tool()
def create_boolean_remove(source_body_name: str, target_body_name: str | None = None) -> dict[str, Any]:
    """Boolean remove: subtract one body from another."""
    return part_design_advanced.create_boolean_remove(source_body_name, target_body_name)


@mcp.tool()
def create_boolean_intersect(source_body_name: str, target_body_name: str | None = None) -> dict[str, Any]:
    """Boolean intersect: intersect one body with another."""
    return part_design_advanced.create_boolean_intersect(source_body_name, target_body_name)


@mcp.tool()
def create_shell(
    feature_name: str,
    face_index: int = 1,
    internal_thickness: float = 1.0,
    external_thickness: float = 0.0,
) -> dict[str, Any]:
    """Create a Shell (hollow) feature."""
    return part_design_advanced.create_shell(feature_name, face_index, internal_thickness, external_thickness)


@mcp.tool()
def create_draft(
    feature_name: str,
    face_index: int = 1,
    angle: float = 5.0,
    direction: list[float] | None = None,
) -> dict[str, Any]:
    """Create a Draft feature."""
    return part_design_advanced.create_draft(feature_name, face_index, angle, direction)


@mcp.tool()
def create_thickness(
    feature_name: str,
    face_index: int = 1,
    offset: float = 1.0,
) -> dict[str, Any]:
    """Create a Thickness feature on a face."""
    return part_design_advanced.create_thickness(feature_name, face_index, offset)


@mcp.tool()
def create_close_surface(surface_name: str) -> dict[str, Any]:
    """Close an open surface to create a solid."""
    return part_design_advanced.create_close_surface(surface_name)


@mcp.tool()
def create_sew_surface(surface_name: str, sewing_side: int = 1) -> dict[str, Any]:
    """Sew a surface onto a solid body."""
    return part_design_advanced.create_sew_surface(surface_name, sewing_side)


@mcp.tool()
def create_split(splitting_element_name: str, split_side: int = 1) -> dict[str, Any]:
    """Split a body with a surface or plane."""
    return part_design_advanced.create_split(splitting_element_name, split_side)


@mcp.tool()
def create_thick_surface(
    surface_name: str,
    top_offset: float = 1.0,
    bottom_offset: float = 1.0,
    offset_direction: int = 1,
) -> dict[str, Any]:
    """Thicken a surface into a solid."""
    return part_design_advanced.create_thick_surface(surface_name, top_offset, bottom_offset, offset_direction)


@mcp.tool()
def create_remove_face(
    feature_name: str,
    face_index: int = 1,
) -> dict[str, Any]:
    """Remove a face from a solid body."""
    return part_design_advanced.create_remove_face(feature_name, face_index)


@mcp.tool()
def create_replace_face(
    feature_name: str,
    surface_name: str,
    face_index: int = 1,
) -> dict[str, Any]:
    """Replace a face with a surface."""
    return part_design_advanced.create_replace_face(feature_name, surface_name, face_index)


# ===========================================================================
# PART DESIGN SWEEP / TRANSFORMATION TOOLS
# ===========================================================================
@mcp.tool()
def create_groove(sketch_name: str | None = None) -> dict[str, Any]:
    """Create a Groove (swept cut) from a profile sketch."""
    return part_design_sweep.create_groove(sketch_name)


@mcp.tool()
def create_scaling(
    feature_name: str,
    factor: float = 1.0,
) -> dict[str, Any]:
    """Create a Scaling transformation on a feature."""
    return part_design_sweep.create_scaling(feature_name, factor)


@mcp.tool()
def create_symmetry(
    feature_name: str,
    plane_name: str = "yz",
) -> dict[str, Any]:
    """Create a Symmetry transformation of a feature."""
    return part_design_sweep.create_symmetry(feature_name, plane_name)


@mcp.tool()
def create_affinity(
    x_ratio: float = 1.0,
    y_ratio: float = 1.0,
    z_ratio: float = 1.0,
) -> dict[str, Any]:
    """Create an Affinity transformation."""
    return part_design_sweep.create_affinity(x_ratio, y_ratio, z_ratio)


@mcp.tool()
def create_blend() -> dict[str, Any]:
    """Create a Blend feature (requires further profile setup in CATIA)."""
    return part_design_sweep.create_blend()


@mcp.tool()
def create_axis_to_axis(
    source_feature_name: str,
    target_feature_name: str,
) -> dict[str, Any]:
    """Create an Axis To Axis transformation."""
    return part_design_sweep.create_axis_to_axis(source_feature_name, target_feature_name)


@mcp.tool()
def create_circ_pattern(
    feature_name: str,
    instances: int = 3,
    angular_spacing: float = 120.0,
    total_angle: float = 360.0,
) -> dict[str, Any]:
    """Create a circular pattern of a feature."""
    return part_design_sweep.create_circ_pattern(feature_name, instances, angular_spacing, total_angle)


@mcp.tool()
def create_loft(
    section1_name: str,
    section2_name: str,
    section3_name: str | None = None,
    name: str = "Loft",
) -> dict[str, Any]:
    """Create a Loft (multi-sections solid) between sketches."""
    return part_design_sweep.create_loft(section1_name, section2_name, section3_name, name)


@mcp.tool()
def create_helix(
    sketch_name: str,
    axis_name: str = "plane_xy",
    pitch: float = 10.0,
    height: float = 50.0,
    starting_angle: float = 0.0,
    name: str = "Helix",
) -> dict[str, Any]:
    """Create a Helix sweep from a profile sketch."""
    return part_design_sweep.create_helix(sketch_name, axis_name, pitch, height, starting_angle, name)


# ===========================================================================
# GSD SURFACE TOOLS
# ===========================================================================
@mcp.tool()
def create_gsd_point(x: float, y: float, z: float, name: str = "Point") -> dict[str, Any]:
    """Create a 3D point in GSD."""
    return gsd.create_gsd_point(x, y, z, name)


@mcp.tool()
def create_gsd_line(
    point1_name: str,
    point2_name: str,
    name: str = "Line",
) -> dict[str, Any]:
    """Create a line through two points in GSD."""
    return gsd.create_gsd_line(point1_name, point2_name, name)


@mcp.tool()
def create_gsd_plane(
    reference_plane_name: str,
    offset: float = 0.0,
    name: str = "Plane",
) -> dict[str, Any]:
    """Create an offset plane in GSD."""
    return gsd.create_gsd_plane(reference_plane_name, offset, name)


@mcp.tool()
def create_gsd_extrude(
    profile_name: str,
    length1: float = 10.0,
    length2: float = 0.0,
    direction: list[float] | None = None,
    name: str = "Extrude",
) -> dict[str, Any]:
    """Extrude a profile in GSD."""
    return gsd.create_gsd_extrude(profile_name, length1, length2, direction, name)


@mcp.tool()
def create_gsd_revol(
    profile_name: str,
    axis_name: str = "plane_xy",
    angle1: float = 0.0,
    angle2: float = 360.0,
    name: str = "Revol",
) -> dict[str, Any]:
    """Revolve a profile around an axis in GSD."""
    return gsd.create_gsd_revol(profile_name, axis_name, angle1, angle2, name)


@mcp.tool()
def create_gsd_offset(
    surface_name: str,
    offset: float = 1.0,
    name: str = "Offset",
) -> dict[str, Any]:
    """Offset a surface in GSD."""
    return gsd.create_gsd_offset(surface_name, offset, name)


@mcp.tool()
def create_gsd_project(
    element_name: str,
    support_name: str,
    name: str = "Project",
) -> dict[str, Any]:
    """Project an element onto a support surface in GSD."""
    return gsd.create_gsd_project(element_name, support_name, name)


@mcp.tool()
def create_gsd_intersect(
    element1_name: str,
    element2_name: str,
    name: str = "Intersect",
) -> dict[str, Any]:
    """Intersect two elements in GSD."""
    return gsd.create_gsd_intersect(element1_name, element2_name, name)


@mcp.tool()
def create_gsd_extract(
    element_name: str,
    name: str = "Extract",
) -> dict[str, Any]:
    """Extract a sub-element in GSD."""
    return gsd.create_gsd_extract(element_name, name)


@mcp.tool()
def create_gsd_fill(
    boundary_name: str,
    name: str = "Fill",
) -> dict[str, Any]:
    """Create a fill surface from a closed boundary in GSD."""
    return gsd.create_gsd_fill(boundary_name, name)


@mcp.tool()
def create_gsd_sweep(
    guide_name: str,
    profile_name: str | None = None,
    sweep_type: str = "line",
    name: str = "Sweep",
) -> dict[str, Any]:
    """Create a sweep surface in GSD."""
    return gsd.create_gsd_sweep(guide_name, profile_name, sweep_type, name)


@mcp.tool()
def create_gsd_split(
    element_name: str,
    splitting_name: str,
    name: str = "Split",
) -> dict[str, Any]:
    """Split an element by another in GSD."""
    return gsd.create_gsd_split(element_name, splitting_name, name)


@mcp.tool()
def create_gsd_join(
    element1_name: str,
    element2_name: str,
    name: str = "Join",
) -> dict[str, Any]:
    """Join two elements in GSD."""
    return gsd.create_gsd_join(element1_name, element2_name, name)


@mcp.tool()
def create_gsd_trim(
    element1_name: str,
    element2_name: str,
    keep_side: int = 1,
    name: str = "Trim",
) -> dict[str, Any]:
    """Trim two elements in GSD."""
    return gsd.create_gsd_trim(element1_name, element2_name, keep_side, name)


@mcp.tool()
def create_gsd_blend(
    curve1_name: str,
    curve2_name: str,
    continuity: str = "tangent",
    name: str = "Blend",
) -> dict[str, Any]:
    """Create a blend surface between two curves in GSD."""
    return gsd.create_gsd_blend(curve1_name, curve2_name, continuity, name)


@mcp.tool()
def create_gsd_boundary(
    surface_name: str,
    name: str = "Boundary",
) -> dict[str, Any]:
    """Extract the boundary of a surface in GSD."""
    return gsd.create_gsd_boundary(surface_name, name)


# ===========================================================================
# SHEET METAL TOOLS
# ===========================================================================
@mcp.tool()
def create_wall(
    sketch_name: str,
    thickness: float = 1.0,
    reverse: bool = False,
) -> dict[str, Any]:
    """Create a Sheet-Metal wall from a sketch profile."""
    return sheet_metal.create_wall(sketch_name, thickness, reverse)


@mcp.tool()
def create_bend(
    wall1_name: str,
    wall2_name: str,
    radius: float = 1.0,
    angle: float = 90.0,
) -> dict[str, Any]:
    """Create a bend between two sheet-metal walls."""
    return sheet_metal.create_bend(wall1_name, wall2_name, radius, angle)


@mcp.tool()
def create_flat_pattern() -> dict[str, Any]:
    """Create a flat pattern of the current sheet-metal part."""
    return sheet_metal.create_flat_pattern()


@mcp.tool()
def create_cutout(
    sketch_name: str,
    depth: float = 10.0,
) -> dict[str, Any]:
    """Create a sheet-metal cutout (Pocket through wall)."""
    return sheet_metal.create_cutout(sketch_name, depth)


@mcp.tool()
def create_flange(
    wall_name: str,
    length: float = 10.0,
    angle: float = 90.0,
    radius: float = 1.0,
) -> dict[str, Any]:
    """Create a flange on a wall edge."""
    return sheet_metal.create_flange(wall_name, length, angle, radius)


@mcp.tool()
def create_hem(
    wall_name: str,
    length: float = 5.0,
    radius: float = 1.0,
) -> dict[str, Any]:
    """Create a hem on a wall edge."""
    return sheet_metal.create_hem(wall_name, length, radius)


@mcp.tool()
def create_joggle(
    wall_name: str,
    depth: float = 2.0,
    radius: float = 1.0,
) -> dict[str, Any]:
    """Create a joggle on a wall."""
    return sheet_metal.create_joggle(wall_name, depth, radius)


@mcp.tool()
def create_corner_relief(
    wall1_name: str,
    wall2_name: str,
    relief_type: str = "circular",
    size: float = 5.0,
) -> dict[str, Any]:
    """Create a corner relief between two walls."""
    return sheet_metal.create_corner_relief(wall1_name, wall2_name, relief_type, size)


# ===========================================================================
# AXIS SYSTEM TOOLS (robotics / kinematics)
# ===========================================================================
@mcp.tool()
def create_axis_system(
    name: str = "AxisSystem",
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    origin_z: float = 0.0,
    x_axis: list[float] | None = None,
    y_axis: list[float] | None = None,
    z_axis: list[float] | None = None,
) -> dict[str, Any]:
    """Create a new coordinate frame (axis system) in the active Part."""
    return axis_systems.create_axis_system(name, origin_x, origin_y, origin_z, x_axis, y_axis, z_axis)


@mcp.tool()
def list_axis_systems() -> list[dict[str, Any]]:
    """List all axis systems in the active Part."""
    return axis_systems.list_axis_systems()


@mcp.tool()
def set_axis_system_origin(
    name: str,
    x: float,
    y: float,
    z: float,
) -> dict[str, Any]:
    """Move an existing axis system to a new origin."""
    return axis_systems.set_axis_system_origin(name, x, y, z)


# ===========================================================================
# MATERIAL TOOLS
# ===========================================================================
@mcp.tool()
def apply_material(material_name: str, body_name: str | None = None) -> dict[str, Any]:
    """Apply a material to a body."""
    return materials.apply_material(material_name, body_name)


@mcp.tool()
def remove_material(body_name: str | None = None) -> dict[str, Any]:
    """Remove material from a body."""
    return materials.remove_material(body_name)


@mcp.tool()
def list_materials() -> list[dict[str, Any]]:
    """List available materials."""
    return materials.list_materials()


@mcp.tool()
def get_material_properties(body_name: str | None = None) -> dict[str, Any]:
    """Get material properties of a body."""
    return materials.get_material_properties(body_name)


# ===========================================================================
# FEATURE TREE TOOLS
# ===========================================================================
@mcp.tool()
def get_full_feature_tree() -> list[dict[str, Any]]:
    """Return the complete feature tree of the active part."""
    return feature_tree.get_full_feature_tree()


@mcp.tool()
def get_body_contents(body_name: str | None = None) -> dict[str, Any]:
    """Return the contents of a specific body."""
    return feature_tree.get_body_contents(body_name)


@mcp.tool()
def rename_feature(old_name: str, new_name: str) -> dict[str, Any]:
    """Rename a feature in the active part."""
    return feature_tree.rename_feature(old_name, new_name)


@mcp.tool()
def copy_paste_feature(
    feature_name: str,
    target_body_name: str | None = None,
) -> dict[str, Any]:
    """Copy and paste a feature into a target body."""
    return feature_tree.copy_paste_feature(feature_name, target_body_name)


# ===========================================================================
# VIEW CONTROL TOOLS
# ===========================================================================
@mcp.tool()
def set_view_mode(mode: str = "shading") -> dict[str, Any]:
    """Set the view display mode."""
    return view_control.set_view_mode(mode)


@mcp.tool()
def hide_show(element_name: str, hide: bool = True) -> dict[str, Any]:
    """Hide or show a geometric element."""
    return view_control.hide_show(element_name, hide)


@mcp.tool()
def isolate(element_name: str) -> dict[str, Any]:
    """Isolate a single element (hide all others)."""
    return view_control.isolate(element_name)


@mcp.tool()
def activate_view(view_name: str = "Front") -> dict[str, Any]:
    """Activate a standard view (Front, Back, Top, etc.)."""
    return view_control.activate_view(view_name)


# ===========================================================================
# SKETCHER ADVANCED TOOLS
# ===========================================================================
@mcp.tool()
def add_spline(points: list[list[float]], sketch_name: str | None = None) -> dict[str, Any]:
    """Add a 2D spline (open) to the active or named sketch.

    Args:
        points: List of [x, y] control points.
        sketch_name: Optional target sketch name.
    """
    return sketcher_advanced.add_spline(points, sketch_name)


@mcp.tool()
def add_ellipse(
    center_x: float,
    center_y: float,
    major_radius: float,
    minor_radius: float,
    angle: float = 0.0,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a closed ellipse to the active or named sketch.

    Args:
        center_x, center_y: Ellipse center.
        major_radius: Major axis radius.
        minor_radius: Minor axis radius.
        angle: Rotation angle of major axis in degrees.
        sketch_name: Optional target sketch name.
    """
    return sketcher_advanced.add_ellipse(center_x, center_y, major_radius, minor_radius, angle, sketch_name)


@mcp.tool()
def add_construction_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Add a construction line (axis) to the active or named sketch.

    Args:
        x1, y1: Start point.
        x2, y2: End point.
        sketch_name: Optional target sketch name.
    """
    return sketcher_advanced.add_construction_line(x1, y1, x2, y2, sketch_name)


@mcp.tool()
def project_3d_to_sketch(
    element_names: list[str],
    sketch_name: str | None = None,
) -> dict[str, Any]:
    """Project 3D element(s) onto the active or named sketch.

    Args:
        element_names: List of 3D element names to project.
        sketch_name: Optional target sketch name.
    """
    return sketcher_advanced.project_3d_to_sketch(element_names, sketch_name)


# ===========================================================================
# PART DESIGN MORE TOOLS
# ===========================================================================
@mcp.tool()
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
    return part_design_more.create_stiffener(sketch_name, thickness, reverse)


@mcp.tool()
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
    return part_design_more.create_face_fillet(feature_name, radius, face1_index, face2_index)


@mcp.tool()
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
    return part_design_more.create_tritangent_fillet(feature_name, remove_face_index, face1_index, face2_index)


# ===========================================================================
# GSD ADVANCED TOOLS
# ===========================================================================
@mcp.tool()
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
    return gsd_advanced.create_gsd_multisections_surface(section_names, guide_names, spine_name, name)


@mcp.tool()
def create_gsd_extrapolate(
    surface_name: str,
    length: float = 10.0,
    continuity: str = "tangent",
    name: str = "Extrapolate",
) -> dict[str, Any]:
    """Extrapolate a surface or curve by length in GSD.

    Args:
        surface_name: Surface/curve to extrapolate.
        length: Extrapolation length in mm.
        continuity: "point", "tangent", or "curvature".
        name: Feature name.
    """
    return gsd_advanced.create_gsd_extrapolate(surface_name, length, continuity, name)


@mcp.tool()
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
    return gsd_advanced.create_gsd_parallel_curve(curve_name, support_name, offset, invert_direction, geodesic, name)


@mcp.tool()
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

    Args:
        center_point_name: Starting point name.
        axis_name: Axis line/plane name.
        pitch: Helix pitch in mm.
        height: Total height in mm.
        radius: Helix radius in mm.
        starting_angle: Start angle in degrees.
        clockwise: Clockwise revolution.
        name: Feature name.
    """
    return gsd_advanced.create_gsd_helix(center_point_name, axis_name, pitch, height, radius, starting_angle, clockwise, name)


@mcp.tool()
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
    return gsd_advanced.create_gsd_spine(section_names, guide_names, name)


# ===========================================================================
# DRAFTING ADVANCED TOOLS
# ===========================================================================
@mcp.tool()
def create_section_view(
    parent_view_name: str,
    x: float,
    y: float,
    section_x1: float,
    section_y1: float,
    section_x2: float,
    section_y2: float,
    scale: float = 1.0,
    name: str = "SectionView",
    section_type: str = "Arrow",
    side_to_draw: int = 1,
) -> dict[str, Any]:
    """Create a section view from a parent view."""
    return drafting_advanced.create_section_view(
        parent_view_name, x, y, section_x1, section_y1, section_x2, section_y2, scale, name, section_type, side_to_draw
    )


@mcp.tool()
def create_detail_view(
    parent_view_name: str,
    x: float,
    y: float,
    center_x: float,
    center_y: float,
    radius: float = 10.0,
    scale: float = 2.0,
    name: str = "DetailView",
) -> dict[str, Any]:
    """Create a circular detail view from a parent view."""
    return drafting_advanced.create_detail_view(parent_view_name, x, y, center_x, center_y, radius, scale, name)


@mcp.tool()
def create_isometric_view(
    parent_view_name: str,
    x: float,
    y: float,
    scale: float = 1.0,
    name: str = "IsometricView",
) -> dict[str, Any]:
    """Create an isometric view from a parent view."""
    return drafting_advanced.create_isometric_view(parent_view_name, x, y, scale, name)


@mcp.tool()
def create_broken_view(
    view_name: str,
    break_x1: float,
    break_y1: float,
    break_x2: float,
    break_y2: float,
    gap: float = 5.0,
    orientation: str = "horizontal",
) -> dict[str, Any]:
    """Create a broken view on an existing view."""
    return drafting_advanced.create_broken_view(view_name, break_x1, break_y1, break_x2, break_y2, gap, orientation)


@mcp.tool()
def generate_dimensions() -> dict[str, Any]:
    """Generate dimensions automatically on the active drawing sheet."""
    return drafting_advanced.generate_dimensions()


@mcp.tool()
def add_bom_table(
    x: float,
    y: float,
    rows: int = 10,
    columns: int = 4,
    row_height: float = 5.0,
    column_width: float = 30.0,
    headers: list[str] | None = None,
) -> dict[str, Any]:
    """Add a BOM-like table to the active drawing sheet."""
    return drafting_advanced.add_bom_table(x, y, rows, columns, row_height, column_width, headers)


@mcp.tool()
def add_gdt(
    view_name: str,
    leader_x: float,
    leader_y: float,
    text_x: float,
    text_y: float,
    symbol: int = 0,
    text: str = "A",
) -> dict[str, Any]:
    """Add a GD&T (geometric tolerance) symbol to a drawing view."""
    return drafting_advanced.add_gdt(view_name, leader_x, leader_y, text_x, text_y, symbol, text)


@mcp.tool()
def add_roughness(
    view_name: str,
    x: float,
    y: float,
    value: str = "Ra 1.6",
) -> dict[str, Any]:
    """Add a surface roughness annotation (approximated as text) to a drawing view."""
    return drafting_advanced.add_roughness(view_name, x, y, value)


# ===========================================================================
# GENERAL TOOLS
# ===========================================================================
@mcp.tool()
def search_elements(
    query: str,
    search_type: str = "name",
) -> list[dict[str, Any]]:
    """Search for elements in the active document using CATIA selection search."""
    return general_tools.search_elements(query, search_type)


@mcp.tool()
def set_graphic_properties(
    element_name: str,
    color: list[int] | None = None,
    line_type: int | None = None,
    width: int | None = None,
    show: bool | None = None,
    opacity: int | None = None,
) -> dict[str, Any]:
    """Set graphic properties (color, line type, width, show, opacity) of an element."""
    return general_tools.set_graphic_properties(element_name, color, line_type, width, show, opacity)


@mcp.tool()
def set_layer(element_name: str, layer: int) -> dict[str, Any]:
    """Set the layer of an element."""
    return general_tools.set_layer(element_name, layer)


@mcp.tool()
def undo() -> dict[str, Any]:
    """Undo the last operation (best effort)."""
    return general_tools.undo()


@mcp.tool()
def redo() -> dict[str, Any]:
    """Redo the last undone operation (best effort)."""
    return general_tools.redo()


@mcp.tool()
def begin_undo_transaction() -> dict[str, Any]:
    """Begin a new undo-redo transaction group."""
    return general_tools.begin_undo_transaction()


@mcp.tool()
def end_undo_transaction() -> dict[str, Any]:
    """End the current undo-redo transaction group."""
    return general_tools.end_undo_transaction()


# ===========================================================================
# ASSEMBLY ANALYSIS TOOLS
# ===========================================================================
@mcp.tool()
def list_bom() -> list[dict[str, Any]]:
    """List Bill of Materials for the active product."""
    return assembly_analysis.list_bom()


@mcp.tool()
def measure_clearance(element1: str, element2: str) -> dict[str, Any]:
    """Measure minimum clearance/distance between two product instances."""
    return assembly_analysis.measure_clearance(element1, element2)
