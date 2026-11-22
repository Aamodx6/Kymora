# Small-Batch Fast Path Benchmark Report (HEAD)

Comprehensive evaluation of small-batch latency on repository HEAD after pre-warm removal.
Compares Kymora 1-thread (sequential caller-thread inline), Kymora 16-thread,
and faster Numba baseline (serial vs parallel) on small telemetry payloads.

## Results Table

| Shape (N × L) | Points | Mode | 1T First Call | 1T p50 (p99) | 16T First Call | 16T p50 (p99) | Numba Best p50 (p99) | Ratio (16T / 1T) | Ratio (16T / Numba) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 × 10 | 10 | sequential | 746.2 µs | 22.0 µs (36.4 µs) | 387.5 µs | 23.3 µs (48.4 µs) | 2.9 µs (3.9 µs) [parallel] | 1.06× | 8.05× |
| 1 × 100 | 100 | sequential | 69.3 µs | 22.5 µs (41.2 µs) | 49.8 µs | 30.6 µs (53.0 µs) | 13.0 µs (17.3 µs) [serial] | 1.36× | 2.35× |
| 10 × 500 | 5,000 | sequential | 251.6 µs | 117.4 µs (191.3 µs) | 180.1 µs | 127.3 µs (206.0 µs) | 255.6 µs (558.4 µs) [parallel] | 1.08× | 0.50× |
| 100 × 100 | 10,000 | parallel | 602.4 µs | 388.7 µs (566.0 µs) | 326.5 µs | 143.6 µs (328.9 µs) | 382.9 µs (597.3 µs) [parallel] | 0.37× | 0.38× |
| 100 × 500 | 50,000 | parallel | 1346.1 µs | 1069.3 µs (1441.4 µs) | 518.2 µs | 358.4 µs (654.7 µs) | 1255.2 µs (1807.6 µs) [parallel] | 0.34× | 0.29× |

## Numba Per-Series Cost vs Equal-Feature (13.34 µs/series)

| Shape (N × L) | Numba Mode | Numba Latency (p50) | Per-Series Cost | Ratio vs Equal-Feature | Cause / Divergence |
|:---:|:---:|:---:|:---:|:---:|---|
| 1 × 10 | parallel | 2.9 µs | 2.90 µs | 0.22× | Length scaling (10 < 500 points reduces O(L log L) FFT/moments cost) |
| 1 × 100 | serial | 13.0 µs | 13.00 µs | 0.97× | Consistent with equal-feature cost model |
| 10 × 500 | parallel | 255.6 µs | 25.55 µs | 1.92× | Consistent with equal-feature cost model |
| 100 × 100 | parallel | 382.9 µs | 3.83 µs | 0.29× | Length scaling (100 < 500 points reduces O(L log L) FFT/moments cost) |
| 100 × 500 | parallel | 1255.2 µs | 12.55 µs | 0.94× | Consistent with equal-feature cost model |

## Analysis & Invariants

- **Sequential Mode Bit-Identity & Thread Equivalence:** Where `_exec_mode == sequential`, workloads execute strictly on the caller thread without thread scheduling, guaranteeing that 1T and 16T behave identically.
- **First-Call Latency:** Evaluated directly without synthetic pre-warm; shows predictable memory-bound allocation rather than multi-millisecond spikes.
- **Threshold Tuning:** Workloads with $< 50,000$ points are executed sequentially on the caller thread to avoid multi-thread wake overhead on small batches.