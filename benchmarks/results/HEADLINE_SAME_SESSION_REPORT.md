# Same-Session Headline Ratios Report (HEAD)

Protocol-compliant interleaved same-session evaluation on repository HEAD under Windows High Performance power scheme and AC online.
- **Workload:** 1,000 series × 500 steps, float64 C-contiguous gaussian, 16 threads across all methods.
- **Methodology:** 3 interleaved sessions; each session times Kymora, catch22, TSFEL, and tsfresh in the same environment.

## Summary Ratios

- **Kymora Headline Throughput:** **428,633 series/s** (median **2.33 ms**, 95% CI [367,067, 475,896] series/s)
- **catch22 Speedup:** **84×** raw (**127×** per-feature; catch22 median 196.82 ms)
- **TSFEL Speedup:** **1,177×** raw (**249×** per-feature; TSFEL median 2745.41 ms)
- **tsfresh Speedup:** **10,502×** raw (**446×** per-feature; tsfresh median 24500.85 ms)

## Per-Session Breakdown

| Session | Kymora (ms) | catch22 (ms) | TSFEL (ms) | tsfresh (ms) | Ratio catch22 | Ratio TSFEL | Ratio tsfresh |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Session 1 | 4.12 ms | 222.30 ms | 4099.49 ms | 23199.34 ms | **54.0×** | **995.5×** | **5633.4×** |
| Session 2 | 2.00 ms | 198.87 ms | 2628.13 ms | 24500.85 ms | **99.6×** | **1316.0×** | **12268.2×** |
| Session 3 | 2.13 ms | 195.42 ms | 2965.92 ms | 24690.93 ms | **91.8×** | **1394.0×** | **11604.5×** |

## Protocol Notes

- **Interleaved Execution:** Eliminates cross-session thermal throttling or background interference by measuring all four libraries within the same process session.
- **Per-Feature Normalization:** Accounts for differing catalog sizes (33 for Kymora, 22 for catch22, 156 for TSFEL, 777 for tsfresh).
- **Thread Parity:** tsfresh, TSFEL, and catch22 all execute multi-threaded using the same 16-thread pool configuration.