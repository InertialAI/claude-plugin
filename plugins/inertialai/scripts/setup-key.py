# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "httpx>=0.27",
#   "keyring>=24.0.0",
# ]
# ///
"""Store an InertialAI API key in your OS keychain.

Run this in your terminal — never paste your API key into a Claude Code chat
(the key would land in transcripts and request logs).

  uv run --script /path/to/setup-key.py

The key is read via getpass (no echo), validated against the InertialAI API,
and stored in your OS keychain (macOS Keychain / libsecret / Windows
Credential Manager). On platforms without a keychain backend (e.g. headless
Linux, plain WSL), the script falls back to instructions for the
INERTIAL_API_KEY environment variable.
"""

from __future__ import annotations

import getpass
import sys

import httpx
import keyring
from keyring.errors import KeyringError

API_BASE = "https://inertialai.com"
SERVICE = "inertialai"
USERNAME = "default"


def validate(key: str) -> tuple[bool, str]:
    try:
        r = httpx.post(
            f"{API_BASE}/api/v1/embeddings",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "dummy", "input": {"text": "validate"}},
            timeout=15.0,
        )
    except Exception as e:
        return False, f"Network error reaching {API_BASE}: {e}"
    if r.status_code == 401 or r.status_code == 403:
        return False, f"Authentication failed (HTTP {r.status_code}) — key is invalid"
    if r.status_code < 400:
        return True, "Key validated against /api/v1/embeddings"
    return (
        True,
        f"Key authenticated; API returned {r.status_code} (treated as a payload "
        "issue, not an auth issue)",
    )


def main() -> int:
    print("InertialAI API key setup")
    print("------------------------")
    print(
        "Stores your key in the OS keychain so the Claude Code plugin can read\n"
        "it without exposing it in your shell history or chat transcripts."
    )
    print()

    key = getpass.getpass("Paste your INERTIAL_API_KEY (input hidden): ").strip()
    if not key:
        print("No key entered. Aborting.")
        return 1

    print()
    print("Validating against the InertialAI API...")
    ok, msg = validate(key)
    print(f"  {msg}")
    if not ok:
        print("Aborting. Re-check the key and try again.")
        return 1

    try:
        keyring.set_password(SERVICE, USERNAME, key)
    except KeyringError as e:
        print()
        print(f"Could not store key in OS keychain: {e}")
        print(
            "Your platform has no usable keyring backend (common on headless\n"
            "Linux and plain WSL). Use the environment variable path instead —\n"
            "add this to ~/.zshrc or ~/.bashrc, then restart your shell:\n"
        )
        print("  export INERTIAL_API_KEY='<your key>'")
        print()
        return 2

    print()
    print(f"Stored in OS keychain (service='{SERVICE}', user='{USERNAME}').")
    print("The MCP server will find it automatically next session.")
    print("In an existing Claude Code session, run `/reload-plugins`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
