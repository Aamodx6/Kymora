# Tsxtract
### High-Performance Time-Series Feature Extraction. Rust Core. Python Ease.

[![PyPI - Version](https://img.shields.io/pypi/v/tsxtract-rs.svg?color=blue)](https://pypi.org/project/tsxtract-rs/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tsxtract-rs.svg)](https://pypi.org/project/tsxtract-rs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Aamodx6/Tsxtract/actions/workflows/ci.yml/badge.svg)](https://github.com/Aamodx6/Tsxtract/actions/workflows/ci.yml)

> **What if time-series feature engineering was 800× faster and used zero defensive memory copies?**

**Tsxtract** is a minimalistic, dependency-light time-series feature extraction library designed to make extracting statistical, temporal, and spectral features across large datasets blazingly fast, memory-efficient, and effortless. It combines a zero-copy Rust engine with a clean, Scikit-Learn-compatible Python interface—ideal for machine learning pipelines, quantitative finance, real-time sensor telemetry, and high-throughput research.

[PyPI](https://pypi.org/project/tsxtract-rs/) • [Features](#key-features) • [Installation](#installation) • [Quickstart](#quickstart) • [Benchmarks](#benchmarks) • [Streaming & Sliding Windows](#streaming--sliding-windows) • [Scikit-Learn Integration](#scikit-learn-pipeline) • [Documentation](https://landing-drab-six-14.vercel.app)

---

### Why Tsxtract?

Traditional Python time-series feature libraries (`tsfresh`, `TSFEL`, `catch22`) force a painful trade-off: **wait minutes to hours for feature extraction, or risk Out-Of-Memory (OOM) crashes from defensive copies.** Tsxtract eliminates that trade-off.

* **Blazing Fast:** Computes up to **800,256 series/second** on standard hardware—outperforming `catch22` by **820×** and `tsfresh` by **14,000×**.
* **Zero-Copy Ingestion:** Directly borrows contiguous NumPy buffer pointers via PyO3. No data duplication, no DataFrame melting, and zero intermediate memory ballooning.
* **33 Curated, High-Signal Features:** Avoids the curse of dimensionality. Features are mathematically non-redundant ($|r| < 0.70$ for 83.3% of pairs), spanning distribution moments, quantiles, crossings, spectral power, and permutation entropy.
* **Full Multi-Core Scaling (GIL-Free):** Releases Python's Global Interpreter Lock (GIL) across the entire computation region, saturating all CPU cores with Rayon's work-stealing scheduler.
* **Real-Time Streaming Ready:** Compute streaming features with constant memory $O(1)$ state updates using the built-in `StreamingExtractor`.

---

### Key Features

* **Zero-Copy Hybrid Architecture:** PyO3 bindings pass 2D NumPy pointer references directly into native Rust SIMD and multi-core loops without copying a single byte.
* **Batch-First Parallelism:** Processes $N$ series in parallel across hardware threads instead of running serial Python loops.
* **Dual API Support:** Extract raw 2D NumPy matrices for maximum speed, or labeled Pandas/Polars DataFrames for immediate exploratory analysis.
* **Scikit-Learn Compatible:** Seamlessly drop `TsxtractTransformer` into any `sklearn.pipeline.Pipeline` or cross-validation grid search.
* **Realfft & Branchless Primitives:** Preallocated thread-local FFT workspaces and branchless quantile quickselects ensure predictable sub-millisecond execution.
* **Streaming & Sliding Windows:** Extract rolling features over continuous data streams without reallocating buffers.

---

### Installation

#### Prebuilt Wheels (Recommended)
Precompiled binary wheels are available on [PyPI (tsxtract-rs)](https://pypi.org/project/tsxtract-rs/) for **Linux** (`x86_64`, `aarch64`), **macOS** (Apple Silicon `arm64`, Intel `x86_64`), and **Windows** (`x64`). No Rust compiler required!

```bash
# Core install (NumPy only)
pip install tsxtract-rs

# With optional Pandas DataFrame support
pip install "tsxtract-rs[pandas]"
```

*Using `uv` or `conda`:*
```bash
uv add tsxtract-rs
```

#### From Source (Development)
```bash
git clone https://github.com/Aamod007/Tsxtract.git
cd Tsxtract
pip install maturin
maturin develop --release
```

---

### Quickstart

#### 1. Batch Feature Extraction (2D NumPy)
Extract 33 features from 100,000 series in under a second:

```python
import numpy as np
import tsxtractor as tsx

# 1,000 series of 500 time-steps (float64)
X = np.random.randn(1000, 500)

# Extract 33 features (zero-copy, multi-threaded)
features = tsx.extract_features(X)

print("Output shape:", features.shape)      # (1000, 33)
print("Feature names:", tsx.feature_names()[:5])
# ['mean', 'std', 'var', 'min', 'max', ...]
```

#### 2. Labeled Pandas DataFrame
```python
# Returns a labeled pandas DataFrame with clean column headers
df = tsx.extract_features_df(X)
print(df.head())
```

#### 3. Ragged Series of Different Lengths
```python
# Sequences of varying lengths are supported natively
arr1 = np.random.randn(300)
arr2 = np.random.randn(500)
arr3 = np.random.randn(120)

features = tsx.extract_features([arr1, arr2, arr3])
print(features.shape)  # (3, 33)
```

#### 4. Sliding Windows over a Long Signal
```python
# Extract rolling window features from a 1D continuous sensor stream
signal = np.random.randn(100_000)
windowed_features = tsx.sliding_features(signal, window=256, stride=64)
```

---

### Scikit-Learn Pipeline

Integrate directly into standard classification, regression, or clustering pipelines:

```python
import numpy as np
import tsxtractor as tsx
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class TsxtractTransformer(BaseEstimator, TransformerMixin):
    """Extract 33 Tsxtract features per input row (one series per row)."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_contig = np.ascontiguousarray(X, dtype=np.float64)
        return tsx.extract_features(X_contig)

# Assemble end-to-end reproducible pipeline
pipeline = Pipeline([
    ("features", TsxtractTransformer()),
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(n_estimators=100))
])

# Fit on raw time-series training data (n_samples, time_steps)
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
```

---

### Streaming & Real-Time Telemetry

Maintain running statistical features in real-time embedded systems or trading loops without recomputing from scratch:

```python
from tsxtractor import StreamingExtractor

# Initialize streaming extractor with buffer capacity
stream = StreamingExtractor(capacity=500)

# Ingest points one by one with O(1) state updates
for tick in incoming_data_feed:
    stream.push(tick)
    current_features = stream.compute()
```

---

### Benchmarks

Tested on a 16-core system across **1,000 series of 500 steps** (500,000 data points total):

| Library | Features | Runtime | Series / sec | Per-Feature Cost | Speedup vs Tsxtract |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Tsxtract (`tsxtract-rs`)** | **33** | **1.25 ms** | **800,256** | **0.038 µs** | **Baseline (1.0×)** |
| `catch22` | 22 | 1,024.8 ms | 976 | 46.58 µs | **820× slower** |
| `TSFEL` | 156 | 7,154.0 ms | 140 | 45.86 µs | **5,725× slower** |
| `tsfresh` | 777 | 17,683.3 ms | 57 | 22.76 µs | **14,151× slower** |

#### Memory Footprint (100,000 series × 500 steps):
* **Tsxtract:** **+25.2 MiB** allocated memory (strictly the output matrix, zero input duplication).
* **tsfresh / Pandas:** **+1,250 MiB** memory ballooning due to melted DataFrame indices.

---

### The 33 Curated Features

Tsxtract deliberately computes 33 high-signal, non-redundant features spanning all temporal domains:
* **Distribution Moments:** Mean, Standard Deviation, Variance, Skewness, Kurtosis.
* **Extrema & Spans:** Min, Max, Peak-to-Peak Range, Quantiles (q05, q25, median, q75, q95), Interquartile Range (IQR).
* **Dynamics & Crossing:** Zero Crossing Rate, Mean Crossing Rate, Root Mean Square (RMS), Crest Factor, Median Absolute Deviation (MAD).
* **Temporal Differences:** Mean Absolute Change, Mean Consecutive Change, Number of Local Peaks.
* **Autocorrelation Structure:** Lag-1, Lag-2, Lag-3, Lag-5, Lag-10 Autocorrelation.
* **Spectral Domain:** Energy, Spectral Energy, Dominant Frequency, Spectral Centroid, Spectral Spread, Spectral Roll-off.
* **Complexity:** Permutation Entropy (order 3, delay 1).

---

### Contributing

Contributions, bug reports, and PRs are welcome!
Please check [`CONTRIBUTING.md`](https://github.com/Aamod007/Tsxtract/blob/main/CONTRIBUTING.md) for details on setting up the local Rust/Python development environment and running the benchmark suites.

---

### License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/Aamod007/Tsxtract/blob/main/LICENSE) for details.

*Built with Rust and Python by [Aamod](https://github.com/Aamod007).*
