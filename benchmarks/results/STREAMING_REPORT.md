# Streaming Re-validation Report (HEAD)

Suite: `benchmarks/suites/streaming.py` (B3) re-run on repository HEAD.
System: Windows 11, High Performance plan, AC online, single thread.
Every capacity is parity-gated before timing (`compute(all) == core33`, `compute(fast) == fast subset`).

> [!NOTE]
> **Complexity Contract:**
> - Ingestion: **amortized $O(1)$ per-sample ingestion, worst-case $O(W)$ upon drift re-anchoring**.
> - Periodic re-anchoring passes over the window buffer (showing in max push latency).
> - Fast subset query: **$O(1)$ flat query latency** across all window capacities.

## Measured Latency vs Window Capacity

| Window Capacity (W) | Gate Rel Diff | push p50 (p99 / max) (µs) | compute(fast) p50 (p99 / max) (µs) | compute(all) p50 (µs) | Naive Recompute p50 (µs) | Speedup (fast vs naive) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 64 | 7.72e-16 | 0.20 (0.20 / 60.1) µs | 0.30 (0.40 / 3.9) µs | 1.80 µs | 26.05 µs | 86.8× |
| 256 | 6.51e-16 | 0.20 (0.20 / 68.2) µs | 0.30 (0.40 / 0.8) µs | 5.40 µs | 26.50 µs | 88.3× |
| 4,096 | 3.78e-14 | 0.20 (0.20 / 21.7) µs | 0.30 (0.40 / 1.6) µs | 73.30 µs | 107.80 µs | 359.3× |
| 65,536 | 2.97e-14 | 0.20 (0.20 / 315.7) µs | 0.30 (0.30 / 0.9) µs | 1326.60 µs | 2569.95 µs | 8566.4× |
