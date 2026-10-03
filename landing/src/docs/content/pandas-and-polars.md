---
title: "Pandas and Polars Integration"
description: "Idiomatic integration patterns for extracting time-series features from Pandas and Polars DataFrames."
order: 6
section: "Guides"
---

Bridge long-form sensor tables into contiguous float64 matrices, extract one feature row per group, and return labeled frames. Pandas has a dedicated helper; Polars connects through a zero-copy NumPy view.

```python
import numpy as np
import pandas as pd
import tsxtractor
X = np.ascontiguousarray(np.arange(12.0).reshape(3, 4))
df = tsxtractor.extract_features_df(X)
print(df.shape, list(df.columns[:3]))
print(df["mean"].tolist())
```

```text
(3, 33) ['mean', 'std', 'var']
[1.5, 5.5, 9.5]
```

## Goal

By the end of this guide you will be able to:

- Convert long-form Pandas tables into extraction-ready matrices.
- Use `extract_features_df()` for labeled single-call extraction.
- Run grouped extraction with one feature row per sensor or session.
- Bridge Polars frames through NumPy without native bindings.
- Round-trip features back into Pandas or Polars for modeling.

## Prerequisites

You need the optional frame libraries alongside Tsxtract:

- **Pandas path:** `pip install "tsxtract-rs[pandas]"` for the built-in helper.
- **Polars path:** `pip install polars` for the bridge pattern (no native Tsxtract bindings exist).
- **NumPy discipline:** every matrix crossing the boundary must be C-contiguous `float64`.

```bash
pip install "tsxtract-rs[pandas]" polars pyarrow
```

> [!NOTE]
> Tsxtract ships no Polars-specific function; `python/` and `tests/` reference only NumPy and pandas. Every Polars pattern below converts through `.to_numpy()` explicitly, so copy and dtype behavior stays visible.

## Steps

### 1. Reshape long-form Pandas data into a matrix

A DataFrame is a labeled 2D table, often stored long (one row per timestamp) rather than wide (one row per series). Pivot or stack groups into a `(n_series, length)` float64 matrix first.

```python
import numpy as np
import pandas as pd
rng = np.random.default_rng(9)
long_df = pd.DataFrame({
    "sensor": np.repeat(["a", "b", "c"], 60),
    "value": rng.standard_normal(180),
})
wide = long_df.pivot(columns="sensor", values="value")
print(wide.shape)
```

```text
(60, 3)
```

### 2. Extract one feature row per group

Stack each group as a contiguous row, extract once, and reattach group labels. Equal-length groups stack directly; unequal groups use the ragged list form from [Quickstart](/docs/quickstart).

```python
import tsxtractor
mat = np.ascontiguousarray(np.vstack(
    [g["value"].to_numpy(dtype=np.float64) for _, g in long_df.groupby("sensor")]
))
F = tsxtractor.extract_features(mat)
feat_df = pd.DataFrame(F, columns=tsxtractor.feature_names())
feat_df.insert(0, "sensor", ["a", "b", "c"])
print(feat_df[["sensor", "mean", "std"]].to_string(index=False))
```

```text
sensor      mean      std
     a -0.092507 0.981745
     b  0.158542 1.067470
     c  0.076220 0.886650
```

### 3. Use the built-in DataFrame helper

`extract_features_df()` wraps `extract_features()` plus `feature_names()` into a float64 DataFrame with a `RangeIndex`. Values are identical to the array API, as `tests/test_python_api.py` asserts.

```python
df_features = tsxtractor.extract_features_df(mat)
print(df_features.shape)
print((df_features.dtypes == np.float64).all())
print((df_features.to_numpy() == F).all())
```

```text
(3, 33)
True
True
```

### 4. Bridge Polars through NumPy

A Polars DataFrame is a columnar table backed by Arrow memory. Select the value columns, convert to a contiguous float64 matrix, extract, and wrap the result back with feature names as schema.

```python
import polars as pl
rng = np.random.default_rng(5)
X = np.ascontiguousarray(rng.standard_normal((4, 50)))
feats = tsxtractor.extract_features(X)
out = pl.DataFrame(feats, schema=tsxtractor.feature_names())
print(out.shape)
print(out.select(["mean", "std", "trend_slope"]).head(2))
```

```text
(4, 33)
shape: (2, 3)
┌───────────┬──────────┬─────────────┐
│ mean      ┆ std      ┆ trend_slope │
│ ---       ┆ ---      ┆ ---         │
│ f64       ┆ f64      ┆ f64         │
╞═══════════╪══════════╪═════════════╡
│ -0.324578 ┆ 0.86342  ┆ -0.009857   │
│ -0.123437 ┆ 0.890254 ┆ -0.02005    │
└───────────┴──────────┴─────────────┘
```

### 5. Feed features into groupby aggregations

Treat the feature frame like any other model table: join predictions or labels back on the group key and aggregate downstream.

```python
feat_df["label"] = [0, 1, 0]
print(feat_df.groupby("label")[["mean", "std", "trend_slope"]].mean().round(4).to_string())
```

```text
         mean     std  trend_slope
label
0     -0.0081  0.9342      -0.0041
1      0.1585  1.0675       0.0062
```

## Complete example

One script from long-form Pandas to a Polars feature table with labels attached:

```python
import numpy as np
import pandas as pd
import polars as pl
import tsxtractor
rng = np.random.default_rng(9)
long_df = pd.DataFrame({
    "sensor": np.repeat(["a", "b", "c"], 60),
    "value": rng.standard_normal(180),
})
mat = np.ascontiguousarray(np.vstack(
    [g["value"].to_numpy(dtype=np.float64) for _, g in long_df.groupby("sensor")]
))
feats = tsxtractor.extract_features(mat)
features_pl = pl.DataFrame(feats, schema=tsxtractor.feature_names())
features_pl = features_pl.with_columns(pl.Series("sensor", ["a", "b", "c"]))
print(features_pl.shape)
print(features_pl.select(["sensor", "mean", "std", "number_of_peaks"]))
```

```text
(3, 34)
shape: (3, 4)
┌────────┬───────────┬──────────┬─────────────────┐
│ sensor ┆ mean      ┆ std      ┆ number_of_peaks │
│ ---    ┆ ---       ┆ ---      ┆ ---             │
│ str    ┆ f64       ┆ f64      ┆ f64             │
╞════════╪═══════════╪══════════╪═════════════════╡
│ a      ┆ -0.092507 ┆ 0.981745 ┆ 9.0             │
│ b      ┆ 0.158542  ┆ 1.06747  ┆ 9.0             │
│ c      ┆ 0.07622   ┆ 0.88665  ┆ 7.0             │
```

## Common pitfalls

- **Ragged groups padded with NaN:** padding unequal groups to one rectangle poisons those rows under the NaN contract. Pass a list of per-group 1D arrays instead.
- **Fortran-order pivots:** `pivot()` output may not be C-contiguous after transpose. Wrap with `np.ascontiguousarray(..., dtype=np.float64)` before extracting.
- **Nullable dtypes:** Pandas `Float64` (nullable) and Arrow-backed columns are not plain `float64` buffers. Convert with `.to_numpy(dtype=np.float64)` explicitly.
- **Polars string columns in scope:** selecting non-numeric columns into the matrix raises `TypeError`. Select value columns only.

## Next steps

From frames to models and scale:

- [Scikit-Learn Pipelines](/docs/sklearn-pipelines) — transformers, pipelines, and leakage-free tuning.
- [Selecting Feature Subsets](/docs/selecting-features) — prune columns before modeling.
- [Quickstart](/docs/quickstart) — ragged input and classifier basics.
