# Kymora (formerly Tsxtract)
### High-Performance Time-Series Feature Extraction. Rust Core. Python Ease.

[![PyPI - Version](https://img.shields.io/pypi/v/kymora.svg?color=blue)](https://pypi.org/project/kymora/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kymora.svg)](https://pypi.org/project/kymora/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Aamodx6/Kymora/actions/workflows/ci.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/ci.yml)
[![Release](https://github.com/Aamodx6/Kymora/actions/workflows/release.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/release.yml)
[![Nightly](https://github.com/Aamodx6/Kymora/actions/workflows/nightly.yml/badge.svg)](https://github.com/Aamodx6/Kymora/actions/workflows/nightly.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://aamodx6.github.io/Kymora/)

> [!NOTE]
> **Kymora** was previously developed and released under the name **Tsxtract**. On PyPI, it is published and installed as [`kymora`](https://pypi.org/project/kymora/):
> ```bash
> pip install kymora
> ```

> **Batch time-series feature extraction: 33 features at 2.33 ms median per 1,000 series x 500 steps (428,633 series/s; 84.4× catch22, 1,177× TSFEL, 10,502× tsfresh), with no copy of the input and bounded O(T × L) worker scratch (~2.26–3.22 MiB at N ≤ 10k).**

**Kymora** is a minimalistic, dependency-light time-series feature extraction library designed to make extracting statistical, temporal, and spectral features across large datasets fast and memory-efficient. It combines a zero-copy Rust engine with a clean, Scikit-Learn-compatible Python interface—ideal for machine learning pipelines, quantitative finance, real-time sensor telemetry, and high-throughput research.

[PyPI](https://pypi.org/project/kymora/) • [Features](#key-features) • [Installation](#installation) • [Quickstart](#quickstart) • [Benchmarks](#benchmarks) • [Streaming & Real-Time Telemetry](#streaming-real-time-telemetry) • [Scikit-Learn Integration](#scikit-learn-pipeline) • [Documentation](https://aamodx6.github.io/Kymora/) • [Website](https://landing-drab-six-14.vercel.app)

---

### Why Kymora?

Traditional Python time-series feature libraries (`tsfresh`, `TSFEL`, `catch22`) force a painful trade-off: **wait minutes to hours for feature extraction, or risk Out-Of-Memory (OOM) crashes from defensive copies.** Kymora eliminates that trade-off.

* **Throughput (measured):** Pooled median **428,633 series/second** (2.33 ms; 95% bootstrap CI [367,067, 475,896] series/s, [2.10, 2.72] ms) across 3 same-session interleaved rounds on an i7-13620H laptop, 10 cores / 16 threads under High Performance scheme — about **84.4×** `catch22` (126.5× per-feature), **1,177×** `TSFEL` (248.9× per-feature), and **10,502×** `tsfresh` (446.0× per-feature) raw time on the same machine (see Benchmarks and `CLAIMS.md`).
* **Zero-Copy Ingestion:** Directly borrows contiguous NumPy buffer pointers via PyO3. No copy of the input, no DataFrame melting, and predictable worker scratch memory ($O(T \times L)$, ~2.26–3.22 MiB at $N \le 10,000$; does not scale with $N$).
* **33 Curated, High-Signal Features:** Avoids the curse of dimensionality. Features are mathematically non-redundant ($|r| < 0.70$ for 83.3% of pairs), spanning distribution moments, quantiles, crossings, spectral power, and permutation entropy.
* **Full Multi-Core Scaling (GIL-Free):** Releases Python's Global Interpreter Lock (GIL) across the entire computation region, saturating all CPU cores with Rayon's work-stealing scheduler.
* **Real-Time Streaming Ready:** Maintain rolling windows with incremental state updates using the built-in `StreamingExtractor` — amortized $O(1)$ per-sample ingestion (worst-case $O(W)$ upon drift re-anchoring) plus a fast 12-feature tier with no sorting and no FFT.

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
* **`core33` (33 features - Default):** Frozen authoritative v1.0 set spanning all temporal, quantile, and spectral domains (~1.90 ms median per 1,000 series on i7-13620H / 16 threads, re-measured 2026-11-22; pooled multi-session median 2.33 ms / 428,633 series/s across same-session interleaved rounds; 0.0575 µs per series-feature).
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
| Library | Features | Runtime (1k × 500) | Series / sec | Speedup (raw time) | Per-feature | Speedup (per-feature) |
| :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| **Kymora (`core33`)** | **33** | **2.33 ms** | **428,633** | **Baseline (1.0×)** | **0.0707 µs** | **Baseline (1.0×)** |
| `catch22` | 22 | 196.82 ms | 5,081 | **84.4× slower** | 8.95 µs | **126.5×** |
| `TSFEL` | 156 | 2,745.41 ms | 364 | **1,177× slower** | 17.60 µs | **248.9×** |
| `tsfresh` | 777 | 24,500.85 ms | 41 | **10,502× slower** | 31.53 µs | **446.0×** |

Pooled medians: kymora over 3 interleaved sessions (median 2.33 ms, 95% CI [2.10, 2.72] ms; 428,633 series/s [367,067, 475,896]); competitors run multi-threaded (16 threads) in the same session rounds; artifacts `benchmarks/results/HEADLINE_SAME_SESSION_REPORT.md` and `benchmarks/results/headline_same_session_ratios.json`. Per-session ratios: catch22 [54.0×, 99.6×, 91.8×], TSFEL [995.5×, 1,316.0×, 1,394.0×], tsfresh [5,633.4×, 12,268.2×, 11,604.5×]. Raw time answers "how long for the batch"; per-feature answers "how expensive each number is". Different feature counts mean different work — read both columns, and prefer the equal-feature table above for a like-for-like claim.

#### Predictive utility on real-world datasets (UCR Archive)

Speed is meaningless if features fail to predict well downstream. We evaluated Kymora `core33` against `catch22`, `TSFEL`, and `tsfresh` on canonical UCR univariate classification datasets (matched set $n = 42$, canonical fixed train/test splits, 16 threads across all four libraries, standard `RandomForestClassifier` and `RidgeClassifier` with fold-isolated imputation and scaling):

| Library | Features | Datasets | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Median Extract Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `tsfresh` | 777 | 42 | **84.79%** | **82.39%** | **1.64** | **1.79** | 20,943.62 ms |
| `TSFEL` | 156 | 42 | **81.00%** | **79.71%** | 2.33 | 2.26 | 942.67 ms |
| **Kymora (`core33`)** | **33** | **42** | **79.96%** | **77.42%** | **2.71** | **2.64** | **1.26 ms** (ref) |
| `catch22` | 22 | 42 | 79.83% | 75.75% | 2.79 | 2.98 | 159.40 ms |

* On linear models (Ridge with train-isolated `StandardScaler`), Kymora reaches **77.42% mean accuracy**, edging out `catch22` (**75.75%**) with an average rank of **2.64 vs 2.98** (head-to-head W/T/L 23/5/14, Holm-adjusted $p = 0.2016$).
* On tree models (Random Forest), Kymora achieves **79.96% mean accuracy** (rank 2.71 vs catch22 2.79, head-to-head W/T/L 23/3/16, Holm-adjusted $p = 0.5554$, Critical Difference $CD = 0.72$), within ~1.0% of TSFEL (81.00%) and ~4.8% of tsfresh (84.79%), while extracting features with a median per-dataset speedup of **117.2× vs catch22**, **768.2× vs TSFEL**, and **17,217.0× vs tsfresh**.
* Full per-dataset accuracy breakdown: [`benchmarks/results/DOWNSTREAM_UCR_REPORT.md`](benchmarks/results/DOWNSTREAM_UCR_REPORT.md).

#### Where Kymora is slower

Honest losses, with evidence (`benchmarks/results/2026-10-05_l1_rerun/l1_root_cause.json`, `benchmarks/results/L1_ROOT_CAUSE.md`, `benchmarks/results/SMALL_BATCH_REPORT.md`):

- **Tiny single-shot calls.** Against a hand-written numba baseline on the same 33 features, kymora loses only at 1 × 10 (p50 22.3 µs vs numba 1.3 µs) and 1 × 100 (p50 23.4 µs vs numba 11.8 µs, 1.98× loss), where Numba's JIT compiles inline loops without C-FFI wrapper overhead. At 10 × 500, Kymora wins 6.3× (117.8 µs vs 742.0 µs); at 100 × 100, Kymora wins 10.6× (143.2 µs vs 1518.0 µs); at 100 × 500, Kymora wins 21.2× (358.1 µs vs 7599.0 µs).
- **Small-batch threshold:** Inline sequential caller execution below 8,000 points (`SERIAL_WORK_SIZE_THRESHOLD = 8000`) matches 1T and 16T execution and avoids Rayon thread wake jitter.
- **Not a robust loss:** at ≥1,000 series, Kymora beats the numba baseline 6.0×–11.8× on identical features (equal-feature table above).

#### Memory footprint (re-measured on HEAD sweep $N = 1\text{k}..100\text{k}$, fresh-process peak RSS):
* **Worker scratch is $O(T \times L)$ and does not scale with $N$:** Peak worker scratch across 16 Rayon worker threads is bounded at ~2.26–3.22 MiB at $N \le 10,000$ and reaches a 14.28 MiB RSS high-water mark at $N=100,000$.
* **Zero defensive copies:** At $100,000 \times 500$, total process peak RSS is 406.77 MiB (input array 381.47 MiB + preallocated output matrix 25.18 MiB = 406.65 MiB, representing 99.97% of memory).
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
