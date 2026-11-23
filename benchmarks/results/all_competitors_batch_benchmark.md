# Batch-throughput benchmark

100 series x 200 steps, 16 worker threads, Windows-11-10.0.26300-SP0, Python 3.14.6.

Time is reported as Median ± IQR across repeated runs, including input reshaping.

| library | features | median time | IQR | mean time | series/s | ms/feature | vs kymora |
|---|---:|---:|---:|---:|---:|---:|---:|
| kymora 0.8.2 | 33 | 0.30 ms | 0.05 ms | 0.29 ms | 333,890 | 0.0091 | baseline |
| catch22 (pycatch22) | 22 | 34.41 ms | 1.03 ms | 35.01 ms | 2,906 | 1.5641 | 115x slower |
| antropy (complexity/entropy) | 8 | 111.50 ms | 0.55 ms | 111.50 ms | 897 | 13.9369 | 372x slower |
| sktime (Catch22 transformer) | 22 | 233.80 ms | 4.19 ms | 233.80 ms | 428 | 10.6272 | 781x slower |
| numba (parallel JIT baseline) | 10 | 0.04 ms | 0.01 ms | 0.04 ms | 2,844,950 | 0.0035 | 0x slower |
| numpy (vectorized baseline) | 12 | 0.45 ms | 0.03 ms | 0.45 ms | 223,489 | 0.0373 | 1x slower |
| TSFEL (all domains) | 156 | 815.00 ms | 5.66 ms | 815.00 ms | 123 | 5.2243 | 2,721x slower |
| tsfresh (EfficientFCParameters) | 777 | 6.37 s | 0.00 s | 6.37 s | 16 | 8.1928 | 21,255x slower |

Read this honestly: these libraries compute different numbers of features, so total time is not a like-for-like comparison. The kymora advantage is parallelising across series in native code; on a single short series it will not look meaningfully faster than catch22.

- **kymora 0.8.2** -- Rust core, rayon across series, zero-copy input
- **catch22 (pycatch22)** -- C core, single-threaded Python loop over series
- **antropy (complexity/entropy)** -- Python/Numba, single-threaded loop for entropy/fractal dimensions
- **sktime (Catch22 transformer)** -- sktime panel wrapper over catch22
- **numba (parallel JIT baseline)** -- Numba @njit(parallel=True, fastmath=True) 10 features
- **numpy (vectorized baseline)** -- Pure vectorized NumPy 12 basic features
- **TSFEL (all domains)** -- Python/numba, per-series extractor calls
- **tsfresh (EfficientFCParameters)** -- includes the long-format reshape, its required input form
