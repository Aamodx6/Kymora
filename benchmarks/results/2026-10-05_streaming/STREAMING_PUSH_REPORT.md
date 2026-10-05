# Streaming per-push cost vs window size (Phase 2.4)

Suite: `benchmarks/suites/streaming.py` (B3), run 2026-10-05 on
i7-13620H laptop (10 cores / 16 threads), Windows 11, Performance plan,
AC online, single thread. Every capacity parity-gated before timing
(`compute(all) == core33`, `compute(fast) == fast subset`, max rel err
shown). Exploratory single-machine numbers, not fleet evidence.

| Capacity | Gate max rel | push (µs) | compute fast p50 (µs) | compute all p50 (µs) | naive recompute p50 (µs) |
| --- | --- | --- | --- | --- | --- |
| 64 | 7.72e-16 | 0.205 | 0.60 | 3.6 | 438.1 |
| 256 | 6.51e-16 | 0.218 | 0.70 | 11.6 | 300.9 |
| 4096 | 3.78e-14 | 0.195 | 0.40 | 138.5 | 494.1 |
| 65536 | 2.97e-14 | 0.314 | 0.40 | 2350.0 | 6076.8 |

End-to-end (cap 256, 99,744 points, compute every 64): streaming 0.030s vs naive 0.432s = 14.4x speedup.

Reading: `push` and `compute(fast)` are flat across 64..65536 (O(1));
`compute(all)` grows linearly with W (O(W) batch pipeline).

![per-push and compute cost vs window size](../../docs/img/streaming_push_cost.png)
