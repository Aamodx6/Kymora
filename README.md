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

> **Batch time-series feature extraction: 33 features at 1.74 ms median per 1,000 series x 500 steps (575,391 series/s; 249× catch22, 1,175× TSFEL, 8,612× tsfresh), with no copy of the input and 3.21 MiB worker scratch.**

**Kymora** is a minimalistic, dependency-light time-series feature extraction library designed to make extracting statistical, temporal, and spectral features across large datasets fast and memory-efficient. It combines a zero-copy Rust engine with a clean, Scikit-Learn-compatible Python interface—ideal for machine learning pipelines, quantitative finance, real-time sensor telemetry, and high-throughput research.

[PyPI](https://pypi.org/project/kymora/) • [Features](#key-features) • [Installation](#installation) • [Quickstart](#quickstart) • [Benchmarks](#benchmarks) • [Streaming & Real-Time Telemetry](#streaming-real-time-telemetry) • [Scikit-Learn Integration](#scikit-learn-pipeline) • [Documentation](https://aamodx6.github.io/Kymora/) • [Website](https://landing-drab-six-14.vercel.app)

---

### Why Kymora?

Traditional Python time-series feature libraries (`tsfresh`, `TSFEL`, `catch22`) force a painful trade-off: **wait minutes to hours for feature extraction, or risk Out-Of-Memory (OOM) crashes from defensive copies.** Kymora eliminates that trade-off.

* **Throughput (measured):** Pooled median **575,391 series/second** (1.74 ms; best run **799,680 series/second**) on an i7-13620H laptop, 10 cores / 16 threads under High Performance scheme — about **249×** `catch22` (373× per-feature), **1,175×** `TSFEL` (248× per-feature), and **8,612×** `tsfresh` (366× per-feature) raw time on the same machine (see Benchmarks and `CLAIMS.md`).
* **Zero-Copy Ingestion:** Directly borrows contiguous NumPy buffer pointers via PyO3. No copy of the input, no DataFrame melting, and predictable scratch memory (3.21 MiB for 10,000 series).
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
* **`core33` (33 features - Default):** Frozen authoritative v1.0 set spanning all temporal, quantile, and spectral domains (~1.90 ms median per 1,000 series on i7-13620H / 16 threads, re-measured 2026-11-22; a same-day repeat measured 2.53 ms — run-to-run spread, both artifacts committed; 0.0575 µs per series-feature).
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
| **Kymora (`core33`)** | **33** | **1.74 ms** | **575,391** | **Baseline (1.0×)** | **0.0527 µs** | **Baseline (1.0×)** |
| `catch22` | 22 | 432.6 ms | 2,312 | **249× slower** | 19.66 µs | **373×** |
| `TSFEL` | 156 | 2,041.5 ms | 490 | **1,175× slower** | 13.09 µs | **248×** |
| `tsfresh` | 777 | 14,966.8 ms | 67 | **8,612× slower** | 19.26 µs | **366×** |

Pooled medians: kymora over 360 runs across 3 interleaved sessions (median 1.74 ms, 95% CI [1.72, 1.76] ms; best 1.25 ms); competitors 8/10/7 runs; artifacts `benchmarks/results/HEADLINE_THROUGHPUT_REPORT.md` and `benchmarks/results/2026-11-22_reproduce_readme/`. Previous exploratory Silent session (1.84 ms / 542,682 series/s; best 1.57 ms / 636,943 series/s) recorded in `CLAIMS.md`. Raw time answers "how long for the batch"; per-feature answers "how expensive each number is". Different feature counts mean different work — read both columns, and prefer the equal-feature table above for a like-for-like claim.

#### Predictive utility on real-world datasets (UCR Archive)

Speed is meaningless if features fail to predict well downstream. We evaluated Kymora `core33` against `catch22`, `TSFEL`, and `tsfresh` on canonical UCR univariate classification datasets (5-fold stratified CV, standard `RandomForestClassifier` and `RidgeClassifier`):

| Library | Features | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Median Extract Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `tsfresh` | 777 | **95.97%** | **95.27%** | 1.60 | 1.60 | 7,592.33 ms |
| `TSFEL` | 156 | **95.55%** | **94.75%** | 1.75 | 1.50 | 3,037.06 ms |
| **Kymora (`core33`)** | **33** | **92.34%** | **93.58%** | 2.88 | **2.25** | **0.81 ms** (ref) |
| `catch22` | 22 | 93.73% | 90.47% | 2.38 | 3.25 | 60.68 ms |

* On linear models (Ridge with fold-isolated `StandardScaler`), Kymora reaches **93.58% accuracy**, beating `catch22` (**90.47%**, Wilcoxon $p = 0.0156$) with an average rank of **2.25 vs 3.25**.
* On tree models (Random Forest), Kymora achieves **92.34% accuracy** (within ~1.4% of catch22 and ~3.2% of tsfresh/TSFEL), while extracting features with a median per-dataset speedup of **80× vs catch22**, **5,344× vs TSFEL**, and **7,788× vs tsfresh**.
* Full per-dataset accuracy breakdown: [`benchmarks/results/DOWNSTREAM_UCR_REPORT.md`](benchmarks/results/DOWNSTREAM_UCR_REPORT.md).

#### Where Kymora is slower

Honest losses, with evidence (`benchmarks/results/2026-10-05_l1_rerun/l1_root_cause.json`, `benchmarks/results/L1_ROOT_CAUSE.md`, `B3_REPORT.md`):

- **Tiny single-shot calls.** Against a hand-written numba baseline on the same 33 features (HEAD rerun 2026-10-05), kymora loses only at 1 × 100 — gaussian 1.78× [1.76,1.80], heavy_tailed 1.75× [1.74,1.76], random_walk 1.43× [1.42,1.45] (95% CIs exclude 1.0; classified call-overhead + quantile-stage). At 10 × 500 the rows are parity/noise (0.85×–1.08×) and the 1 × 100 sinusoid row is a kymora win with a clamped CI — all four are exploratory (noisy host, CI95 rel-widths 13–78%; the rerun recorded no env/CPU load or per-row CV), so no claim is made off them. Absolute medians at 1 × 100 are ~0.029 ms vs numba 0.016–0.020 ms.
- **Thread wake at small n** (pre pool-cache, 0.8.0 prep). At 100 × 100, 16 threads made kymora ~27% *slower* than 1 thread (pool wake/join swamps ~12 µs/series of compute). Scaling efficiency at small batches is poor regardless of core count.
- **Single-series tail latency at very short lengths** (pre pool-cache, 0.8.0 prep). At length 10, kymora wins the median (345.8 µs vs numpy's 1,317.6 µs) but loses the tail (p99 15.4 ms, max 29.1 ms) to wake jitter.
- **Not a robust loss** (pre pool-cache, 0.8.0 prep): the 100 × 500 rows against the numba baseline are parity within noise (0.94×–0.99×, CI crosses 1.0).

Guidance: batch many series into one call, or use `StreamingExtractor` for one-series-at-a-time ingest. At ≥1,000 series the picture inverts — kymora beats the numba baseline 6.0×–11.8× on identical features (equal-feature table above).

#### Memory footprint (re-measured 2026-11-22, fresh-process peak RSS):
* **Matched Shape (10,000 × 500):**
  * **Kymora (`core33`):** peak extraction overhead **+5.73 MiB** over bare interpreter (input 41.73 MiB, preallocated output matrix 2.52 MiB, worker scratch **3.21 MiB**; no copy of the input).
  * **tsfresh (EfficientFCParameters, 777 features):** extraction peak **+410.3 MiB** (long-format DataFrame plus intermediate frames; total 452.2 MiB) — **71.6× larger** extraction overhead than Kymora.
* **Large Scale (100,000 × 500):**
  * **Kymora (`core33`):** +418.0 MiB peak over a bare interpreter — input 385.2 MiB, extraction overhead **+32.8 MiB** (25.2 MiB preallocated output matrix + ~7.6 MiB worker scratch; no copy of the input).
  * **tsfresh:** multi-hour run — **PENDING**, tracked in `CLAIMS.md`.

Artifact: `benchmarks/results/2026-11-22_remeasure/memory.jsonl` and measured scratch deltas.


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
