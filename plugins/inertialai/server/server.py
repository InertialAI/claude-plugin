# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "mcp>=1.2.0",
#   "httpx>=0.27",
#   "keyring>=24.0.0",
# ]
# ///
"""MCP server wrapping the InertialAI embeddings API.

Tools operate on locally-stored handles rather than raw vectors so that
512-dim floats never enter the model's context window.
"""

from __future__ import annotations

import os
import sqlite3
import struct
import uuid
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

try:
    import keyring as _keyring

    _HAS_KEYRING = True
except Exception:
    _HAS_KEYRING = False

API_BASE = os.environ.get("INERTIAL_API_BASE", "https://inertialai.com")
KEYRING_SERVICE = "inertialai"
KEYRING_USERNAME = "default"
DATA_DIR = Path(
    os.environ.get("INERTIAL_DATA_DIR")
    or os.environ.get("CLAUDE_PLUGIN_DATA")
    or Path.home() / ".inertialai"
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "embeddings.db"

mcp = FastMCP("inertialai")


def _resolve_api_key() -> tuple[str | None, str]:
    """Return (api_key, source) where source is 'env', 'keyring', or 'none'.

    Env var wins so users can override stored credentials per-shell.
    """
    env = os.environ.get("INERTIAL_API_KEY")
    if env:
        return env, "env"
    if _HAS_KEYRING:
        try:
            stored = _keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if stored:
                return stored, "keyring"
        except Exception:
            pass
    return None, "none"


def _setup_script_path() -> Path:
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        return Path(root) / "scripts" / "setup-key.py"
    return Path(__file__).resolve().parent.parent / "scripts" / "setup-key.py"


def _missing_key_error() -> dict[str, Any]:
    script = _setup_script_path()
    return {
        "error": "No InertialAI API key found.",
        "fix": (
            "Run `/inertialai:setup` for guided setup, or set "
            "INERTIAL_API_KEY in your shell, or run "
            f"`uv run --script {script}` in your terminal to store "
            "the key in your OS keychain."
        ),
    }


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            handle TEXT PRIMARY KEY,
            model TEXT NOT NULL,
            dim INTEGER NOT NULL,
            vector BLOB NOT NULL,
            text TEXT,
            label TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", blob))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@mcp.tool()
async def create_embedding(
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
    api_key, _ = _resolve_api_key()
    if not api_key:
        return _missing_key_error()
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
    conn = _db()
    for item in items:
        vec = item.get("embedding") or item.get("vector") or []
        if not vec:
            continue
        handle = uuid.uuid4().hex[:12]
        conn.execute(
            "INSERT INTO embeddings (handle, model, dim, vector, text, label) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (handle, body.get("model", model), len(vec), _pack(vec), text, label),
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


@mcp.tool()
def list_models() -> dict[str, Any]:
    """List available InertialAI models.

    Currently a static list; switch to a live `/v1/models` call when the
    API exposes one so new model launches reach users without a plugin
    update.
    """
    return {
        "models": [
            {"id": "inertial-embed-alpha", "type": "embedding"},
            {"id": "dummy", "type": "embedding"},
        ]
    }


@mcp.tool()
def compare(handle_a: str, handle_b: str) -> dict[str, Any]:
    """Cosine similarity between two stored embeddings.

    Returns a single float in [-1, 1]; close to 1 means similar.
    """
    conn = _db()
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
    a = _unpack(*rows[handle_a])
    b = _unpack(*rows[handle_b])
    return {"similarity": _cosine(a, b)}


@mcp.tool()
def find_similar(
    query_handle: str,
    corpus_handles: list[str] | None = None,
    k: int = 5,
) -> dict[str, Any]:
    """Top-k most similar embeddings to a query.

    If `corpus_handles` is omitted, searches every stored embedding except
    the query itself.
    """
    conn = _db()
    qrow = conn.execute(
        "SELECT vector, dim FROM embeddings WHERE handle = ?", (query_handle,)
    ).fetchone()
    if qrow is None:
        conn.close()
        return {"error": f"Unknown handle: {query_handle}"}
    q = _unpack(qrow[0], qrow[1])

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
            "similarity": _cosine(q, _unpack(v, d)),
            "label": label,
            "text": text,
        }
        for (h, v, d, label, text) in cursor
    ]
    conn.close()
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return {"matches": scored[:k]}


@mcp.tool()
def classify(
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
    conn = _db()
    qrow = conn.execute(
        "SELECT vector, dim FROM embeddings WHERE handle = ?", (query_handle,)
    ).fetchone()
    if qrow is None:
        conn.close()
        return {"error": f"Unknown handle: {query_handle}"}
    q = _unpack(qrow[0], qrow[1])

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
        {"handle": h, "label": label, "similarity": _cosine(q, _unpack(v, d))}
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


@mcp.tool()
def list_embeddings(
    label: str | None = None, limit: int = 100
) -> dict[str, Any]:
    """List stored embeddings (handles, labels, descriptions).

    Optionally filter by `label`. Use this to inspect the local corpus.
    """
    conn = _db()
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


@mcp.tool()
def delete_embedding(handle: str) -> dict[str, Any]:
    """Delete a stored embedding by handle."""
    conn = _db()
    cur = conn.execute("DELETE FROM embeddings WHERE handle = ?", (handle,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return {"deleted": deleted}


@mcp.tool()
def check_setup() -> dict[str, Any]:
    """Diagnose API key configuration. Use this when starting work, when an
    API call fails with auth errors, or when the user asks how to set up
    the plugin.

    Returns whether a key is available, from which source, and the exact
    terminal command to run if setup is needed.
    """
    api_key, source = _resolve_api_key()
    script = _setup_script_path()
    result: dict[str, Any] = {
        "api_key_present": api_key is not None,
        "source": source,
        "api_base": API_BASE,
        "data_dir": str(DATA_DIR),
        "keyring_available": _HAS_KEYRING,
    }
    if api_key is None:
        result["setup_command"] = f"uv run --script {script}"
        result["env_var_alternative"] = (
            "export INERTIAL_API_KEY='your-key'  # add to ~/.zshrc or ~/.bashrc"
        )
    return result


if __name__ == "__main__":
    mcp.run()
