# Kymora
### High-Performance Time Series Feature Extraction Library. Rust Core. Python Ease.

[![PyPI - Version](https://img.shields.io/pypi/v/kymora.svg?color=blue)](https://pypi.org/project/kymora/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kymora.svg)](https://pypi.org/project/kymora/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/kymora)](https://pypi.org/project/kymora/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Aamodx6/Kymora/actions/workflows/ci.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/ci.yml)
[![Release](https://github.com/Aamodx6/Kymora/actions/workflows/release.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/release.yml)
[![Nightly](https://github.com/Aamodx6/Kymora/actions/workflows/nightly.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/nightly.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://aamodx6.github.io/Kymora/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.placeholder-blue)](https://zenodo.org)

> [!NOTE]
> On PyPI, the package is published and installed as [`kymora`](https://pypi.org/project/kymora/):
> ```bash
> pip install kymora
> ```

> **Batch time-series feature extraction: 33 features at 1.94 ms median per 1,000 series x 500 steps (514,245 series/s; 95.4× catch22, 1,291× TSFEL, 12,106× tsfresh), with no copy of the input and bounded O(T × L) worker scratch (~2.29–3.33 MiB at N ≤ 10k).**

**Kymora** is a high-performance **Time Series Feature Extraction Library** for Python, powered by a native Rust engine (no copy of the input) with a clean, Scikit-Learn-compatible interface—ideal for machine learning pipelines, quantitative finance, real-time sensor telemetry, and high-throughput research.

[PyPI](https://pypi.org/project/kymora/) • [Features](#key-features) • [Installation](#installation) • [Quickstart](#quickstart) • [Benchmarks](#benchmarks) • [Streaming & Real-Time Telemetry](#streaming-real-time-telemetry) • [Scikit-Learn Integration](#scikit-learn-pipeline) • [Documentation](https://aamodx6.github.io/Kymora/) • [Website](https://landing-drab-six-14.vercel.app)

---

### Why Kymora?

Traditional Python time-series feature libraries (`tsfresh`, `TSFEL`, `catch22`) force a painful trade-off: **wait minutes to hours for feature extraction, or risk Out-Of-Memory (OOM) crashes from defensive copies.** Kymora eliminates that trade-off.

* **Throughput (measured):** Pooled median **514,245 series/second** (1.94 ms; 95% bootstrap CI [495,050, 529,605] series/s, [1.89, 2.02] ms; isolated baseline 358,654 series/s / 2.79 ms) across 3 same-session interleaved rounds with inter-block cooldowns on an i7-13620H laptop, 10 cores / 16 threads under High Performance scheme — about **95.4×** `catch22` (143.1× per-feature), **1,291×** `TSFEL` (273.0× per-feature), and **12,106×** `tsfresh` (514.1× per-feature) raw time on the same machine (see Benchmarks and `CLAIMS.md`).
* **Direct Buffer Ingestion (No Input Copy):** Directly borrows contiguous NumPy buffer pointers via PyO3. No copy of the input, no DataFrame melting, and predictable worker scratch memory ($O(T \times L)$, ~2.29–3.33 MiB at $N \le 10,000$; does not scale with $N$).
* **33 Curated, High-Signal Features:** Avoids the curse of dimensionality. Features are mathematically non-redundant ($|r| < 0.70$ for 83.3% of pairs), spanning distribution moments, quantiles, crossings, spectral power, and permutation entropy.
* **Full Multi-Core Scaling (GIL-Free):** Releases Python's Global Interpreter Lock (GIL) across the entire computation region, saturating all CPU cores with Rayon's work-stealing scheduler.
* **Real-Time Streaming Ready:** Maintain rolling windows with incremental state updates using the built-in `StreamingExtractor` — amortized $O(1)$ per-sample ingestion (worst-case $O(W)$ upon drift re-anchoring) plus a fast 12-feature tier with no sorting and no FFT.

---

### Key Features

* **Direct Native Architecture:** PyO3 bindings pass 2D NumPy pointer references directly into native-Rust multi-core loops without copying a single byte.
* **Batch-First Parallelism:** Processes $N$ series in parallel across hardware threads instead of running serial Python loops.
* **Dual API Support:** Extract raw 2D NumPy matrices for maximum speed, or labeled Pandas/Polars DataFrames for immediate exploratory analysis.
* **Scikit-Learn Compatible:** Drop `KymoraTransformer` into any `sklearn.pipeline.Pipeline` or cross-validation grid search.
* **Realfft & Histogram Quantiles:** Preallocated per-worker FFT scratch and histogram multi-select quantiles ensure predictable sub-millisecond execution.
* **Streaming & Sliding Windows:** Extract rolling features over continuous data streams without reallocating buffers.

---

### Installation

#### Prebuilt Wheels (Recommended)
Precompiled binary wheels are available on [PyPI (kymora)](https://pypi.org/project/kymora/) for **Linux** (`x86_64`, `aarch64`), **macOS** (Apple Silicon `arm64`, Intel `x86_64`), and **Windows** (`x64`). No Rust compiler required!

```bash
pip install kymora
```

#### From Source (Development)
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
pip install maturin
maturin develop --release
```

---

### Quickstart

#### 1. Batch Feature Extraction (2D NumPy)
Extract 33 features from 100,000 series in under a second:

```python
import numpy as np
import kymora as km

# 1,000 series of 500 time-steps (float64)
X = np.random.randn(1000, 500)

# Extract 33 features (direct buffer borrowing, multi-threaded)
features = km.extract_features(X)

print("Output shape:", features.shape)      # (1000, 33)
print("Feature names:", km.feature_names()[:5])
# ['mean', 'std', 'var', 'min', 'max', ...]
```

#### 2. Labeled Pandas DataFrame
```python
# Returns a labeled pandas DataFrame with clean column headers
df = km.extract_features_df(X)
print(df.head())
```

#### 3. Ragged Series of Different Lengths
```python
# Sequences of varying lengths are supported natively
arr1 = np.random.randn(300)
arr2 = np.random.randn(500)
arr3 = np.random.randn(120)

features = km.extract_features([arr1, arr2, arr3])
print(features.shape)  # (3, 33)
```

#### 4. Sliding Windows over a Long Signal
```python
# Extract rolling window features from a 1D continuous sensor stream
signal = np.random.randn(100_000)
windowed_features = km.sliding_features(signal, window=256, stride=64)
```

---

### TSFEL Drop-In Migration & Domain Architecture

For teams and data scientists migrating from or configured for **TSFEL**, Kymora provides a 100% compatible drop-in replacement (`from kymora.compat import tsfel`) that delivers **up to 1,000× faster extraction** with zero code refactoring:

```python
# Simply replace: import tsfel
from kymora.compat import tsfel

# Your existing TSFEL pipeline remains 100% identical:
cfg = tsfel.get_features_by_domain("statistical")
features_df = tsfel.time_series_features_extractor(cfg, X, fs=100.0)
clean_df = tsfel.correlated_features(features_df, threshold=0.90)
```

#### Modular Package Structure (TSFEL-Standard Layout)
To ensure seamless adoption across research and industry, Kymora exposes standard modular subpackages:
* **`kymora.feature_extraction`**: Scientific domain configuration (`get_features_by_domain`), feature schema (`features.json`), and extraction engine (`time_series_features_extractor`, `calc_features`).
* **`kymora.datasets`**: Real-world benchmark dataset loaders (`load_dataset("ECG200")`, `list_datasets()`).
* **`kymora.utils`**: Collinear feature pruning (`correlated_features`).
* **`kymora.compat.tsfel`**: Drop-in replacement module.

#### Advanced Cepstral & Continuous Wavelet Transform (CWT) Features
Kymora includes vectorized, SIMD-accelerated implementations of specialized audio and biomedical features:
* **MFCC (12 coefficients)**: Mel filterbank log energies with Type-II DCT and cepstral liftering (exact bitwise match to TSFEL).
* **LPCC (12 coefficients)**: $O(p^2)$ Levinson-Durbin autoregression and cepstral recursion.
* **CWT Wavelets (37 features)**: Mexican hat (Ricker) continuous wavelet transform energy, absolute mean, variance, and entropy across 9 dyadic scales.

```python
import kymora

# Extract audio and biomedical descriptors on real signals
features = [
    "mean", "std", "root_mean_square",
    "mfcc_0", "mfcc_1", "mfcc_2",
    "lpcc_0", "lpcc_1",
    "wavelet_energy_scale_1", "wavelet_energy_scale_2", "wavelet_entropy"
]
df = kymora.extract_features_df(X, features=features, fs=100.0)
```

#### Real-World Benchmark: Kymora vs TSFEL on Canonical UCR Datasets

Tested across canonical real-world empirical time series (300 series per dataset, 16 threads, Python 3.14.6; report: [`benchmarks/results/KYMORA_VS_TSFEL_BENCHMARK_REPORT.md`](benchmarks/results/KYMORA_VS_TSFEL_BENCHMARK_REPORT.md)):

| Real Dataset | Domain / Signal | Series Length ($L$) | Kymora Latency | TSFEL Latency | Real Data Speedup | Parity Error |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **GunPoint** | Video Motion Capture | 150 | **1.57 ms** | 3,065.13 ms | **1,946.2× faster** | $< 10^{-15}$ |
| **ECG200** | Cardiology ECG Heartbeats | 96 | **0.64 ms** | 197.23 ms | **307.8× faster** | $< 10^{-15}$ |
| **ItalyPowerDemand** | Energy Grid Telemetry | 24 | **1.27 ms** | 172.56 ms | **135.9× faster** | $< 10^{-15}$ |
| **Coffee** | Food Chemistry NIR Spectra | 286 | **1.35 ms** | 200.42 ms | **147.9× faster** | $< 10^{-15}$ |
| **Wafer** | Semiconductor Etching Sensor | 152 | **1.25 ms** | 211.76 ms | **169.2× faster** | $< 10^{-15}$ |

> On real spectroscopic sensor signals (`Coffee`), Kymora extracted all features in **1.54 ms**, while TSFEL took **6,080.09 ms** (**3,948× faster**), while achieving identical 100.0% classification accuracy.

---

### Scikit-Learn Pipeline

Integrate directly into standard classification, regression, or clustering pipelines
(`pip install "kymora[sklearn]"` for the optional dependency):

```python
import numpy as np
from kymora.sklearn import KymoraTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Assemble end-to-end reproducible pipeline
pipeline = Pipeline([
    ("features", KymoraTransformer()),  # (n_series, length) -> (n_series, 33)
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(n_estimators=100))
])

# Synthetic training data (n_samples, time_steps) — replace with your series
rng = np.random.default_rng(0)
X_train = rng.standard_normal((40, 128))
y_train = (X_train.sum(axis=1) > 0).astype(int)
X_test = rng.standard_normal((10, 128))

# Fit on raw time-series training data (n_samples, time_steps)
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
```

### Streaming & Real-Time Telemetry

Maintain running statistical features in real-time embedded systems or trading loops without recomputing from scratch:

```python
import numpy as np
from kymora import StreamingExtractor

# Initialize streaming extractor with window capacity
stream = StreamingExtractor(window_size=500)
incoming_data_feed = iter(np.random.default_rng(1).standard_normal(600))

for tick in incoming_data_feed:
    stream.push(tick)
    
    # 1. Fast 12-feature tier (O(1) accumulator reads — no scan, no sorting, no FFT):
    # Returns 12 features: mean, std, var, skew, kurt, abs_energy, rms,
    # mean_abs_change, mean_change, cid_ce, zero_crossings, trend_slope.
    # Accuracy matches batch within rtol 1e-9 (see docs/streaming.md for the
    # large-offset skew/kurt conditioning note).
    fast_features = stream.compute(kind="fast")
    
    # 2. Complete 33-feature set evaluated over the current rolling window:
    all_features = stream.compute(kind="all")
```

---

### Profiles & Feature Catalog

Choose the performance-to-breadth profile that fits your pipeline:

* **`minimal` (10 features):** Centered moments, extrema, energy, zero crossings. Zero sorting and zero FFT overhead (~0.58 ms per 1,000 series; **1,716,444 series/s**, re-measured 2026-11-22).
* **`core33` (33 features - Default):** Frozen authoritative v1.0 set spanning all temporal, quantile, and spectral domains (~1.94 ms median per 1,000 series on i7-13620H / 16 threads; pooled multi-session interleaved throughput **514,245 series/s**, 95% CI [495,050, 529,605] series/s; isolated single-method baseline: 358,654 series/s / 2.79 ms; 0.0589 µs per series-feature).
* **`extended` (143 features):** Adds distribution statistics, crossings, nonlinear stats, PACF (Levinson-Durbin), full linear regression trend, and spectral aggregations.
* **`full` (543 features):** Complete high-coverage bank including all 400 FFT coefficient parameters extracted directly from the precomputed spectrum with zero redundant transforms.

```python
import kymora

# List available profiles and feature counts
print(kymora.list_profiles())
# {'minimal': 10, 'core33': 33, 'extended': 143, 'full': 543}

# Inspect individual features and their computational prerequisites
print(kymora.describe_feature("autocorr_lag_1"))
```

---

### Benchmarks

All numbers below are pooled medians from interleaved rounds with 95% bootstrap CIs, subprocess-isolated, GC disabled — from one laptop (i7-13620H, 10 cores (6P+4E) / 16 threads, Windows 11, AC online; the Windows power scheme of each run is recorded in its artifact `env.json`, and this re-baseline ran on `Silent`). **Exploratory single-machine numbers, not fleet evidence.** Claim→artifact map: [`CLAIMS.md`](CLAIMS.md). Artifacts: `benchmarks/results/EQUAL_FEATURE_REPORT.md` + `2026-11-22_equal_feature/` (equal-feature, 2026-11-22), `benchmarks/results/2026-11-22_remeasure/` (profiles / scaling / memory, 2026-11-22), `benchmarks/results/2026-11-22_reproduce_readme/` (raw-time full catalogs, 2026-11-22):

#### Equal-feature comparison — the like-for-like table (1,000 × 500)

Both sides compute **exactly the same features**: each library is restricted to the subset whose definitions match kymora's, and every feature pair is numerically verified before timing (parity gate: max rel err ≤ 1e-9; artifact `2026-11-22_equal_feature/parity.json`). 16 threads, 6 interleaved rounds per row:

| Library | Equal features | Kymora med (ms) | Library med (ms) | Ratio (95% CI) |
| :--- | :---: | :---: | :---: | :--- |
| numba baseline | 33 | 2.24 | 13.34 | **6.0× slower** [5.7, 6.5] |
| numpy baseline | 33 | 2.19 | 361.33 | **165.1× slower** [157.2, 170.5] |
| TSFEL | 13 | 1.97 | 2,145.73 | **1,089.1× slower** [1,007.3, 1,132.2] |
| tsfresh | 13 | 2.34 | 6,580.57 | **2,812.4× slower** [2,584.3, 2,914.1] |

Kymora is fastest on **all 16 equal-feature rows** measured across 4 shapes (ratios 6.0×–2,812.4×; full tables: `benchmarks/results/EQUAL_FEATURE_REPORT.md`). `catch22` has no row here by design: none of its 22 features is definition-identical to a core33 feature (mapping and near-miss analysis: [`docs/benchmarks/feature_mapping.md`](docs/benchmarks/feature_mapping.md)).

#### Profile throughput (1,000 × 500, 16 threads — re-measured 2026-11-22):
| Profile | Features | Latency (1k) | Per-Series | Per-Feature Cost | Throughput |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `minimal` | 10 | **0.58 ms** | **0.58 µs** | 0.0583 µs | **1,716,444 series/s** |
| `core33` | 33 | **1.90 ms** | **1.90 µs** | 0.0575 µs | **526,912 series/s** |
| `extended` | 143 | **8.02 ms** | **8.02 µs** | 0.0561 µs | **124,635 series/s** |
| `full` | 543 | **9.44 ms** | **9.44 µs** | 0.0174 µs | **105,982 series/s** |

Artifact: `benchmarks/results/2026-11-22_remeasure/profiles.jsonl` (medians of subprocess-isolated runs per profile).

#### Multi-core scaling (`core33`, 1,000 × 500 — re-measured 2026-11-22):
| Worker Threads | Latency | Per-Series Cost | Speedup vs 1 Thread | Scaling Efficiency |
| :---: | :---: | :---: | :---: | :---: |
| 1 Thread | 11.22 ms | 11.22 µs | 1.00× | 100.0% |
| 2 Threads | 5.83 ms | 5.83 µs | 1.92× | 96.1% |
| 4 Threads | 3.40 ms | 3.40 µs | 3.30× | 82.6% |
| 8 Threads | 2.22 ms | 2.22 µs | 5.05× | 63.1% |
| 16 Threads | 2.30 ms | 2.30 µs | 4.87× | 30.5% |
| 32 Threads | 2.09 ms | 2.09 µs | 5.37× | 16.8% |

Efficiency drops past ~4–8 threads on this hybrid P+E-core laptop (oversubscription past 10 physical cores); treat the shape of this table as hardware-bound. Artifact: `benchmarks/results/2026-11-22_remeasure/scaling.jsonl`.

#### Raw-time comparison — full default catalogs (1,000 × 500)

Each library times its **full default catalog** end to end, including the input reshaping it requires (tsfresh's long-format DataFrame, catch22/TSFEL's per-series loop):
| Library | Features | Runtime (1k × 500) | Series / sec | Speedup (raw time) |
| :--- | :---: | :---: | :---: | :--- |
| **Kymora (`core33`)** | **33** | **1.94 ms** | **514,245** | **Baseline (1.0×)** |
| `catch22` | 22 | 185.50 ms | 5,391 | **95.4× slower** |
| `TSFEL` | 156 | 2,509.53 ms | 398 | **1,291× slower** |
| `tsfresh` | 777 | 23,540.62 ms | 42 | **12,106× slower** |

Pooled medians: kymora over 3 interleaved sessions (median 1.94 ms, 95% CI [1.89, 2.02] ms; 514,245 series/s [495,050, 529,605]; isolated single-library baseline: 358,654 series/s / 2.79 ms). Competitors run multi-threaded (16 threads: native Rayon for Kymora; 16 worker processes for catch22, TSFEL, and tsfresh) in the same session rounds with inter-block cooldowns; artifacts `benchmarks/results/HEADLINE_SAME_SESSION_REPORT.md` and `benchmarks/results/headline_same_session_ratios.json`. Per-session ratios: catch22 [91.8×, 100.5×, 87.9×], TSFEL [2,036.3×, 1,325.6×, 1,256.3×], tsfresh [11,952.0×, 12,014.0×, 12,630.8×]. Different feature counts mean different work — for normalized per-feature speedups (143.1×, 273.0×, 514.1×) and detailed breakdowns, see [`docs/benchmarks.md`](docs/benchmarks.md), and prefer the equal-feature table above for a like-for-like claim.

#### Predictive utility on real-world datasets (UCR Archive)

Speed is meaningless if features fail to predict well downstream. We evaluated Kymora (`core33`, `extended`, and `full` profiles) against `catch22`, `TSFEL`, and `tsfresh` on canonical UCR univariate classification datasets (matched set $n = 42$, canonical fixed train/test splits, 16 threads across all methods, standard `RandomForestClassifier` and `RidgeClassifier` with fold-isolated imputation and scaling):

| Library | Features | Datasets | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Median Extract Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `tsfresh` | 777 | 42 | **84.79%** | **82.39%** | **2.19** | **2.43** | 20,943.62 ms |
| **Kymora (`full`)** | 543 | 42 | **82.79%** | **80.66%** | **2.83** | **3.17** | **2.17 ms** |
| **Kymora (`extended`)** | 143 | 42 | **83.12%** | **80.39%** | **2.98** | **3.19** | **1.74 ms** |
| `TSFEL` | 156 | 42 | 81.00% | 79.71% | 3.36 | 3.24 | 942.67 ms |
| **Kymora (`core33`)** | **33** | **42** | **79.96%** | **77.42%** | **4.12** | **3.83** | **1.26 ms** (ref) |
| `catch22` | 22 | 42 | 79.83% | 75.75% | 4.14 | 4.29 | 159.40 ms |

* **Predictive accuracy:** Kymora achieves catch22-class accuracy at ~100× lower cost (core33 achieves 79.96% RF / 77.42% Ridge vs catch22 79.83% RF / 75.75% Ridge; 117.2× faster median extraction). tsfresh and TSFEL are more accurate (mean RF accuracy gaps: +1.04% for TSFEL, +4.83% for tsfresh, $p < 0.05$), reflecting their larger feature catalogs (156 and 777 features vs 33), but require 100× to 10,000× longer extraction runtime.
* **Extended and Full profiles:** Kymora's `extended` (143 feats) and `full` (543 feats) profiles achieve 83.12% and 82.79% RF accuracy, outperforming TSFEL and closing the predictive gap to tsfresh, while extracting in ~1.7–2.2 ms.
* Full per-dataset accuracy breakdown, Holm-adjusted $p$-values, and Pareto frontier: [`benchmarks/results/DOWNSTREAM_UCR_REPORT.md`](benchmarks/results/DOWNSTREAM_UCR_REPORT.md).

#### Where Kymora is slower

Honest losses, with evidence (`benchmarks/results/2026-10-05_l1_rerun/l1_root_cause.json`, `benchmarks/results/L1_ROOT_CAUSE.md`, `benchmarks/results/SMALL_BATCH_REPORT.md`, `docs/internal/single_call_overhead.md`):

- **Tiny single-shot calls:** Against a hand-written Numba baseline on the same 33 features, Kymora loses at 1 × 10 (p50 5.90 µs vs Numba 3.00 µs) and 1 × 100 with standard `extract_features` (p50 7.50 µs vs Numba 14.40 µs steady-state; first-call 35.2 µs), where Numba JIT compiles inline loops. With dedicated `kymora.extract_one(x)`, single-call latency drops to **3.90 µs** (p99 6.40 µs; target <8 µs achieved by bypassing GIL release and caching thread-local scratchpads). We keep the Numba 1×10 loss in the ledger honestly.
- **Small-batch threshold:** Inline sequential caller execution below 8,000 points (`SERIAL_WORK_SIZE_THRESHOLD = 8000`, configurable via `KYMORA_SERIAL_THRESHOLD`) matches 1T and 16T execution and avoids Rayon thread wake jitter.
- **Batch inflection:** At 10 × 500, Kymora wins 2.4× (103.5 µs vs 247.3 µs); at 100 × 100, Kymora wins 2.4× (156.8 µs vs 375.3 µs); at 100 × 500, Kymora wins 3.0× (396.5 µs vs 1,195.2 µs); at ≥1,000 series, Kymora is 6.0×–11.8× faster than the Numba baseline on identical features (equal-feature table above).

#### Memory footprint (re-measured on HEAD sweep $N = 1\text{k}..100\text{k}$, fresh-process peak RSS):
* **Worker scratch is $O(T \times L)$ and does not scale with $N$:** Peak worker scratch across 16 Rayon worker threads is bounded at 2.29–3.33 MiB at $N \le 10,000$ (0.20–2.52 MiB for 4 threads) and reaches a 25.38 MiB RSS high-water mark at $N=100,000$ due to OS physical page commit of large output arrays.
* **No defensive copies:** At $100,000 \times 500$, total process peak RSS delta is 406.86 MiB (input array 381.47 MiB + preallocated output matrix 25.18 MiB = 406.65 MiB, representing 99.95% of memory).
* **tsfresh comparison:** tsfresh extraction overhead reaches **+293.2 MiB** at 1,000 × 500 and **+410.3 MiB** at 10,000 × 500 (totals 300.9 / 452.2 MiB) due to long-format DataFrame conversions.

Artifact: `benchmarks/results/MEMORY_SWEEP_REPORT.md` (`memory_sweep_results.json`).


---

### The 33 Curated Features

Kymora deliberately computes 33 high-signal, non-redundant features spanning all temporal domains (exact catalog: `kymora.feature_names()`):
* **Moments:** mean, std, var, skewness, kurtosis.
* **Extrema & quantiles:** min, max, median, quantile_10, quantile_25, quantile_75, quantile_90.
* **Energy & shape:** abs_energy, root_mean_square, number_of_peaks.
* **Differences & trend:** mean_abs_change, mean_change, cid_ce, mean_second_derivative_central, trend_slope, trend_r2.
* **Crossings & runs:** zero_crossings, mean_crossings, longest_strike_above_mean, longest_strike_below_mean.
* **Autocorrelation:** autocorr_lag_1, autocorr_lag_2, autocorr_lag_5, autocorr_lag_10.
* **Spectral:** dominant_frequency, spectral_centroid, spectral_entropy.
* **Complexity:** permutation_entropy (order 3, delay 1).

---

### Contributing

Contributions, bug reports, and PRs are welcome!
Please check [`CONTRIBUTING.md`](https://github.com/Aamodx6/Kymora/blob/main/CONTRIBUTING.md) for details on setting up the local Rust/Python development environment and running the benchmark suites.

---

### License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/Aamodx6/Kymora/blob/main/LICENSE) for details.

*Built with Rust and Python by [Aamod](https://github.com/Aamod007).*
