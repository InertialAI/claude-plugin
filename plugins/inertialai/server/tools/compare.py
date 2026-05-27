from __future__ import annotations

from typing import Any

from store import cosine, db, unpack

from ._base import Tool


class CompareTool(Tool):
    name = "compare"

    def run(self, handle_a: str, handle_b: str) -> dict[str, Any]:
        """Cosine similarity between two stored embeddings.

        Returns a single float in [-1, 1]; close to 1 means similar.
        """
        conn = db()
        rows = {
            row[0]: (row[1], row[2])
            for row in conn.execute(
                "SELECT handle, vector, dim FROM embeddings WHERE handle IN (?, ?)",
                (handle_a, handle_b),
            )
        }
        conn.close()
        missing = [h for h in (handle_a, handle_b) if h not in rows]
        if missing:
            return {"error": f"Unknown handle(s): {missing}"}
        a = unpack(*rows[handle_a])
        b = unpack(*rows[handle_b])
        return {"similarity": cosine(a, b)}
