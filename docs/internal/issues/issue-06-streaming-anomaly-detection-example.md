---
title: "docs: Real-time streaming anomaly detection tutorial"
labels: ["documentation", "good first issue", "examples"]
---

## Context
Kymora's `StreamingExtractor` computes rolling statistics in amortized $O(1)$ time with a $0.3\ \mu\text{s}$ fast evaluation latency. A tutorial showing how to combine rolling streaming features with an online anomaly detection algorithm (e.g. Half-Space Trees or an incremental Isolation Forest) will demonstrate real-time telemetry processing.

## Acceptance Criteria
1. Create a runnable tutorial script in `docs/examples/streaming_anomaly_detection.py`.
2. Generate synthetic telemetry (sensor signals with sudden mean shifts or variance spikes).
3. Demonstrate sample-by-sample ingestion with `push()` and rolling anomaly scoring.
4. Add clear markdown walkthrough in `docs/tutorials/streaming_anomaly.md`.

## Files to Touch
- `docs/examples/streaming_anomaly_detection.py`
- `docs/tutorials/streaming_anomaly.md`
- `mkdocs.yml`: Add tutorial to navigation.

## Tests to Add
- Add execution check in docs build or CI example runner.
