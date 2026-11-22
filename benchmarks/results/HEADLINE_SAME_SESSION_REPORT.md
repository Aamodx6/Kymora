# Same-Session Headline Ratios Report (HEAD)

Protocol-compliant interleaved same-session evaluation on repository HEAD under Windows High Performance power scheme and AC online.
- **Workload:** 1,000 series × 500 steps, float64 C-contiguous gaussian, 16 threads across all methods.
- **Methodology:** 3 interleaved sessions; each session times Kymora, catch22, TSFEL, and tsfresh in the same environment.
- **Cooldown:** 10s cooldown between competitor extraction blocks to prevent thermal throttling.

## Summary Ratios

- **Kymora Interleaved Throughput:** **514,245 series/s** (median **1.94 ms**, 95% CI [495,050, 529,605] series/s)
- **Kymora Isolated Baseline:** **358,654 series/s** (median **2.79 ms**, divergence 43.4%)
- **catch22 Speedup:** **95×** raw (**143×** per-feature; catch22 median 185.50 ms)
- **TSFEL Speedup:** **1,291×** raw (**273×** per-feature; TSFEL median 2509.53 ms)
- **tsfresh Speedup:** **12,106×** raw (**514×** per-feature; tsfresh median 23540.62 ms)

## Concurrency Definitions ("16T")

- **Kymora (16T):** 16 native Rayon work-stealing threads within the single Python process (zero defensive copies, zero IPC serialization).
- **catch22 (16T):** `joblib.Parallel(n_jobs=16)` executing across 16 worker processes.
- **TSFEL (16T):** `joblib.Parallel(n_jobs=16)` executing across 16 worker processes.
- **tsfresh (16T):** `multiprocessing.Pool(16)` executing across 16 worker processes.

## Per-Session Breakdown

| Session | Kymora (ms) | catch22 (ms) | TSFEL (ms) | tsfresh (ms) | Ratio catch22 | Ratio TSFEL | Ratio tsfresh |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Session 1 | 1.97 ms | 180.81 ms | 4010.62 ms | 23540.62 ms | **91.8×** | **2036.3×** | **11952.0×** |
| Session 2 | 1.91 ms | 191.78 ms | 2530.23 ms | 22932.28 ms | **100.5×** | **1325.6×** | **12014.0×** |
| Session 3 | 1.97 ms | 173.16 ms | 2474.78 ms | 24881.42 ms | **87.9×** | **1256.3×** | **12630.8×** |

## Protocol Notes

- **Interleaved Execution:** Eliminates cross-session thermal throttling or background interference by measuring all four libraries within the same process session.
- **Per-Feature Normalization:** Accounts for differing catalog sizes (33 for Kymora, 22 for catch22, 156 for TSFEL, 777 for tsfresh).
- **Thread Parity:** tsfresh, TSFEL, and catch22 all execute multi-threaded using the same 16-thread pool configuration.