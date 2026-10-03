---
title: "API Reference"
description: "Comprehensive public API reference for tsxtractor functions, classes, type stubs, and constants."
order: 10
section: "Reference"
---

The public surface is exactly `__all__`: four functions, one class, and the version string. Stubs live in `python/tsxtractor/_core.pyi` with a `py.typed` marker, so type checkers see real signatures.

```python
import tsxtractor
print(sorted(tsxtractor.__all__))
print(tsxtractor.__version__)
```

```text
['StreamingExtractor', '__version__', 'extract_features', 'extract_features_df', 'feature_names', 'sliding_features']
0.3.0
```

## Functions

### `extract_features`

Extract 33 features per series from a uniform or ragged batch.

```python
def extract_features(X: _F64Array | Sequence[_F64Array]) -> _F64Array
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `X` | 2D C-contiguous float64 array `(n_series, length)`, or list of 1D float64 arrays | Required | Batch to featurize; ragged lists allow unequal lengths |

- **Returns:** float64 array of shape `(n_series, 33)`; column `i` is `feature_names()[i]`.
- **Raises:** `ValueError` for empty input, zero-length series, non-contiguous buffers, or zero-column 2D input; `TypeError` for wrong dtype or shape (1D, 3D, lists of lists, non-arrays).
- **Thread-safety:** safe to call from multiple threads; the GIL is released during compute.
- **Performance:** zero-copy input borrow; one `(n_series, 33)` output allocation; Rayon-parallel across series.

```python
import numpy as np
import tsxtractor
X = np.ascontiguousarray(np.arange(12.0).reshape(3, 4))
F = tsxtractor.extract_features(X)
print(F.shape, F.dtype)
print(F[:, 0].tolist())
```

```text
(3, 33) float64
[1.5, 5.5, 9.5]
```

### `extract_features_df`

Same as `extract_features()`, returned as a labeled DataFrame. Requires pandas.

```python
def extract_features_df(X: np.ndarray | Sequence[np.ndarray]) -> pd.DataFrame
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `X` | 2D float64 array `(n_series, length)`, or sequence of 1D float64 arrays | Required | Batch to featurize |

- **Returns:** `(n_series, 33)` float64 DataFrame with `feature_names()` columns and a `RangeIndex`.
- **Raises:** `ImportError` when pandas is missing (install `"tsxtractor[pandas]"`); otherwise the same `ValueError`/`TypeError` cases as `extract_features()`.
- **Thread-safety:** same as `extract_features()`; DataFrame construction is single-threaded pandas code.
- **Performance:** one extra DataFrame wrap over the array call; values are identical to `extract_features()` output.

```python
import tsxtractor
df = tsxtractor.extract_features_df(X)
print(df.shape, list(df.columns[:3]))
```

```text
(3, 33) ['mean', 'std', 'var']
```

### `feature_names`

Feature names in output column order.

```python
def feature_names() -> list[str]
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| None | — | — | Takes no arguments |

- **Returns:** list of 33 unique non-empty strings; index `i` names output column `i`.
- **Raises:** never raises.
- **Thread-safety:** pure metadata read, safe everywhere.
- **Performance:** `O(1)` static registry read; order is frozen within a major version.

```python
names = tsxtractor.feature_names()
print(len(names), names[13], names[30])
```

```text
33 root_mean_square dominant_frequency
```

### `sliding_features`

Extract features over rolling windows of a single series.

```python
def sliding_features(X: _F64Array, window: int, stride: int = 1) -> _F64Array
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `X` | 1D C-contiguous float64 array | Required | Long series to window |
| `window` | int | Required | Window length; must satisfy `1 <= window <= len(X)` |
| `stride` | int | `1` | Step between window starts; must be `>= 1` |

- **Returns:** float64 array of shape `(n_windows, 33)` with `n_windows == (len(X) - window) // stride + 1`.
- **Raises:** `ValueError` for `window`/`stride` below 1, `window` longer than the series, empty input, or non-contiguous buffers; `TypeError` for non-integer window parameters.
- **Thread-safety:** same parallel guarantees as batch extraction, spread across windows.
- **Performance:** windows borrow slices of the input with no data copy; NaN policy applies per window.

```python
x = np.ascontiguousarray(np.arange(10.0))
S = tsxtractor.sliding_features(x, window=4, stride=3)
print(S.shape)
```

```text
(3, 33)
```

## Classes

### `StreamingExtractor`

Stateful streaming extractor with `O(1)` incremental rolling-window updates and periodic re-anchoring every 4,096 steps.

```python
class StreamingExtractor:
    def __init__(self, window_size: int) -> None: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    def push(self, val: float) -> bool: ...
    def reset(self) -> None: ...
    def compute_features(self) -> _F64Array: ...
```

| Member | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `(window_size: int)` | Create an extractor; raises `ValueError` when `window_size < 2` |
| `window_size` | read-only property | Configured window capacity |
| `is_full` | read-only property | `True` once `window_size` samples have been ingested |
| `push` | `(val: float) -> bool` | Ingest one sample; returns `True` when a feature vector is available |
| `reset` | `() -> None` | Clear buffer and accumulators for a new session |
| `compute_features` | `() -> _F64Array` | Length-33 float64 vector; all NaN until the window fills |

- **Returns:** `compute_features()` yields 33 float64 features matching batch extraction to `rtol=1e-9`.
- **Raises:** `ValueError` from the constructor for `window_size` below 2.
- **Thread-safety:** a single instance is not safe for concurrent `push()` calls; use one instance per stream.
- **Performance:** `O(1)` per-sample updates of power sums, trend covariance, differences, and crossings; full recompute only at fill time and every 4,096 steps.

```python
stream = tsxtractor.StreamingExtractor(window_size=4)
for v in (1.0, 2.0, 3.0, 4.0):
    ready = stream.push(v)
print("Ready:", ready, "Full:", stream.is_full)
print("Length:", len(stream.compute_features()))
stream.reset()
print("Full after reset:", stream.is_full)
```

```text
Ready: True Full: True
Length: 33
Full after reset: False
```

## Module data

### `__version__`

Package version string read from installed distribution metadata (filled from `pyproject.toml`/`Cargo.toml` at build time).

```python
__version__: str = "0.3.0"
```

- **Returns:** PEP 440 version string such as `"0.3.0"`.
- **Raises:** never raises; falls back to `"0.0.0.dev0"` in an uninstalled source tree.

> [!NOTE]
> `extract_features()` rejects 1D input with `TypeError` even though the message names the 2D contract. Reshape single series with `x.reshape(1, -1)` or window them with `sliding_features()`.

## See also

Internal links for tasks surrounding each call:

- [Core Concepts](/docs/core-concepts) — input rules and the NaN contract behind every `Raises` entry.
- [Feature Catalog](/docs/feature-catalog) — what each of the 33 output columns means.
- [Large Datasets & Streaming](/docs/large-datasets) — chunking and real-time extractor patterns.
- [Configuration & Environment Variables](/docs/configuration) — build flags affecting performance.
