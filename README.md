# tsxtractor

Fast time-series feature extraction for Python, with a Rust core.

Extracts 33 statistical, temporal, and spectral features from batches of time
series. The Rust core releases the GIL and parallelizes across series with
rayon, so extraction scales with your cores and takes zero-copy views of your
numpy arrays.

## Install

```bash
pip install maturin
maturin develop --release   # from a clone, inside a virtualenv
```

## Usage

```python
import numpy as np
import tsxtractor

# batch: one row per series
X = np.random.randn(10_000, 500)
feats = tsxtractor.extract_features(X)        # (10_000, 33) float64
names = tsxtractor.feature_names()            # column order

# ragged series of different lengths
feats = tsxtractor.extract_features([arr1, arr2, arr3])

# rolling windows over one long series
feats = tsxtractor.sliding_features(x, window=256, stride=64)
```

## Features (33)

| Group | Features |
|---|---|
| Stats | mean, std, var, min, max, median, quantile_10/25/75/90, skewness, kurtosis, abs_energy, root_mean_square |
| Change | mean_abs_change, mean_change, cid_ce (z-normalized), mean_second_derivative_central |
| Counts | zero_crossings, mean_crossings, number_of_peaks (support 3), longest_strike_above/below_mean |
| Correlation | autocorr at lags 1, 2, 5, 10; linear trend slope and r² |
| Entropy | permutation_entropy (order 3, normalized to [0, 1]) |
| Spectral | dominant_frequency, spectral_centroid, spectral_entropy (positive bins, DC excluded, sample spacing 1) |

Conventions: population moments (`ddof=0`); numpy-default linear interpolation
for quantiles; skewness/kurtosis follow `scipy.stats` with `bias=True`
(kurtosis is Fisher/excess).

**NaN policy:** any NaN in a series makes all its features NaN — no silent
imputation. Features that are undefined for a series (e.g. autocorrelation of
a constant series, spectral features of a constant series, change features of
a length-1 series) are NaN individually.

## Benchmark

```bash
python benches/bench_vs_tsfresh.py 1000 500
```

Measured on Windows 11, Python 3.14, 1000 series × 500 steps:

| | features | time |
|---|---|---|
| tsxtractor | 33 | 0.004 s |
| tsfresh (EfficientFCParameters) | 777 | 155 s |

tsfresh computes far more features, so the honest number is per-feature
throughput: **~1700× faster per feature**. 100 000 series × 500 steps runs in
0.32 s.

## Development

```bash
python -m venv .venv && . .venv/Scripts/activate
pip install maturin numpy scipy pytest
maturin develop --release
pytest tests/            # every feature validated against numpy/scipy references
```
