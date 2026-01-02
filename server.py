from __future__ import annotations

from holded_mcp.mcp_server import mcp


if __name__ == "__main__":
    mcp.run(transport="stdio")

