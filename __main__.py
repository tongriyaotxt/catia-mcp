"""Entry point for `python -m catia_mcp`."""

from __future__ import annotations

import sys

from catia_mcp.server import mcp


def main() -> None:
    """Run the CATIA MCP server."""
    # Default to stdio transport for MCP compatibility
    transport = "stdio"
    if len(sys.argv) > 1:
        transport = sys.argv[1]
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
