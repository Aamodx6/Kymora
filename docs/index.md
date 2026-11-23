# kymora

High-performance time-series feature extraction for Python, powered by a native Rust engine.

Extract curated statistical, temporal, spectral, multichannel, and multi-view features across large batches of time series. The Rust core operates directly on contiguous NumPy buffers (no copy of the input), releases the GIL, and parallelizes across series with Rayon; per-series work runs through fused single-traversal passes over lazily computed shared intermediates.

```bash
pip install kymora
```

```python
import numpy as np
import kymora

# Batch extraction over 100,000 series
X = np.random.randn(100_000, 500)
feats = kymora.extract_features(X)       # (100_000, 33) float64
df = kymora.extract_features_df(X)       # pandas DataFrame with labeled columns
```

---

## Architectural Highlights

- **Fused passes & shared intermediates**: moments, differences, crossings, peaks, autocorrelations, trend, ordinal patterns, and FFT each accumulate in as few traversals as possible; intermediates shared between features are computed at most once per series, and unrequested features cost nothing.
- **Rayon parallelism with serial fallback**: series are spread across worker threads (GIL released for the whole parallel region); batches below `SERIAL_THRESHOLD` (8 series) run serially to avoid pool wake-up overhead on small calls.
- **$O(n)$ multi-select quantiles**: histogram/selection multi-quantile evaluation avoids full sorting overhead on the core33 and minimal profiles.
- **Multi-View Transform Engine**: Multiply feature coverage across 8 mathematical domain views (`raw`, `diff`, `diff2`, `detrend`, `znorm`, `abs`, `logret`, `rank`) with automatic invariance pruning.
- **Multichannel & Cross-Channel Dynamics**: Full support for 3D time-series batches `(samples, channels, length)`, evaluating per-channel baselines and pairwise cross-correlation / covariance interactions.
- **Fleet Real-Time Streaming**: `StreamingExtractor` monitors live time-series streams with incremental rolling-window updates; per-sample ingestion is amortized $O(1)$ (worst-case $O(W)$ upon drift re-anchoring), and a fast 12-feature tier avoids sorting and FFT.
- **Supervised Feature Selection**: `select_features` and `KymoraSelector` provide FDR-controlled hypothesis testing and correlation clustering directly within scikit-learn pipelines.
- **TSFEL Drop-In Compatibility**: `from kymora.compat import tsfel` allows any existing TSFEL pipeline to execute up to 1,000× faster with zero code changes.
- **Domain-Driven Feature Extraction**: Standard modular subpackages (`kymora.feature_extraction`, `kymora.datasets`, `kymora.utils`, `kymora.compat`) supporting domain-specific extraction (`statistical`, `temporal`, `spectral`, `fractal`).
- **Acoustic & Biomedical Wavelets**: High-performance vectorized Mel-frequency cepstral coefficients (MFCC), Linear prediction cepstral coefficients (LPCC), and Continuous Wavelet Transforms (CWT) across dyadic scales.

---

## Benchmarks Overview

