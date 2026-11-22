# Headline Throughput Protocol Report (HEAD)

Rigorous multi-session protocol on repository HEAD under strict High Performance power scheme and AC online.
- **Protocol:** 3 interleaved sessions × 4 rounds × 30 runs (360 total measurements).
- **Workload:** 1,000 series × 500 steps, float64 C-contiguous gaussian, 16 threads.

## Summary Metrics

- **Pooled Headline Throughput:** **575,391 series/s** (median **1.74 ms**)
- **95% Bootstrap Confidence Interval:** **[566,701, 581,581] series/s** ([1.72, 1.76] ms)
- **Best Single Run:** **799,680 series/s** (1.25 ms)
- **Inter-Session Range:** **559,268 – 598,247 series/s**

## Per-Session Breakdown

| Session | Runs | Median (ms) | Throughput (series/s) | Min (ms) | Max (ms) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Session 1 | 120 | 1.672 ms | 598,247 series/s | 1.250 ms | 2.586 ms |
| Session 2 | 120 | 1.788 ms | 559,268 series/s | 1.494 ms | 3.306 ms |
| Session 3 | 120 | 1.773 ms | 564,127 series/s | 1.297 ms | 2.461 ms |
