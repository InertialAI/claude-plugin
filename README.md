# InertialAI Claude Code plugin

Time-series embedding and analysis tools for [Claude Code](https://docs.claude.com/en/docs/claude-code), powered by the [InertialAI API](https://docs.inertialai.com).

## Install

```
/plugin marketplace add InertialAI/claude-plugin
/plugin install inertialai@inertialai-plugins
```

Then configure your API key (see below). Requires [`uv`](https://docs.astral.sh/uv/) on `PATH` — the MCP server runs as a `uv` script with inline dependencies, nothing else to install.

## API key

The server resolves the key in this order: `INERTIAL_API_KEY` env var → OS keychain → none. Pick whichever fits your platform:

- **OS keychain (recommended on macOS / Linux desktop / Windows).** In Claude Code, run `/inertialai:setup` — it walks you through running a one-time terminal command that reads the key via `getpass`, validates it, and stores it in your OS keychain. The key never enters the chat.
- **Environment variable (works everywhere including headless Linux / WSL).** Add `export INERTIAL_API_KEY='your-key'` to `~/.zshrc` or `~/.bashrc`, restart your shell.

Never paste your API key into a Claude Code prompt — it would land in transcripts and request logs. Use one of the two paths above.

## Layout

```
.
├── .claude-plugin/marketplace.json          # marketplace catalog
└── plugins/inertialai/
    ├── .claude-plugin/plugin.json           # plugin manifest
    ├── .mcp.json                            # declares the MCP server
    ├── server/server.py                     # MCP server wrapping /api/v1/embeddings
    ├── scripts/setup-key.py                 # one-time interactive key installer
    └── skills/                              # playbooks Claude auto-invokes
        ├── analyze-imu-session/SKILL.md
        ├── find-anomalies/SKILL.md
        ├── compare-sessions/SKILL.md
        └── setup/SKILL.md
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
| `check_setup` | Diagnose API key state and surface setup instructions. |

Embeddings persist in `${CLAUDE_PLUGIN_DATA}/embeddings.db`.

## Adding new models

The API takes `model` as a parameter, so new embedding models work without a plugin update. New endpoint families (forecasting, classification-as-a-service, etc.) get new tools added to `server/server.py`.

## Roadmap

Currently Claude Code only. The MCP server runs as a local subprocess (`uv run --script`), which Cowork's hosted runtime doesn't support. Cowork compatibility is pending a hosted HTTP MCP gateway at `mcp.inertialai.com`; once that ships, the same plugin will work in both products.
