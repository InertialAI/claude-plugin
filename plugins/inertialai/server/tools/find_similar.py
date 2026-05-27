from __future__ import annotations

from typing import Any

from store import cosine, db, unpack

from ._base import Tool


class FindSimilarTool(Tool):
    name = "find_similar"

    def run(
        self,
        query_handle: str,
        corpus_handles: list[str] | None = None,
        k: int = 5,
    ) -> dict[str, Any]:
        """Top-k most similar embeddings to a query.

        If `corpus_handles` is omitted, searches every stored embedding except
        the query itself.
        """
        conn = db()
        qrow = conn.execute(
            "SELECT vector, dim FROM embeddings WHERE handle = ?", (query_handle,)
        ).fetchone()
        if qrow is None:
            conn.close()
            return {"error": f"Unknown handle: {query_handle}"}
        q = unpack(qrow[0], qrow[1])

        if corpus_handles is None:
            cursor = conn.execute(
                "SELECT handle, vector, dim, label, text FROM embeddings WHERE handle != ?",
                (query_handle,),
            )
        else:
            placeholders = ",".join("?" * len(corpus_handles))
            cursor = conn.execute(
                f"SELECT handle, vector, dim, label, text FROM embeddings "
                f"WHERE handle IN ({placeholders})",
                corpus_handles,
            )

        scored = [
            {
                "handle": h,
                "similarity": cosine(q, unpack(v, d)),
                "label": label,
                "text": text,
            }
            for (h, v, d, label, text) in cursor
        ]
        conn.close()
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return {"matches": scored[:k]}
