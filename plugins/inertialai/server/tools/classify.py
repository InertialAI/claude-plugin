from __future__ import annotations

from typing import Any

from store import cosine, db, unpack

from ._base import Tool


class ClassifyTool(Tool):
    name = "classify"

    def run(
        self,
        query_handle: str,
        corpus_handles: list[str] | None = None,
    ) -> dict[str, Any]:
        """Nearest-neighbor classify against the labeled corpus.

        Returns the label of the most similar labeled embedding plus a few
        runners-up so the caller can judge confidence by the gap to second
        place.

        If `corpus_handles` is omitted, searches all stored embeddings that
        have a non-null label.
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
                "SELECT handle, vector, dim, label FROM embeddings "
                "WHERE handle != ? AND label IS NOT NULL",
                (query_handle,),
            )
        else:
            placeholders = ",".join("?" * len(corpus_handles))
            cursor = conn.execute(
                f"SELECT handle, vector, dim, label FROM embeddings "
                f"WHERE label IS NOT NULL AND handle IN ({placeholders})",
                corpus_handles,
            )

        scored = [
            {"handle": h, "label": label, "similarity": cosine(q, unpack(v, d))}
            for (h, v, d, label) in cursor
        ]
        conn.close()
        if not scored:
            return {
                "error": "No labeled embeddings in corpus. "
                "Pass `label` to create_embedding when building a training set."
            }
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        top = scored[0]
        runners = scored[1:5]
        return {
            "label": top["label"],
            "similarity": top["similarity"],
            "matched_handle": top["handle"],
            "runners_up": runners,
            "confidence_gap": top["similarity"]
            - (runners[0]["similarity"] if runners else 0.0),
        }
