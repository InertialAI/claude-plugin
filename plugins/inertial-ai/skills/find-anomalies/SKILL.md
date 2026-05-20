---
name: find-anomalies
description: Detect anomalous windows in a time-series session by embedding and ranking by distance from the rest of the corpus.
---

Use this skill when the user asks "find anything unusual," "detect anomalies," "flag outliers," or similar in a sensor / time-series session.

## Workflow

1. **Embed all windows** of the session via `create_embedding` (see `analyze-imu-session` for windowing guidance). Collect the handles.
2. **Score each window** against the rest of the corpus: for each handle, call `find_similar(query_handle, corpus_handles=<all others>, k=5)` and take the mean similarity of the top-k. Low mean similarity = anomalous.
3. **Rank** windows by anomaly score (1 − mean_top_k_similarity, descending).
4. **Report** the top few anomalies with their timestamps / window indices and a short description of what's distinctive (you can ask the user to look at the raw signal for those windows).

## Alternative: classify against a known-normal corpus

If the user already has labeled "normal" examples, build a labeled corpus by passing `label="normal"` to `create_embedding`, then `classify` each new window. Anomalies show up as low `similarity` or a small `confidence_gap` to non-normal labels.

## Guidelines

- Never include raw embedding vectors in your response. Operate on handles.
- For long sessions (>500 windows), sample the corpus rather than computing all-pairs similarity in a single turn.
