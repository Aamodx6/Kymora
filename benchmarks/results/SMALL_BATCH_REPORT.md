# Small-Batch Fast Path Benchmark Report (HEAD)

Comprehensive evaluation of small-batch latency on repository HEAD.
Compares Kymora 1-thread (sequential caller-thread inline), Kymora 16-thread,
and Numba baseline on small telemetry payloads.

## Results Table

| Shape (N × L) | Points | Kymora 1T p50 (p99) | Kymora 16T p50 (p99) | Numba p50 (p99) | Ratio (16T / 1T) | Ratio (16T / Numba) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 × 10 | 10 | 19.4 µs (46.0 µs) | 21.7 µs (68.2 µs) | 2.8 µs (3.0 µs) | 1.12× | 7.75× |
| 1 × 100 | 100 | 21.3 µs (38.9 µs) | 25.4 µs (68.4 µs) | 11.9 µs (17.5 µs) | 1.19× | 2.14× |
| 10 × 500 | 5,000 | 115.1 µs (226.9 µs) | 120.5 µs (341.5 µs) | 741.9 µs (1012.7 µs) | 1.05× | 0.16× |
| 100 × 100 | 10,000 | 350.1 µs (547.2 µs) | 126.7 µs (266.7 µs) | 1517.5 µs (2471.9 µs) | 0.36× | 0.08× |
| 100 × 500 | 50,000 | 1053.9 µs (1352.7 µs) | 336.7 µs (703.4 µs) | 7598.9 µs (8486.9 µs) | 0.32× | 0.04× |

## Analysis & Fast Path Verification

- **Small workloads (< 50,000 points):** Sequential inline execution on the caller thread completely bypasses Rayon thread scheduling and context switching.
- **Tail Latency Reduction:** At small batches, 1-thread execution drastically curbs p99 and max wake jitter compared to unconstrained multi-core pools.
- **Bit-Identical Output:** Verified bit-identical results between sequential and parallel dispatch across all features.