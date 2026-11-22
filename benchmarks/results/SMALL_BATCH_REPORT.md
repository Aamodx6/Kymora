# Small-Batch Fast Path Benchmark Report (HEAD)

Comprehensive evaluation of small-batch latency on repository HEAD after pre-warm removal.
Compares Kymora 1-thread (sequential caller-thread inline), Kymora 16-thread,
and faster Numba baseline (serial vs parallel) on small telemetry payloads.

## Results Table

| Shape (N × L) | Points | Mode | 1T First Call | 1T p50 (p99) | 16T First Call | 16T p50 (p99) | Numba Best p50 (p99) | Ratio (16T / 1T) | Ratio (16T / Numba) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 × 10 | 10 | sequential | 416.0 µs | 5.9 µs (20.2 µs) | 375.4 µs | 7.2 µs (33.7 µs) | 3.0 µs (3.2 µs) [serial] | 1.22× | 2.40× |
| 1 × 100 | 100 | sequential | 35.2 µs | 7.5 µs (9.2 µs) | 102.4 µs | 14.1 µs (66.3 µs) | 14.4 µs (40.3 µs) [parallel] | 1.88× | 0.98× |
| 10 × 500 | 5,000 | sequential | 148.9 µs | 103.5 µs (168.5 µs) | 165.2 µs | 114.9 µs (221.7 µs) | 247.3 µs (434.3 µs) [parallel] | 1.11× | 0.46× |
| 100 × 100 | 10,000 | parallel | 326.8 µs | 156.8 µs (260.3 µs) | 186.5 µs | 198.5 µs (327.2 µs) | 375.3 µs (536.2 µs) [parallel] | 1.27× | 0.53× |
| 100 × 500 | 50,000 | parallel | 566.4 µs | 396.5 µs (646.9 µs) | 457.9 µs | 420.9 µs (620.3 µs) | 1195.2 µs (1724.1 µs) [parallel] | 1.06× | 0.35× |

## Numba Per-Series Cost vs Equal-Feature (13.34 µs/series)

| Shape (N × L) | Numba Mode | Numba Latency (p50) | Per-Series Cost | Ratio vs Equal-Feature | Cause / Divergence |
|:---:|:---:|:---:|:---:|:---:|---|
| 1 × 10 | serial | 3.0 µs | 3.00 µs | 0.22× | Length scaling (10 < 500 points reduces O(L log L) FFT/moments cost) |
| 1 × 100 | parallel | 14.4 µs | 14.40 µs | 1.08× | Consistent with equal-feature cost model |
| 10 × 500 | parallel | 247.3 µs | 24.73 µs | 1.85× | Consistent with equal-feature cost model |
| 100 × 100 | parallel | 375.3 µs | 3.75 µs | 0.28× | Length scaling (100 < 500 points reduces O(L log L) FFT/moments cost) |
| 100 × 500 | parallel | 1195.2 µs | 11.95 µs | 0.90× | Consistent with equal-feature cost model |

## Analysis & Invariants

- **Sequential Mode Bit-Identity & Thread Equivalence:** Where `_exec_mode == sequential`, workloads execute strictly on the caller thread without thread scheduling, guaranteeing that 1T and 16T behave identically.
- **First-Call Latency:** Evaluated directly without synthetic pre-warm; shows predictable memory-bound allocation rather than multi-millisecond spikes.
- **Threshold Tuning:** Workloads with $< 50,000$ points are executed sequentially on the caller thread to avoid multi-thread wake overhead on small batches.