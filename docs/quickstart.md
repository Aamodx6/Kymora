# Quickstart

## A batch of equal-length series

The main path. One row in, one feature row out.

```python
import numpy as np
import tsxtractor

X = np.random.default_rng(0).standard_normal((10_000, 500))  # 10k series
feats = tsxtractor.extract_features(X)          # (10_000, 33) float64
names = tsxtractor.feature_names()              # column order, stable
```

Input must be **float64 and C-contiguous**. A wrong dtype raises `TypeError`
rather than being silently copied, so you decide where the conversion is paid:

```python
feats = tsxtractor.extract_features(X.astype(np.float64))
```

A slice like `X[:, ::2]` is not contiguous and raises `ValueError`; pass
`np.ascontiguousarray(X[:, ::2])` if that is what you want.

## Labeled columns

```python
df = tsxtractor.extract_features_df(X)
df.columns.tolist()[:3]     # ['mean', 'std', 'var']
```

Requires pandas (`pip install "tsxtract-rs[pandas]"`); it is not a hard
dependency of the library.

## Series of different lengths

Pass a list of 1D arrays. Each series is processed independently, so lengths do
not need to match.

```python
series = [rng.standard_normal(n) for n in (120, 500, 37)]
feats = tsxtractor.extract_features(series)      # (3, 33)
```

## Rolling windows over one long series

```python
x = rng.standard_normal(100_000)
feats = tsxtractor.sliding_features(x, window=256, stride=64)   # (1558, 33)
```

Windows are borrowed slices of your buffer — nothing is copied — and the work is
parallelised across windows. `window` must be at least 1 and no longer than the
series; `stride` must be at least 1. Anything else raises `ValueError`.

## Into a scikit-learn pipeline

Features come out as a plain dense matrix, so nothing special is required:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

X_feat = tsxtractor.extract_features(X)          # (n_series, 33)
X_feat = np.nan_to_num(X_feat)                   # see the NaN policy first
scores = cross_val_score(RandomForestClassifier(), X_feat, y, cv=5)
```

!!! note "Think before nan_to_num"
    A NaN row means that series contained a NaN, and a NaN column entry means
    that feature is undefined for that series (a constant series has no
    autocorrelation). Both are real information. Read the
    [NaN policy](nan-policy.md) before flattening them to zero.

## Controlling thread count

The Rust core uses the default rayon pool, which sizes itself to your logical
cores. Cap it with the standard rayon environment variable — useful inside a
container with a CPU quota, or when you are already parallelising at a higher
level:

```bash
RAYON_NUM_THREADS=4 python my_pipeline.py
```
