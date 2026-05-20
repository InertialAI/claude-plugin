---
name: setup
description: Diagnose and guide InertialAI API key setup. Use when the user wants to configure the plugin or when API calls fail with authentication errors.
---

Use this skill when the user says something like "set up inertial ai", "configure the api key", or when an InertialAI tool returns an auth error (HTTP 401 / "No InertialAI API key found").

## Cardinal rule: never accept the API key in chat

If the user pastes their key into the conversation, it lands in the transcript and gets sent to Anthropic's servers, possibly logged, possibly cached. The correct flow is to have them run a terminal command (in their own shell) that reads the key via `getpass` so it never enters chat history.

If the user offers to paste the key, stop them and direct them to the terminal commands below.

## Workflow

1. Call the `check_setup` MCP tool. It returns:
   - `api_key_present`: whether a key is currently configured
   - `source`: `"env"` (environment variable), `"keyring"` (OS keychain), or `"none"`
   - `setup_command`: the exact `uv run --script ...` command to run, when no key is set
   - `env_var_alternative`: the shell-rc snippet to use, when no key is set
   - `keyring_available`: whether the keyring backend loaded

2. If `api_key_present` is true, tell the user which source is active and stop.

3. If false, present both options and let the user pick:
   - **OS keychain (recommended on macOS / Linux desktop / Windows):** copy-paste the `setup_command` into their terminal. The script prompts for the key with hidden input, validates it against the API, and stores it. Falls back gracefully if no keychain backend is available.
   - **Environment variable (simplest, works everywhere including headless / WSL):** add the `env_var_alternative` snippet to `~/.zshrc` or `~/.bashrc`, then restart their shell.

4. After they've done either step, tell them to run `/reload-plugins` in this session, or start a fresh `claude` session. Then call `check_setup` again to confirm.

## Don't

- Don't ask for the key in chat.
- Don't write the key to any file under the repo, `${CLAUDE_PLUGIN_DATA}`, or the conversation.
- Don't echo or repeat the key even if the user sends it — that puts it in the response cache.
