# InertialAI Claude Code plugin

Time-series embedding and analysis tools for [Claude Code](https://docs.claude.com/en/docs/claude-code), powered by the [InertialAI API](https://docs.inertialai.com).

## Install

```
/plugin marketplace add inertialai/claude-plugin
/plugin install inertial-ai@inertial
export INERTIAL_API_KEY=sk-...
```

Requires [`uv`](https://docs.astral.sh/uv/) on `PATH`. The MCP server runs as a `uv` script with inline dependencies — nothing else to install.

## Layout

```
.
├── .claude-plugin/marketplace.json          # marketplace catalog
└── plugins/inertial-ai/
    ├── .claude-plugin/plugin.json           # plugin manifest
    ├── .mcp.json                            # declares the MCP server
    ├── server/server.py                     # MCP server wrapping /api/v1/embeddings
    └── skills/                              # playbooks Claude auto-invokes
        ├── analyze-imu-session/SKILL.md
        ├── find-anomalies/SKILL.md
        └── compare-sessions/SKILL.md
```

## Tools

All tools operate on stored **handles** rather than raw vectors, so 512-dim floats never enter the model's context.

| Tool | Purpose |
| --- | --- |
| `create_embedding` | Call the API, store the vector locally, return a handle. Pass `label` to add to a classifier corpus. |
| `list_models` | List available embedding models. |
| `compare` | Cosine similarity between two handles. |
| `find_similar` | Top-k most similar handles to a query. |
| `classify` | Nearest-neighbor classify against the labeled corpus. |
| `list_embeddings` / `delete_embedding` | Manage the local store. |

Embeddings persist in `${CLAUDE_PLUGIN_DATA}/embeddings.db`.

## Adding new models

The API takes `model` as a parameter, so new embedding models work without a plugin update. New endpoint families (forecasting, classification-as-a-service, etc.) get new tools added to `server/server.py`.
