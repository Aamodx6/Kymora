---
title: "Quickstart"
description: "Extract feature matrices, use DataFrames, handle ragged series, and train a classifier in five minutes."
order: 3
section: "Start here"
---

Turn raw sequences into a `(n_series, 33)` feature matrix, label it with stable column names, and feed it to a classifier. This guide builds one reproducible binary-classification workflow from synthetic data to saved artifacts.

```python
import numpy as np
import tsxtractor
rng = np.random.default_rng(0)
X = rng.standard_normal((100, 200))
features = tsxtractor.extract_features(X)
print("Output matrix dimensions:", features.shape)
```

```text
Output matrix dimensions: (100, 33)
```

## Goal

By the end of this guide you will be able to:

- Extract feature matrices from uniform 2D float64 arrays.
- Return labeled DataFrames with `extract_features_df()`.
- Audit column positions with `feature_names()`.
- Process ragged batches of variable-length series.
- Train and evaluate a scikit-learn classifier on extracted features.
- Persist features to Parquet, compressed NumPy, and CSV formats.

## Prerequisites

You need Tsxtract plus the optional data-science stack used below:

- **Tsxtract 0.3.0:** `pip install "tsxtractor[pandas]"` for the core plus DataFrame support.
- **scikit-learn:** `pip install scikit-learn` for the classifier demonstration.
- **PyArrow (optional):** `pip install pyarrow` if you want the Parquet save path.

```bash
pip install "tsxtractor[pandas]" scikit-learn pyarrow
```

## Steps

### 1. Generate a labeled time-series batch

A batch is a 2D array with one series per row in C-contiguous `float64` order. Build two synthetic classes: stationary noise versus noise plus linear drift.

```python
import numpy as np
rng = np.random.default_rng(42)
n_samples = 200
series_length = 300
class_0 = rng.standard_normal((n_samples // 2, series_length))
time_axis = np.linspace(0, 5, series_length)
class_1 = rng.standard_normal((n_samples // 2, series_length)) + 0.5 * time_axis
X = np.ascontiguousarray(np.vstack([class_0, class_1]), dtype=np.float64)
y = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))
print("Input data shape:", X.shape)
print("Data type:", X.dtype)
print("Memory is C-contiguous:", X.flags.c_contiguous)
```

```text
Input data shape: (200, 300)
Data type: float64
Memory is C-contiguous: True
```

### 2. Extract features into NumPy

Call `extract_features()` on the matrix. The call borrows the buffer zero-copy, releases the GIL, and spreads series across Rayon worker threads.

```python
import tsxtractor
features = tsxtractor.extract_features(X)
print("Features array shape:", features.shape)
print("Features data type:", features.dtype)
```

```text
Features array shape: (200, 33)
Features data type: float64
```

### 3. Extract directly to a labeled DataFrame

Use `extract_features_df()` when downstream work lives in pandas. Columns follow `feature_names()` order with a plain `RangeIndex`.

```python
df_features = tsxtractor.extract_features_df(X)
print("DataFrame columns:", list(df_features.columns[:6]))
print(df_features[["mean", "std", "trend_slope", "trend_r2"]].head(3).to_string())
```

```text
DataFrame columns: ['mean', 'std', 'var', 'min', 'max', 'median']
       mean       std  trend_slope  trend_r2
0 -0.041079  0.928720    -0.000096  0.000080
1 -0.011252  1.015118    -0.001055  0.008098
2 -0.079238  1.012682    -0.000318  0.000737
```

### 4. Inspect feature names and column order

Column order is a stability guarantee within a major version, so always resolve indices through `feature_names()` instead of hardcoding positions.

```python
names = tsxtractor.feature_names()
for idx, name in enumerate(names[:8]):
    print(f"Column {idx:2d} -> {name}")
```

```text
Column  0 -> mean
Column  1 -> std
Column  2 -> var
Column  3 -> min
Column  4 -> max
Column  5 -> median
Column  6 -> quantile_10
Column  7 -> quantile_25
```

### 5. Handle ragged series of different lengths

Real sensor fleets record unequal durations, and padding with zeros would corrupt variance, quantiles, and autocorrelations. Pass a list of 1D float64 arrays instead.

