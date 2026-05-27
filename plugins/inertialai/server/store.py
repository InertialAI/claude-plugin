"""SQLite-backed embedding store + vector math helpers.

Embeddings persist in `${INERTIAL_DATA_DIR}` / `${CLAUDE_PLUGIN_DATA}` /
`~/.inertialai`, in that resolution order.
"""

from __future__ import annotations

import os
import sqlite3
import struct
from pathlib import Path

DATA_DIR = Path(
    os.environ.get("INERTIAL_DATA_DIR")
    or os.environ.get("CLAUDE_PLUGIN_DATA")
    or Path.home() / ".inertialai"
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "embeddings.db"


def db() -> sqlite3.Connection:
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


def pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def unpack(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", blob))


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
