# Quickstart

## Batch Feature Extraction

One row in, one feature row out. The Rust engine executes without GIL contention.

```python
import numpy as np
import tsxtract

rng = np.random.default_rng(0)
X = rng.standard_normal((10_000, 500))  # 10,000 series, 500 samples each

feats = tsxtract.extract_features(X)          # (10_000, 33) float64
names = tsxtract.feature_names()              # canonical column names
```

Input arrays must be **float64 and C-contiguous**. A wrong dtype or non-contiguous layout will raise `TypeError` or `ValueError` rather than silently copying.

---

## Multi-View Extraction

Generate multi-domain feature representations across differences, detrending, and normalizations:

```python
# Compute features across original series, first differences, and z-normalization
feats_views = tsxtract.extract_features(
    X,
    views=["raw", "diff", "znorm"]
)
view_names = tsxtract.feature_names(views=["raw", "diff", "znorm"])
print(f"Extracted {len(view_names)} features across 3 views.")
```

Features that are mathematically invariant to a transform (e.g. standard deviation under mean shift) are automatically pruned.

---

## Multichannel Sensor Streams

Extract features and cross-channel interaction dynamics from 3D arrays:

```python
# (n_samples, n_channels, length)
X_mc = rng.standard_normal((100, 4, 1000))

# Extract per-channel features and cross-channel dynamics
df_mc = tsxtract.extract_features_mc_df(X_mc, cross=True)
print(df_mc.shape)  # 100 rows x combined channel features
```

---

## Real-Time Fleet Streaming

Stream thousands of live signals concurrently with $O(1)$ updates:

```python
n_streams = 1000
window_size = 200

# Fleet extractor maintains contiguous circular buffers for all streams
extractor = tsxtract.MultiStreamExtractor(n_streams, window_size)

# Ingest new readings from IoT fleet or market feed
new_tick = rng.standard_normal(n_streams)
is_ready = extractor.push_many(new_tick)

if is_ready:
    # Sub-microsecond fast features (mean, std, RMS, etc.)
    fast_matrix = extractor.compute(kind="fast")
```

---

## Supervised Feature Selection in Scikit-Learn

Select statistically significant, non-redundant features using FDR control and correlation clustering:

```python
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier

# Seamless scikit-learn transformer
pipe = Pipeline([
    ("select", tsxtract.TsxSelector(task="classification", fdr=0.05)),
    ("clf", HistGradientBoostingClassifier())
])

# Fits FDR hypothesis tests and correlation clusters on X_feats, y
pipe.fit(feats, y)
predictions = pipe.predict(feats)
```

---

## Hardware Auto-Tuning (Wisdom)

Benchmark your local architecture to configure the optimal execution backend:

```python
# Auto-tunes spin-wait thresholds and thread pool strategies
profile = tsxtract.tune(shapes=[(1000, 500)], budget_s=5.0)
print(f"Optimal pool: {profile['best_config']['pool']}")
```
