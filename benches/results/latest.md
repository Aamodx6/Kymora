# Batch-throughput benchmark

1000 series x 500 steps, 16 worker threads, Windows-11-10.0.26200-SP0, Python 3.14.6.

Time is reported as Median ± IQR across repeated runs, including input reshaping.

| library | features | median time | IQR | mean time | series/s | ms/feature | vs tsxtractor |
|---|---:|---:|---:|---:|---:|---:|---:|
| tsxtractor 0.3.0 | 33 | 1.70 ms | 0.26 ms | 1.73 ms | 586,717 | 0.0516 | baseline |
| catch22 (pycatch22) | 22 | 1.01 s | 1.69 ms | 1.01 s | 986 | 46.1193 | 595x slower |

Read this honestly: these libraries compute different numbers of features, so total time is not a like-for-like comparison. The tsxtractor advantage is parallelising across series in native code; on a single short series it will not look meaningfully faster than catch22.

- **tsxtractor 0.3.0** -- Rust core, rayon across series, zero-copy input
- **catch22 (pycatch22)** -- C core, single-threaded Python loop over series
