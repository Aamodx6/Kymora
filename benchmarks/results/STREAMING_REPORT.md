# Streaming Re-validation Report (HEAD)

Suite: `benchmarks/suites/streaming.py` (B3) re-run on repository HEAD.
System: Windows 11, High Performance plan, AC online, single thread.
Every capacity is parity-gated before timing (`compute(all) == core33`, `compute(fast) == fast subset`).

> [!NOTE]
> **Complexity Contract:**
> - Ingestion: **amortized $O(1)$ per-sample ingestion, worst-case $O(W)$ upon drift re-anchoring**.
> - Periodic re-anchoring passes over the window buffer (timed separately and showing in p99.9/max).
> - Fast subset query: **$O(1)$ flat query latency** across all window capacities.

## Measured Latency vs Window Capacity

| Window Capacity (W) | Gate Rel Diff | push p50 (p99 / p99.9) (µs) | Re-anchor Event p50 (max) (µs) | compute(fast) p50 (p99 / max) (µs) | compute(all) p50 (µs) | Naive Recompute p50 (µs) | Speedup (fast vs naive) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 64 | 7.72e-16 | 0.20 (0.30 / 0.50) µs | 6.6 (22.1) µs | 0.30 (0.90 / 5.6) µs | 1.60 µs | 29.70 µs | 99.0× |
| 256 | 6.51e-16 | 0.20 (0.20 / 0.50) µs | 3.6 (58.5) µs | 0.30 (0.40 / 0.9) µs | 5.40 µs | 28.20 µs | 94.0× |
| 4,096 | 3.78e-14 | 0.20 (0.20 / 0.30) µs | 16.7 (38.4) µs | 0.30 (0.40 / 16.3) µs | 73.90 µs | 120.00 µs | 400.0× |
| 65,536 | 2.97e-14 | 0.20 (0.30 / 0.30) µs | 276.2 (330.2) µs | 0.30 (0.40 / 1.1) µs | 1329.50 µs | 2232.50 µs | 7441.6× |
