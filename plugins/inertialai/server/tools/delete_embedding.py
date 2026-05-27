from __future__ import annotations

from typing import Any

from store import db

from ._base import Tool


class DeleteEmbeddingTool(Tool):
    name = "delete_embedding"

    def run(self, handle: str) -> dict[str, Any]:
        """Delete a stored embedding by handle."""
        conn = db()
        cur = conn.execute("DELETE FROM embeddings WHERE handle = ?", (handle,))
        conn.commit()
        deleted = cur.rowcount
        conn.close()
        return {"deleted": deleted}
