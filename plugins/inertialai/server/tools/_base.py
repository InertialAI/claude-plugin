"""Base class for InertialAI MCP tools.

Each tool lives in its own file under `server/tools/` and subclasses `Tool`.
A subclass sets `name` (the MCP-visible tool name) and implements `run`
(sync or async) with typed parameters and a docstring — FastMCP derives
the JSON schema and description from `run`'s signature and docstring.

To add a new tool:
  1. Create `server/tools/<your_tool>.py` defining `class YourTool(Tool)`.
  2. Add the class to `ALL_TOOLS` in `server/tools/__init__.py`.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


class Tool:
    name: str

    def register(self, mcp: FastMCP) -> None:
        mcp.tool(name=self.name)(self.run)

    def run(self, *args, **kwargs):  # pragma: no cover - subclass override
        raise NotImplementedError
