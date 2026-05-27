"""API key resolution + the standard 'no key configured' error payload.

Resolution order: `INERTIAL_API_KEY` env var → OS keychain → none. Env wins
so users can override stored credentials per shell.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import keyring as _keyring

    HAS_KEYRING = True
except Exception:
    HAS_KEYRING = False

API_BASE = os.environ.get("INERTIAL_API_BASE", "https://inertialai.com")
KEYRING_SERVICE = "inertialai"
KEYRING_USERNAME = "default"


def resolve_api_key() -> tuple[str | None, str]:
    """Return (api_key, source) where source is 'env', 'keyring', or 'none'."""
    env = os.environ.get("INERTIAL_API_KEY")
    if env:
        return env, "env"
    if HAS_KEYRING:
        try:
            stored = _keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if stored:
                return stored, "keyring"
        except Exception:
            pass
    return None, "none"


def setup_script_path() -> Path:
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        return Path(root) / "scripts" / "setup-key.py"
    return Path(__file__).resolve().parent.parent / "scripts" / "setup-key.py"


def missing_key_error() -> dict[str, Any]:
    script = setup_script_path()
    return {
        "error": "No InertialAI API key found.",
        "fix": (
            "Run `/inertialai:setup` for guided setup, or set "
            "INERTIAL_API_KEY in your shell, or run "
            f"`uv run --script {script}` in your terminal to store "
            "the key in your OS keychain."
        ),
    }
