# Kymora
### High-Performance Time-Series Feature Extraction. Rust Core. Python Ease.

[![PyPI - Version](https://img.shields.io/pypi/v/kymora.svg?color=blue)](https://pypi.org/project/kymora/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kymora.svg)](https://pypi.org/project/kymora/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Aamodx6/Kymora/actions/workflows/ci.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/ci.yml)

> **Batch time-series feature extraction: 33 features at 3.18 ms median per 1,000 series x 500 steps, with zero defensive memory copies.**

**Kymora** is a minimalistic, dependency-light time-series feature extraction library designed to make extracting statistical, temporal, and spectral features across large datasets fast and memory-efficient. It combines a zero-copy Rust engine with a clean, Scikit-Learn-compatible Python interface—ideal for machine learning pipelines, quantitative finance, real-time sensor telemetry, and high-throughput research.

[PyPI](https://pypi.org/project/kymora/) • [Features](#key-features) • [Installation](#installation) • [Quickstart](#quickstart) • [Benchmarks](#benchmarks) • [Streaming & Real-Time Telemetry](#streaming-real-time-telemetry) • [Scikit-Learn Integration](#scikit-learn-pipeline) • [Documentation](https://landing-drab-six-14.vercel.app)

---

### Why Kymora?

Traditional Python time-series feature libraries (`tsfresh`, `TSFEL`, `catch22`) force a painful trade-off: **wait minutes to hours for feature extraction, or risk Out-Of-Memory (OOM) crashes from defensive copies.** Kymora eliminates that trade-off.

* **Throughput (measured):** Best run **436,719 series/second** (median 314,450) on an i7-13620H laptop, 10 cores / 16 threads — about **262×** `catch22` and **6,570×** `tsfresh` raw time on the same machine (per-feature: 393× and 279× — see Benchmarks and `CLAIMS.md`).
* **Zero-Copy Ingestion:** Directly borrows contiguous NumPy buffer pointers via PyO3. No data duplication, no DataFrame melting, and zero intermediate memory ballooning.
* **33 Curated, High-Signal Features:** Avoids the curse of dimensionality. Features are mathematically non-redundant ($|r| < 0.70$ for 83.3% of pairs), spanning distribution moments, quantiles, crossings, spectral power, and permutation entropy.
* **Full Multi-Core Scaling (GIL-Free):** Releases Python's Global Interpreter Lock (GIL) across the entire computation region, saturating all CPU cores with Rayon's work-stealing scheduler.
* **Real-Time Streaming Ready:** Maintain rolling windows with incremental state updates using the built-in `StreamingExtractor` — amortized $O(1)$ per-sample ingestion plus a fast 12-feature tier with no sorting and no FFT.

---

### Key Features

* **Zero-Copy Hybrid Architecture:** PyO3 bindings pass 2D NumPy pointer references directly into native-Rust multi-core loops without copying a single byte.
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

> **Name note:** the bare PyPI name `tsxtract` is an unrelated JAX project —
> always `pip install kymora`, never the bare name.

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

# Extract 33 features (zero-copy, multi-threaded)
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

### Scikit-Learn Pipeline

Integrate directly into standard classification, regression, or clustering pipelines:

```python
import numpy as np
import kymora as km
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class KymoraTransformer(BaseEstimator, TransformerMixin):
    """Extract 33 Kymora features per input row (one series per row)."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_contig = np.ascontiguousarray(X, dtype=np.float64)
        return km.extract_features(X_contig)

# Assemble end-to-end reproducible pipeline
pipeline = Pipeline([
    ("features", KymoraTransformer()),
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
    
    # 1. Fast 12-feature tier (no sorting, no FFT — two linear passes over the window):
    # Returns 12 features: mean, std, var, skew, kurt, abs_energy, rms,
    # mean_abs_change, mean_change, cid_ce, zero_crossings, trend_slope
    fast_features = stream.compute(kind="fast")
    
    # 2. Complete 33-feature set evaluated over the current rolling window:
    all_features = stream.compute(kind="all")
```

---

### Profiles & Feature Catalog

Choose the performance-to-breadth profile that fits your pipeline:

* **`minimal` (10 features):** Centered moments, extrema, energy, zero crossings. Zero sorting and zero FFT overhead (~0.51 ms per 1,000 series; **~2,000,000 series/sec**).
* **`core33` (33 features - Default):** Frozen authoritative v1.0 set spanning all temporal, quantile, and spectral domains (~3.18 ms median per 1,000 series on i7-13620H / 16 threads; **314,450 series/sec**, best 436,719; 0.0964 µs per series-feature).
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

Re-measured 2026-10-04 across **1,000 series of 500 steps** (500,000 data points total) — i7-13620H laptop, 10 cores (6P+4E) / 16 threads, Performance plan, AC online, interleaved pre-refactor vs HEAD (see `benchmarks/results/F1_REPORT.md`). Exploratory single-machine numbers, not fleet evidence. The `core33` and competitor rows below are from that run; all other rows predate it (†) and are pending re-baseline (tracked in `CLAIMS.md`):

#### Profile Throughput (1,000 × 500):
| Profile | Features | Latency (1k) | Per-Series | Per-Feature Cost | Throughput |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `minimal`† | 10 | **0.51 ms** | **0.51 µs** | 0.0507 µs | **1,972,776 series/s** |
| `core33` | 33 | **3.18 ms** | **3.18 µs** | 0.0964 µs | **314,450 series/s** |
| `extended`† | 143 | **7.12 ms** | **7.12 µs** | 0.0498 µs | **140,395 series/s** |
| `full`† | 543 | **8.36 ms** | **8.36 µs** | 0.0154 µs | **119,654 series/s** |

† predates the 2026-10-04 re-baseline; pending re-measurement.

#### Multi-Core Scaling (`core33`, 1,000 × 500) †:
| Worker Threads | Latency | Per-Series Cost | Speedup vs 1 Thread | Scaling Efficiency |
| :---: | :---: | :---: | :---: | :---: |
| 1 Thread | 11.31 ms | 11.31 µs | 1.00× | 100.0% |
| 2 Threads | 6.03 ms | 6.03 µs | 1.88× | 93.8% |
| 4 Threads | 3.58 ms | 3.58 µs | 3.16× | 78.9% |
| 8 Threads | 2.52 ms | 2.52 µs | 4.49× | 56.1% |
| 16 Threads | 2.60 ms | 2.60 µs | 4.34× | 27.1% |

#### Competitive Landscape (1,000 × 500):
| Library | Features | Runtime (1k × 500) | Series / sec | Speedup (raw time) | Per-feature | Speedup (per-feature) |
| :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| **Kymora (`core33`)** | **33** | **3.18 ms** | **314,450** | **Baseline (1.0×)** | **0.0964 µs** | **Baseline (1.0×)** |
| `catch22` | 22 | 833.1 ms | 1,200 | **262× slower** | 37.87 µs | **393×** |
| `TSFEL` | 156 | 2,541.6 ms | 393 | **799× slower** | 16.29 µs | **169×** |
| `tsfresh` | 777 | 20,891.2 ms | 48 | **6,570× slower** | 26.89 µs | **279×** |

Pooled medians: kymora over 4 HEAD rounds (n=400 runs), competitors over 10 rounds (n=53/83/64); 95% bootstrap CIs in `benchmarks/results/F1_REPORT.md`. Raw time answers "how long for the batch"; per-feature answers "how expensive each number is".

#### Memory Footprint (100,000 series × 500 steps) †:
* **Kymora:** **25.18 MiB** allocated memory (strictly the output matrix: $100,000 \times 33 \times 8\text{ B}$, with **+0.00 MiB intermediate overhead**).
* **tsfresh / Pandas:** **+1,250 MiB** memory ballooning due to melted DataFrame indices.


---

### The 33 Curated Features

Kymora deliberately computes 33 high-signal, non-redundant features spanning all temporal domains:
* **Distribution Moments:** Mean, Standard Deviation, Variance, Skewness, Kurtosis.
* **Extrema & Spans:** Min, Max, Peak-to-Peak Range, Quantiles (q05, q25, median, q75, q95), Interquartile Range (IQR).
* **Dynamics & Crossing:** Zero Crossing Rate, Mean Crossing Rate, Root Mean Square (RMS), Crest Factor, Median Absolute Deviation (MAD).
* **Temporal Differences:** Mean Absolute Change, Mean Consecutive Change, Number of Local Peaks.
* **Autocorrelation Structure:** Lag-1, Lag-2, Lag-5, Lag-10 Autocorrelation.
* **Spectral Domain:** Energy, Spectral Energy, Dominant Frequency, Spectral Centroid, Spectral Spread, Spectral Roll-off.
* **Complexity:** Permutation Entropy (order 3, delay 1).

---

### Contributing

Contributions, bug reports, and PRs are welcome!
Please check [`CONTRIBUTING.md`](https://github.com/Aamodx6/Kymora/blob/main/CONTRIBUTING.md) for details on setting up the local Rust/Python development environment and running the benchmark suites.

---

### License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/Aamodx6/Kymora/blob/main/LICENSE) for details.

*Built with Rust and Python by [Aamod](https://github.com/Aamod007).*