```python
ragged_batch = [
    np.ascontiguousarray(rng.standard_normal(120), dtype=np.float64),
    np.ascontiguousarray(rng.standard_normal(450), dtype=np.float64),
    np.ascontiguousarray(rng.standard_normal(280), dtype=np.float64),
]
ragged_features = tsxtractor.extract_features(ragged_batch)
print("Extracted matrix shape from ragged input:", ragged_features.shape)
```

```text
Extracted matrix shape from ragged input: (3, 33)
```

### 6. Train a scikit-learn classifier

Extracted arrays plug directly into estimators and cross-validation without adapters. Stratify the split so both signal classes appear in train and test.

```python
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    features, y, test_size=0.3, random_state=42, stratify=y
)
clf = HistGradientBoostingClassifier(random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred, target_names=["Noise", "Drift"]))
```

```text
              precision    recall  f1-score   support

       Noise       1.00      1.00      1.00        30
       Drift       1.00      1.00      1.00        30

    accuracy                           1.00        60
   macro avg       1.00      1.00      1.00        60
weighted avg       1.00      1.00      1.00        60
```

### 7. Save features to disk

Persist the matrix once so training, tuning, and reporting all read identical inputs. Parquet preserves column names, while `.npz` keeps a pure-NumPy bundle.

```python
df_features.to_parquet("features.parquet", engine="pyarrow", index=False)
np.save("features.npy", features)
df_features.to_csv("features.csv", index=False)
print("Saved shapes:", features.shape, df_features.shape)
```

```text
Saved shapes: (200, 33) (200, 33)
```

> [!TIP]
> Save the output of `feature_names()` alongside the matrix (for `.npz`, add `names=np.array(names)`). Future readers can then verify column meaning without consulting docs.

## Complete example

This script combines synthesis, extraction, ragged handling, model training, and feature ranking in one runnable file:

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import tsxtractor
rng = np.random.default_rng(123)
n_samples = 400
length = 250
time = np.linspace(0, 4 * np.pi, length)
signals_0 = np.sin(time) + rng.normal(0, 0.2, (n_samples // 2, length))
signals_1 = np.cumsum(rng.normal(0, 0.1, (n_samples // 2, length)), axis=1)
X = np.ascontiguousarray(np.vstack([signals_0, signals_1]), dtype=np.float64)
y = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))
df = tsxtractor.extract_features_df(X)
print("Extracted DataFrame shape:", df.shape)
ragged_sample = [np.ascontiguousarray(X[0, :100]), np.ascontiguousarray(X[1, :200]), np.ascontiguousarray(X[2, :250])]
print("Ragged features shape:", tsxtractor.extract_features(ragged_sample).shape)
X_train, X_test, y_train, y_test = train_test_split(df.values, y, test_size=0.25, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
print(f"Test accuracy: {model.score(X_test, y_test):.3f}")
top = np.argsort(model.feature_importances_)[::-1][:3]
print("Top 3 features:", [tsxtractor.feature_names()[i] for i in top])
```

```text
Extracted DataFrame shape: (400, 33)
Ragged features shape: (3, 33)
Test accuracy: 1.000
Top 3 features: ['mean_abs_change', 'spectral_entropy', 'cid_ce']
```

## Common pitfalls

- **1D input to `extract_features()`:** a bare 1D array raises `TypeError` because the batch API needs shape `(n_series, length)`. Reshape single series with `x.reshape(1, -1)` or use `sliding_features()` for rolling windows.
- **Wrong dtype:** `int64`, `float32`, and `float16` arrays raise `TypeError` instead of being copied silently. Convert once with `X.astype(np.float64)` and keep that buffer.
- **Empty series in ragged lists:** an empty 1D member raises `ValueError` naming its index. Filter zero-length recordings before extraction.
- **NaN rows after extraction:** any NaN in a series blanks all 33 columns for that row by design. Impute upstream when partial features are required.

## Next steps

Continue from working extraction to internals and production patterns:

- [Core Concepts](/docs/core-concepts) — memory layout, dtypes, and the NaN contract.
- [Pandas and Polars Integration](/docs/pandas-and-polars) — grouped and columnar workflows.
- [Scikit-Learn Pipelines](/docs/sklearn-pipelines) — custom transformers without leakage.
- [Large Datasets & Streaming](/docs/large-datasets) — batching, sliding windows, and online extraction.
