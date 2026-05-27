from __future__ import annotations

from typing import Any

from store import db

from ._base import Tool


class ListEmbeddingsTool(Tool):
    name = "list_embeddings"

    def run(self, label: str | None = None, limit: int = 100) -> dict[str, Any]:
        """List stored embeddings (handles, labels, descriptions).

        Optionally filter by `label`. Use this to inspect the local corpus.
        """
        conn = db()
        if label is None:
            cursor = conn.execute(
                "SELECT handle, model, dim, label, text, created_at FROM embeddings "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            cursor = conn.execute(
                "SELECT handle, model, dim, label, text, created_at FROM embeddings "
                "WHERE label = ? ORDER BY created_at DESC LIMIT ?",
                (label, limit),
            )
        items = [
            {"handle": h, "model": m, "dim": d, "label": lbl, "text": t, "created_at": c}
            for (h, m, d, lbl, t, c) in cursor
        ]
        conn.close()
        return {"count": len(items), "embeddings": items}
