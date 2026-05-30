# CATIA MCP Server

Model Context Protocol (MCP) server for Dassault Systèmes **CATIA V5** (and V6 via compatible COM interfaces) automation on Windows.

It exposes almost every common CATIA operation—document management, 2D sketcher, 3D Part Design, Assembly, Drafting, Parameters & Formulas, Measurement/Analysis, and Export/View control—as strongly-typed MCP tools. Any MCP-compatible client (Claude Code, Claude Desktop, Continue, etc.) can drive CATIA without writing custom glue code.

## Architecture

```
Claude / MCP Client
       │  stdio / SSE (MCP JSON-RPC)
       ▼
catia_mcp/server.py  (FastMCP)
       │
       ▼
catia_mcp/tools/*.py  (business logic)
       │
       ▼
win32com.client  →  CATIA.Application (COM)
```

## Prerequisites

- **Windows** with CATIA V5 (or V6) installed and registered as a COM server.
- **Python 3.11+**
- `pywin32` (bundled in requirements)

> **Tip:** If CATIA does not appear as a COM server, run `cnext.exe /regserver` from the CATIA `bin` directory as Administrator.

## Installation

```bash
# Clone or copy this folder
cd catia-mcp

# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Usage

### 1. stdio (default — for Claude Code / Claude Desktop)

```bash
python -m catia_mcp
```

Add to Claude Code:

```bash
claude mcp add catia -- python -m catia_mcp
```

Or in Claude Desktop `settings.json`:

```json
{
  "mcpServers": {
    "catia": {
      "command": "python",
      "args": ["-m", "catia_mcp"]
    }
  }
}
```

### 2. Streamable HTTP (for remote / web clients)

```bash
python -m catia_mcp streamable-http
```

Then connect to `http://localhost:8000/mcp`.

## Available Tools (Summary)

| Category | Tools |
|----------|-------|
| **Meta / Connection** | `catia_status`, `ensure_catia_visible` |
| **Document** | `list_documents`, `get_active_document_info`, `open_document`, `new_document`, `save_document`, `save_as_document`, `close_document`, `close_all_documents`, `get_document_type` |
| **Sketcher** | `create_sketch_on_plane`, `add_point`, `add_line`, `add_circle`, `add_rectangle`, `add_arc`, `close_sketch`, `get_sketch_elements` |
| **Part Design** | `create_pad`, `create_pocket`, `create_shaft`, `create_hole`, `create_fillet`, `create_chamfer`, `create_mirror`, `create_pattern`, `create_rib`, `create_slot`, `add_body`, `insert_in_body` |
| **Assembly** | `create_product`, `add_component`, `add_existing_component`, `update_product`, `get_product_tree`, `apply_constraint`, `move_component`, `explode_product`, `activate_product` |
| **Measurement** | `measure_distance`, `measure_length`, `measure_area`, `measure_volume`, `measure_inertia`, `get_bounding_box` |
| **Parameters** | `list_parameters`, `get_parameter_value`, `set_parameter_value`, `add_parameter`, `add_formula`, `update` |
| **Drafting** | `create_drawing`, `create_sheet`, `create_view`, `add_dimension`, `add_annotation`, `update_sheet_links` |
| **Export / View** | `export_to_stl`, `export_to_step`, `export_to_iges`, `export_to_pdf`, `capture_screenshot`, `fit_all_in`, `update_view` |

## Example Prompts

> *These are example natural-language requests you can send to Claude once the MCP server is connected.*

1. **Open a part and create a simple bracket**
   > "Create a new Part, sketch a 50×30 rectangle on the XY plane, extrude it to 10 mm, then add a 5 mm hole through the center."

2. **Drive parameters**
   > "Set parameter `Length_1` to 120 mm and update the model."

3. **Assembly operation**
   > "Create a new Product, add an existing component from `C:\\Parts\\Base.CATPart`, then add a new component and move it 50 mm along X."

4. **Export**
   > "Export the active document to `C:\\Export\\model.stp` as STEP AP214."

5. **Measurement**
   > "Measure the volume and bounding box of the active PartBody."

## Development

```bash
# Lint
ruff check catia_mcp

# Run with MCP Inspector (requires Node)
npx -y @modelcontextprotocol/inspector
# Then connect to http://localhost:8000/mcp if using HTTP transport
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `CATIA.Application` not found | Make sure CATIA is installed. Run `cnext.exe /regserver` in the CATIA `bin` folder as Admin. |
| `No active document` | CATIA must have a document open, or use `new_document` / `open_document` first. |
| `Active document is not a Part document` | Some tools only work on `.CATPart`; switch to a Part document or create one with `new_document("Part")`. |
| Sketch or feature fails | Ensure the sketch is on a valid support plane and profile is closed where required. |

## License

MIT
