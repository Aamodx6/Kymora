---
title: 'Kymora: High-Throughput Batch and Streaming Time-Series Feature Extraction with a Rust Core'
tags:
  - Python
  - Rust
  - time-series
  - feature-extraction
  - machine-learning
  - signal-processing
authors:
  - name: Aamod Kumar
    affiliation: 1
affiliations:
  - name: Independent Researcher, India
    index: 1
date: 22 November 2026
bibliography: paper.bib
---

# Summary

Time-series feature extraction is a foundational step in machine learning
workflows spanning industrial IoT, biosignal analysis, and quantitative
finance. Established Python toolkits — `tsfresh` [@christ2018tsfresh],
`catch22` [@lubba2019catch22], `TSFEL` [@barandas2020tsfel] — compute rich
feature banks but become the pipeline bottleneck on large batches: a
thousand series can cost minutes, mostly in per-series Python dispatch and
repeated data reshaping.

`Kymora` is a batch-oriented feature extractor with a Rust core (`PyO3` [@pyo3]) that
borrows contiguous NumPy buffers directly (no copy of the input), releases the GIL,
and parallelizes across the series dimension with Rayon [@rayon]. It ships 33 curated
statistical, temporal, and spectral features (frozen column order), wider `extended`
and `full` profiles, a streaming engine for rolling windows with amortized O(1)
per-sample updates (worst-case O(W) during periodic drift re-anchoring), a
scikit-learn [@pedregosa2011scikit] transformer, and a documented NaN contract.
Every performance figure in this paper traces to a committed artifact via `CLAIMS.md`.

# Statement of Need

Practitioners choosing a feature library face three coupled costs:
redundant thousand-column banks that slow downstream models, serial
per-series FFI dispatch, and full recomputation for every sliding window.
`Kymora` addresses the throughput side: one FFI crossing per batch, fused
per-series traversals with shared intermediates, and anchored incremental
accumulators for streams. It does not aim to replace `tsfresh` for
exploratory screening or `catch22` where those exact estimators are needed —
the honest comparison tables below include the cases where `Kymora` loses.

# State of the Field

`tsfresh` [@christ2018tsfresh] offers the widest bank (777 features in its
efficient config) with hypothesis-test-based selection; `TSFEL`
[@barandas2020tsfel] covers statistical, temporal, and spectral domains
(156 features); `catch22` [@lubba2019catch22] distills 22 canonical
characteristics implemented in C but dispatched per series from Python;
`sktime` provides pipeline transformers around several of these. `Kymora`
occupies the batch-throughput niche: a small curated bank computed with
minimal memory traffic, plus streaming and selection tooling around it.

# Software Design

The Rust core (`src/`) owns all numerics; Python (`python/kymora/`) is a
pass-through. Per series: one fused pass for sums/extrema/NaN checks, one
centered pass for moments 2–4, shared selection-based quantiles, one real
FFT [@frigo2005design] with a shared power spectrum, and fused lag/autocorrelation,
difference, threshold, and ordinal-pattern traversals [@bandt2002permutation; @batista2014cid]. Intermediates are
computed at most once per series; unrequested features cost nothing.
`StreamingExtractor` maintains anchored shifted power sums with a drift
guard (exact re-anchor past 0.25σ drift), giving amortized O(1) pushes
(worst-case O(W) during periodic drift re-anchoring) and O(1) fast-tier reads
verified against batch output within rtol 1e-9. Inputs are borrowed directly,
never copied (non-contiguous layouts raise unless the caller opts into one
explicit copy); `KymoraError` covers structure while NaN follows a tested
propagation contract.

# Performance

Method: fresh subprocess per measurement, warmup, GC disabled, interleaved
rounds, pooled medians with 95% bootstrap CIs. Machine: i7-13620H laptop
(10 cores (6P+4E) / 16 threads), Windows 11, High Performance plan, AC online,
1,000 series × 500 steps, 16 threads — exploratory single-machine numbers, not fleet evidence.

Like-for-like (each library restricted to definition-matched features,
parity-gated at ≤1e-9 before timing):

| Library | Equal features | Kymora (ms) | Library (ms) | Ratio |
|---|---:|---:|---:|---|
| numba baseline | 33 | 2.24 | 13.34 | 6.0× |
| numpy baseline | 33 | 2.19 | 361.33 | 165.1× |
| TSFEL | 13 | 1.97 | 2,145.73 | 1,089.1× |
| tsfresh | 13 | 2.34 | 6,580.57 | 2,812.4× |

As-is configs (33 vs up to 777 features): kymora pooled median 1.94 ms (514,245
series/s, 0.0589 µs/series-feature; isolated baseline 358,654 series/s) vs catch22 185.50 ms, TSFEL 2,509.53 ms,
tsfresh 23,540.62 ms. The raw ratio compares different amounts of work (95.4×, 1,291×, 12,106×);
per-feature ratios are 143.1×, 273.0×, 514.1× respectively.

Downstream utility on 42 canonical univariate UCR datasets [@dau2019ucr]
(`benchmarks/results/DOWNSTREAM_UCR_REPORT.md`): Kymora core33 achieves
catch22-class accuracy (79.96% vs 79.83% RandomForest accuracy; Holm-adjusted
p = 0.5554) at ~100× lower extraction cost (1.26 ms vs 159.40 ms median, 117.2× speedup).
tsfresh (84.79%) and TSFEL (81.00%) achieve higher accuracy from their wider feature banks,
requiring 20,943.62 ms (17,217.0×) and 942.67 ms (768.2×) extraction time. Extended and full
Kymora profiles reach 83.12% and 82.79% accuracy within 1.74 ms and 2.17 ms.

# Limitations

- All timings are single-machine and exploratory until multi-platform CI
  artifacts land; laptop thermals and hybrid P/E cores add run-to-run
  spread, and thread scaling plateaus near the physical core count (16T is
  2.30 ms vs 8T at 2.22 ms).
- On single-series micro-workloads (1×10 points), hand-tuned Numba is ~2.0× faster
  (3.00 µs vs 5.90 µs; documented in the loss ledger). For batches ≥10×500 or
  ≥100×100, Kymora's fast-path sequential and parallel execution is 2.4×–3.0× faster.
- Skewness/kurtosis on large-offset series (e.g. 1e9 + noise) are
  conditioning-limited in any implementation; the streaming contract bounds
  drift absolutely rather than relatively.
- Float32 input covers core33/minimal/subsets only; `extended`/`full` and
  views need float64. Heavy O(n²)+ estimators are not shipped.

# Acknowledgments

Built on PyO3 [@pyo3], NumPy, Rayon [@rayon], realfft, scikit-learn [@pedregosa2011scikit], and the sktime
ecosystem it integrates with. Benchmark competitors: tsfresh [@christ2018tsfresh], TSFEL [@barandas2020tsfel],
pycatch22 [@lubba2019catch22], and the authors' numpy/numba baselines.

# References