All numbers below are pooled medians from interleaved rounds with 95% bootstrap CIs, subprocess-isolated, GC disabled — measured on an Intel Core i7-13620H (10 cores, 6P+4E, 16 threads, High Performance power scheme). For complete methodology, reproduction scripts, and artifact SHAs, see [Benchmarks](benchmarks.md) and [`CLAIMS.md`](https://github.com/Aamodx6/Kymora/blob/main/CLAIMS.md).

### Canonical Real-World Empirical Benchmarks (UCR Archive)

Tested across canonical real-world empirical time series datasets (300 series per dataset, 16 threads, Python 3.14.6; artifact: [`benchmarks/results/KYMORA_VS_TSFEL_BENCHMARK_REPORT.md`](https://github.com/Aamodx6/Kymora/blob/main/benchmarks/results/KYMORA_VS_TSFEL_BENCHMARK_REPORT.md)):

| Real Dataset | Domain / Signal | Series Length ($L$) | Kymora Latency | TSFEL Latency | Real Data Speedup | Numerical Parity Error |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **GunPoint** | Video Motion Capture | 150 | **1.57 ms** | 3,065.13 ms | **1,946.2× faster** | $< 8.59 \times 10^{-13}$ (Pass) |
| **ECG200** | Cardiology ECG Heartbeats | 96 | **0.64 ms** | 197.23 ms | **307.8× faster** | $< 8.59 \times 10^{-13}$ (Pass) |
| **ItalyPowerDemand** | Energy Grid Telemetry | 24 | **1.27 ms** | 172.56 ms | **135.9× faster** | $< 8.59 \times 10^{-13}$ (Pass) |
| **Coffee** | Food Chemistry NIR Spectra | 286 | **1.35 ms** | 200.42 ms | **147.9× faster** | $< 8.59 \times 10^{-13}$ (Pass) |
| **Wafer** | Semiconductor Sensor | 152 | **1.25 ms** | 211.76 ms | **169.2× faster** | $< 8.59 \times 10^{-13}$ (Pass) |

* On full spectroscopic sensor signals (`Coffee`), Kymora extracted all features in **1.54 ms**, while TSFEL required **6,080.09 ms** (**3,948× faster**), achieving identical 100.0% classification accuracy.

### Equal-feature comparison — like-for-like (1,000 × 500)

Both sides compute **exactly the same features**: each competitor is restricted to the subset whose mathematical definitions match Kymora's, and every feature pair is numerically verified before timing (parity gate: max rel err $\le 10^{-9}$; artifact `2026-11-22_equal_feature/parity.json`). 16 threads, 6 interleaved rounds per row:

| Library | Equal features | Kymora med (ms) | Library med (ms) | Ratio (95% CI) |
| :--- | :---: | :---: | :---: | :--- |
| numba baseline | 33 | 2.24 | 13.34 | **6.0× slower** [5.7, 6.5] |
| numpy baseline | 33 | 2.19 | 361.33 | **165.1× slower** [157.2, 170.5] |
| TSFEL | 13 | 1.97 | 2,145.73 | **1,089.1× slower** [1,007.3, 1,132.2] |
| tsfresh | 13 | 2.34 | 6,580.57 | **2,812.4× slower** [2,584.3, 2,914.1] |

Kymora is fastest on **all 16 equal-feature rows** measured across 4 shapes (ratios 6.0×–2,812.4×). `catch22` has no row here by design: none of its 22 features is definition-identical to a core33 feature (see [Feature mapping](benchmarks/feature_mapping.md)).

### Raw-time comparison — full default catalogs (1,000 × 500)

| Library | Features | Runtime (1k × 500) | Series / sec | Speedup (raw time) |
| :--- | :---: | :---: | :---: | :--- |
| **Kymora (`core33`)** | **33** | **1.94 ms** | **514,245** | **Baseline (1.0×)** |
| `catch22` | 22 | 185.50 ms | 5,391 | **95.4× slower** |
| `TSFEL` | 156 | 2,509.53 ms | 398 | **1,291× slower** |
| `tsfresh` | 777 | 23,540.62 ms | 42 | **12,106× slower** |

For detailed breakdowns, multi-core scaling, memory footprint sweeps, and UCR predictive accuracy benchmarks, see [Benchmarks](benchmarks.md).

---

## Guarantees

| Surface | Guarantee |
|---|---|
| `feature_names()` order and length | Frozen across all minor releases within a major version |
| Output dtype | `float64` default (with fast `float32` pipeline support) |
| [NaN policy](nan-policy.md) | Exact and tested NaN propagation semantics |
| Panic safety | Rust panics are intercepted and translated into Python exceptions |

Numerical parity is validated feature by feature against NumPy and SciPy references.

---

## Where the speed comes from

Three compounding effects, in order of contribution:

1. **Parallelism across series.** The dominant term. Each series is independent, so throughput scales with core count while the GIL is released. (Conversely, a single series shows no *parallel* advantage — there is nothing to spread.)
2. **Fused per-series passes.** Feature groups share traversals and shared intermediates are computed at most once per series, so catalog breadth does not multiply cost.
3. **Direct buffer borrowing (no copy of the input).** Inputs are borrowed views of the caller's NumPy memory and the output array is allocated once and written in place — no defensive copies, no per-series allocation in the hot path.

What does *not* contribute (despite older wording that suggested otherwise): explicit SIMD intrinsics (there are none — only compiler auto-vectorization) and a custom spin-pool scheduler (the prototype lives on `experiment/spin-pool`, measured at ±1% — see `docs/internal/experiments.md`; scheduling is Rayon).

---

## When NOT to use Kymora

Engineering honesty is essential: Kymora is not the right tool for every workload.

- **Single-series tiny workloads ($N=1, L \le 10$):** Fixed C-API call overhead (~1.5–3 µs) means inlined Numba loops run faster for single short series. Use Numba for single-series scalar processing.
- **Massive exploratory feature searches (500+ features):** If your workflow requires computing hundreds of parameterized feature variations without prior domain knowledge, use `tsfresh`.
- **Non-CPU execution:** Kymora is engineered strictly for multi-core CPUs; GPU and distributed backends are out of scope.
- **Micro streaming windows ($W < 4$):** Higher-order moments are degenerate for windows smaller than 4 points.
- **Non-float or strided input:** Only contiguous `float64`/`float32` is accepted — anything else raises instead of copying silently (or pass `contiguous="copy"` for one explicit copy).

For an in-depth breakdown with measured latency profiles and recommendations, see [When NOT to Use Kymora](when-not-to-use.md).
