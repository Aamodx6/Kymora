# Thread scaling analysis (Phase 5.1)

Machine: i7-13620H laptop, 10 cores (6P+4E) / 16 threads, Windows 11,
Performance plan, AC online. Workload: core33, 1,000 series × 500, f64
C-contiguous gaussian, 21-run medians. Exploratory single-machine numbers.

## Measured scaling (2026-10-06, HEAD with pool cache)

| n_jobs | median (ms) | speedup vs 1T | efficiency vs 6P |
|---|---|---|---|
| 1 | 12.16 | 1.00× | — |
| 2 | 6.47 | 1.88× | — |
| 4 | 3.76 | 3.23× | — |
| 6 | 3.02 | 4.03× | 67% |
| 8 | 2.89 | 4.21× | 70% |
| 10 | 2.95 | 4.12× | — |
| 12 | 2.78 | 4.37× | — |
| 16 | 2.80 | 4.34× | — |

Consistent with the 2026-10-05 remeasure artifact (peak 4.25× @ 16T).

## Reading

Gains stop at ~6 threads = the P-core count. The 4 E-cores and SMT add
~5% at best. Amdahl fits give inconsistent serial fractions (10% at 6T,
18% at 16T), so this is not a fixed serial bottleneck: per-thread work is
FFT/selection-heavy with per-worker scratch, and beyond the P-cores the
extra threads are slower (E-cores) or share execution resources (SMT)
while adding pool-dispatch and memory-bandwidth pressure. No code change
can make E-cores fast; topology-aware scheduling (P-core preference) is
not available through rayon. Conclusion: the plateau is hardware
topography, not a software bug worth chasing (stop rule, arch §9.4).

## Fix implemented: cached thread pools

`run_in_pool` built a fresh rayon `ThreadPool` on *every* call with
`n_jobs` set (~200 µs measured on a 32×500 batch, dominating small calls
— arch F2). Pools are now cached per thread count (process-wide
`OnceLock<HashMap>`; build failure still falls back to inline execution).

| Shape | n_jobs=8 before | n_jobs=8 after | n_jobs=None |
|---|---|---|---|
| 32×500 | 556 µs | 242 µs | ~250 µs |
| 1000×500 | ~3.0 ms | ~2.8 ms | ~2.2–2.5 ms (noisy) |

Small-call win is 2.3× and far above machine noise; the 1k shape is
within run-to-run spread (no regression). Numeric results are untouched
(scheduling only); `test_results_bitwise_identical_across_thread_counts`
locks arch I7.

## Recommendation (see 5.2)

Leave the default (`n_jobs=None`, global pool, all threads): capping at
6 would trade ~5% peak throughput for complexity and platform-specific
behavior. Pass an explicit `n_jobs` for oversubscription control (now
free); expect scaling to stop near the physical P-core count on hybrid
laptops and near the core count on servers.
