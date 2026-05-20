---
name: compare-sessions
description: Compare two time-series sessions (e.g. before/after, subject A vs B) by embedding windows and comparing distributions.
---

Use this skill when the user asks to compare two sessions, check whether two recordings represent the same activity, or measure drift between conditions.

## Workflow

1. **Embed both sessions** into windows (see `analyze-imu-session`). Tag handles with a label per session, e.g. `label="session_a"` and `label="session_b"`, so you can retrieve them later via `list_embeddings`.
2. **Pairwise comparison.** For each window in A, call `find_similar(query_handle, corpus_handles=<session_b handles>, k=1)` and record the best similarity. The distribution of best-match similarities tells you how alike the sessions are.
3. **Summary statistics.** Report mean and 10th-percentile of the best-match similarities. High mean + tight distribution = similar sessions. Low mean or long left tail = divergence.
4. **Drill in.** Surface the windows in A that have the *lowest* best-match against B — those are the parts of A that don't appear in B.

## Guidelines

- Don't fetch raw vectors. The `compare` and `find_similar` tools do the math server-side and return small results.
- If sessions have different lengths or sample rates, window them to the same duration before embedding so comparisons are fair.
