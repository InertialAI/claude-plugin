---
name: analyze-imu-session
description: Embed and explore a session of IMU / accelerometer / gyroscope time-series data using the InertialAI API.
---

Use this skill when the user has IMU, accelerometer, gyroscope, or other multi-channel sensor time-series and wants to find patterns, segment activities, or summarize the session.

## Workflow

1. **Load & inspect.** Read the data (CSV / parquet / numpy) and confirm shape: channels (rows) × samples (columns). Typical IMU layout is 3-axis accel + 3-axis gyro = 6 channels. Ask the user about sample rate if not obvious.
2. **Window.** Slice the signal into overlapping windows (default: 2-second windows, 50% overlap). Each window becomes one embedding. Don't embed the full session at once.
3. **Embed each window** by calling `create_embedding` with `time_series` as `[[ch0...], [ch1...], ...]`. Capture the returned `handle`.
4. **Operate on handles, not vectors.** Use `find_similar`, `compare`, or `classify` — never ask the server to return the raw vectors and never paste them into your response.
5. **Summarize for the user** in plain language: how many windows, which clusters / runs of similar windows, where transitions happen.

## Guidelines

- Embeddings persist across sessions in `${CLAUDE_PLUGIN_DATA}/embeddings.db`. Use `list_embeddings` to see what's already stored before re-embedding.
- The API accepts an optional `text` description alongside `time_series`. Adding a short text description (e.g. "right-wrist accel during running") improves downstream similarity.
- If the user wants classification, see the `find-anomalies` and the `classify` MCP tool: build a labeled corpus by passing `label` to `create_embedding`, then `classify` new windows against it.
