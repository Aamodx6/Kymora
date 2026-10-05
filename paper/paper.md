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
date: 06 October 2026
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

`Kymora` is a batch-oriented feature extractor with a Rust core (PyO3) that
takes zero-copy views of NumPy buffers, releases the GIL, and parallelizes
across the series dimension with Rayon. It ships 33 curated statistical,
temporal, and spectral features (frozen column order), wider `extended` and
`full` profiles, an O(1)-amortized streaming engine for rolling windows, a
scikit-learn transformer, and a documented NaN contract. Every performance
figure in this paper traces to a committed artifact via `CLAIMS.md`.

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
FFT with a shared power spectrum, and fused lag/autocorrelation,
difference, threshold, and ordinal-pattern traversals. Intermediates are
computed at most once per series; unrequested features cost nothing.
`StreamingExtractor` maintains anchored shifted power sums with a drift
guard (exact re-anchor past 0.25σ drift), giving O(1)-amortized pushes and
O(1) fast-tier reads verified against batch output within rtol 1e-9.
Inputs are borrowed, never copied (non-contiguous layouts raise unless the
caller opts into one explicit copy); `KymoraError` covers structure while
NaN follows a tested propagation contract.

# Performance

Method: fresh subprocess per measurement, warmup, GC disabled, interleaved
rounds, pooled medians with 95% bootstrap CIs. Machine: i7-13620H laptop
(10 cores/16 threads), Windows 11, 1,000 series × 500 steps, 16 threads —
exploratory single-machine numbers, not fleet evidence.

Like-for-like (each library restricted to definition-matched features,
parity-gated at ≤1e-9 before timing):

| Library | Equal features | Kymora (ms) | Library (ms) | Ratio |
|---|---:|---:|---:|---|
| numba baseline | 33 | 4.72 | 16.05 | 3.4× |
| numpy baseline | 33 | 4.68 | 285.50 | 61.0× |
| TSFEL | 13 | 3.92 | 2,213.69 | 564.6× |
| tsfresh | 13 | 4.94 | 8,359.45 | 1,693.8× |

As-is configs (33 vs up to 777 features): kymora 3.18 ms (314,450
series/s, 0.0964 µs/series-feature) vs catch22 833.1 ms, TSFEL 2,541.6 ms,
tsfresh 20,891.2 ms. The raw ratio compares different amounts of work;
per-feature ratios are 393×/169×/279× respectively.

Downstream utility (`benchmarks/results/downstream_report.md`): on four
synthetic classification tasks, RandomForest over the 33 features reaches
96.5–100.0% accuracy, matching catch22 at a fraction of the extraction
time. Feature redundancy (`docs/redundancy_report.md`): mean pairwise
|r| 0.37 across dynamical archetypes.

# Limitations

- All timings are single-machine and exploratory until multi-platform CI
  artifacts land; laptop thermals and hybrid P/E cores add run-to-run
  spread, and thread scaling plateaus near the physical core count.
- `Kymora` loses small-batch throughput cases to a hand-tuned numba
  baseline (up to ~40× at 1×100 series: fixed ~70 µs dispatch floor
  dominates), documented per case in the README.
- Skewness/kurtosis on large-offset series (e.g. 1e9 + noise) are
  conditioning-limited in any implementation; the streaming contract bounds
  them absolutely rather than relatively.
- Float32 input covers core33/minimal/subsets only; `extended`/`full` and
  views need float64. Heavy O(n²)+ estimators are not shipped.

# Acknowledgments

Built on PyO3, NumPy, Rayon, realfft, scikit-learn, and the sktime
ecosystem it integrates with. Benchmark competitors: tsfresh, TSFEL,
pycatch22, sktime, antropy, and the authors' numpy/numba baselines.

# References
