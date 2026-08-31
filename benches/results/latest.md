# Batch-throughput benchmark

1000 series x 500 steps, 16 cores, Windows-11-10.0.26200-SP0, Python 3.14.6.

Time is wall clock for the whole batch, including the input reshaping each library requires. Each library gets the best of as many runs as fit in a two-second budget, so the fast path is not reported as one noisy millisecond.

| library | features | total time | series/s | ms/feature | vs tsxtractor |
|---|---:|---:|---:|---:|---:|
| tsxtractor 0.2.1 | 33 | 1.2 ms | 800,256 | 0.0379 | baseline |
| catch22 (pycatch22) | 22 | 1.02 s | 976 | 46.5805 | 820x slower |
| TSFEL (all domains) | 156 | 7.15 s | 140 | 45.8591 | 5,725x slower |
| tsfresh (EfficientFCParameters) | 777 | 17.68 s | 57 | 22.7584 | 14,151x slower |

Read this honestly: these libraries compute different numbers of features, so total time is not a like-for-like comparison. The tsxtractor advantage is parallelising across series in native code; on a single short series it will not look meaningfully faster than catch22.

- **tsxtractor 0.2.1** -- Rust core, rayon across series, zero-copy input
- **catch22 (pycatch22)** -- C core, single-threaded Python loop over series
- **TSFEL (all domains)** -- Python/numba, per-series extractor calls
- **tsfresh (EfficientFCParameters)** -- includes the long-format reshape, its required input form
