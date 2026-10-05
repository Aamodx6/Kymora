# Performance guide

How to get the most out of kymora, and when not to bother. Numbers below
are exploratory single-machine results (i7-13620H, Windows 11); re-run the
suites on your hardware before quoting anything. Claim→artifact map:
[CLAIMS.md](https://github.com/Aamodx6/Kymora/blob/main/CLAIMS.md).

## Thread tuning

- Leave `n_jobs=None` (shared global pool, all threads) unless you need
  oversubscription control. An explicit `n_jobs` uses a cached per-count
  pool, so it costs nothing extra either.
- Scaling stops near the physical core count — ~6 threads on a 6P+4E
  hybrid laptop (peak 4.37× at 12 threads), near core count on servers.
  See `docs/internal/thread_scaling.md` for the analysis.
- One series has nothing to spread: single-series calls are latency-bound
  (~70 µs fixed floor + ~10 µs/series compute at n=500). Batch many series
  into one call, or use `StreamingExtractor` for one-at-a-time ingest.

## Memory layout

- Inputs are borrowed, never copied: pass C-contiguous arrays. Strided or
  Fortran input raises unless `contiguous="copy"` (one explicit copy).
- Outputs are the only allocation: core33 on 100k×500 is ~26 MB float64.
  Reuse a preallocated `out=` buffer across calls for zero steady-state
  allocation, or `out_dtype="float32"` to halve output memory.
- `extended` (~150 features) and `full` (777) multiply output width; for
  outputs beyond RAM, extract in row chunks (the API is row-parallel, so
  chunking is exact).

## Which profile when

| Profile | Features | Use when |
|---|---|---|
| `minimal` (10) | moments, extrema, energy, crossings | Sorting/FFT-free screening; fastest (~1.2 ms per 1k×500) |
| `core33` (33, default) | full temporal + quantile + spectral set | General classification/regression features |
| `extended` (~143) | + distribution, PACF, trend, spectral agg | You need the wider bank and pay ~3.5× core33 |
| `full` (543+) | + all FFT coefficient parameters | Exhaustive search; ~4× core33, wide output |

`features=[...]` with a moment-heavy subset skips SELECT/SORTED/SPECTRUM
intermediates entirely — cheaper than any profile containing them.

## Streaming costs

`push` ≈ 0.2 µs and `compute(kind="fast")` ≈ 0.4–0.7 µs, flat across
window sizes 64…65536; `compute(kind="all")` grows linearly with W.
Artifact: `benchmarks/results/2026-10-05_streaming/`. See the
[streaming guide](streaming.md) for the complexity contract.

## When not to use kymora

- A handful of series: fixed per-call overhead dominates; numpy/numba wins.
- Features outside the shipped profiles, or custom Python features on the
  hot path (use the batch API around them instead).
- Heavy O(n²)+ estimators (sample entropy, CWT, DFA): not shipped;
  tsfresh/antropy cover those (slower, but they exist).
