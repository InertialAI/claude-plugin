from __future__ import annotations

import uuid
from typing import Any

import httpx

from auth import API_BASE, missing_key_error, resolve_api_key
from store import db, pack

from ._base import Tool


class CreateEmbeddingTool(Tool):
    name = "create_embedding"

    async def run(
        self,
        time_series: list[list[float]] | None = None,
        text: str | None = None,
        model: str = "inertial-embed-alpha",
        dimensions: int | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        """Embed a time-series (and/or text description) via InertialAI.

        Returns a handle that other tools (compare, find_similar, classify)
        reference. The raw vector is stored locally and NOT returned, to keep
        it out of the model's context.

        Pass `label` when building a labeled corpus for classify().

        Args:
            time_series: List of channel arrays, e.g. [[ax...], [ay...], [az...]].
            text: Optional natural-language description of the signal.
            model: Embedding model id (default: inertial-embed-alpha).
            dimensions: Optional embedding dimensionality.
            label: Optional label to associate with this embedding.
        """
        api_key, _ = resolve_api_key()
        if not api_key:
            return missing_key_error()
        if time_series is None and text is None:
            return {"error": "Provide at least one of `time_series` or `text`"}

        input_obj: dict[str, Any] = {}
        if time_series is not None:
            input_obj["time_series"] = time_series
        if text is not None:
            input_obj["text"] = text

        payload: dict[str, Any] = {"model": model, "input": input_obj}
        if dimensions is not None:
            payload["dimensions"] = dimensions

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{API_BASE}/api/v1/embeddings",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )

        if r.status_code >= 400:
            return {"error": f"API {r.status_code}: {r.text[:500]}"}

        body = r.json()
        items = body.get("data") or []
        if not items:
            return {"error": "API returned no embeddings"}

        handles: list[dict[str, Any]] = []
        conn = db()
        for item in items:
            vec = item.get("embedding") or item.get("vector") or []
            if not vec:
                continue
            handle = uuid.uuid4().hex[:12]
            conn.execute(
                "INSERT INTO embeddings (handle, model, dim, vector, text, label) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (handle, body.get("model", model), len(vec), pack(vec), text, label),
            )
            handles.append({"handle": handle, "dim": len(vec)})
        conn.commit()
        conn.close()

        return {
            "handles": handles,
            "model": body.get("model", model),
            "usage": body.get("usage"),
            "count": len(handles),
        }
