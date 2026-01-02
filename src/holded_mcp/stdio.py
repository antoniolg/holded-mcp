from __future__ import annotations

from holded_mcp.mcp_server import mcp


def main() -> None:
    mcp.run(transport="stdio")

