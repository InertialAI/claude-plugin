from __future__ import annotations

from typing import Any

from auth import API_BASE, HAS_KEYRING, resolve_api_key, setup_script_path
from store import DATA_DIR

from ._base import Tool


class CheckSetupTool(Tool):
    name = "check_setup"

    def run(self) -> dict[str, Any]:
        """Diagnose API key configuration. Use this when starting work, when an
        API call fails with auth errors, or when the user asks how to set up
        the plugin.

        Returns whether a key is available, from which source, and the exact
        terminal command to run if setup is needed.
        """
        api_key, source = resolve_api_key()
        script = setup_script_path()
        result: dict[str, Any] = {
            "api_key_present": api_key is not None,
            "source": source,
            "api_base": API_BASE,
            "data_dir": str(DATA_DIR),
            "keyring_available": HAS_KEYRING,
        }
        if api_key is None:
            result["setup_command"] = f"uv run --script {script}"
            result["env_var_alternative"] = (
                "export INERTIAL_API_KEY='your-key'  # add to ~/.zshrc or ~/.bashrc"
            )
        return result
