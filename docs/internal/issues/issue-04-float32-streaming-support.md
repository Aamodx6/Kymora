---
title: "feat: Add np.float32 support to StreamingExtractor"
labels: ["enhancement", "good first issue", "performance", "numerics"]
---

## Context
Currently, `StreamingExtractor` primarily operates with double-precision `f64` buffers. Edge and embedded devices collecting streaming sensor readings often supply `float32` arrays to save memory and bus bandwidth.

## Acceptance Criteria
1. Allow `StreamingExtractor` to ingest `float32` inputs without requiring Python-side conversion to `float64`.
2. Maintain an internal `f64` accumulator for shifted power sums to preserve numerical stability against catastrophic cancellation.
3. Verify that `push` throughput remains $\le 0.25\ \mu\text{s}$ per sample.

## Files to Touch
- `src/streaming.rs`: Add generic or `f32` conversion path to `push` / `push_many`.
- `python/kymora/streaming.py`: Update type annotations and docstrings.

## Tests to Add
- `tests/unit/test_streaming_f32.py`: Push `np.float32` arrays and compare results with `float64` execution within single-precision epsilon bounds.
