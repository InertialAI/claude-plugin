from __future__ import annotations

from typing import Any

from ._base import Tool


class ListModelsTool(Tool):
    name = "list_models"

    def run(self) -> dict[str, Any]:
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
