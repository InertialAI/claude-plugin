"""MCP tool registry.

Add a new tool by:
  1. Creating `server/tools/<your_tool>.py` with a `Tool` subclass.
  2. Importing the class here and appending it to `ALL_TOOLS`.
"""

from __future__ import annotations

from ._base import Tool
from .check_setup import CheckSetupTool
from .classify import ClassifyTool
from .compare import CompareTool
from .create_embedding import CreateEmbeddingTool
from .delete_embedding import DeleteEmbeddingTool
from .find_similar import FindSimilarTool
from .list_embeddings import ListEmbeddingsTool
from .list_models import ListModelsTool

ALL_TOOLS: list[type[Tool]] = [
    CreateEmbeddingTool,
    ListModelsTool,
    CompareTool,
    FindSimilarTool,
    ClassifyTool,
    ListEmbeddingsTool,
    DeleteEmbeddingTool,
    CheckSetupTool,
]

__all__ = ["Tool", "ALL_TOOLS"]
