# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "mcp>=1.2.0",
#   "httpx>=0.27",
#   "keyring>=24.0.0",
# ]
# ///
"""MCP server wrapping the InertialAI embeddings API.

Tools live one-per-file under `tools/` and subclass `tools.Tool`. This
module is just the entry point: build a FastMCP instance, register every
tool listed in `tools.ALL_TOOLS`, and run.

To add a new tool, create `tools/<your_tool>.py` and append the class to
`ALL_TOOLS` in `tools/__init__.py` — no edits to this file required.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tools import ALL_TOOLS

mcp = FastMCP("inertialai")

for tool_cls in ALL_TOOLS:
    tool_cls().register(mcp)


if __name__ == "__main__":
    mcp.run()
