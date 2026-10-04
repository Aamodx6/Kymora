---
title: "API Reference"
description: "Comprehensive public API reference for tsxtractor functions, classes, type stubs, and constants."
order: 10
section: "Reference"
---

The public surface covers batch, streaming, multichannel, and supervised feature extraction. Stubs live in `python/tsxtractor/_core.pyi` with a `py.typed` marker for IDEs and type checkers.

```python
import tsxtractor
print(sorted(tsxtractor.__all__))
print(tsxtractor.__version__)
```

```text
['MultiStreamExtractor', 'StreamingExtractor', 'TsxSelector', '__version__', 'describe_feature', 'extract_features', 'extract_features_df', 'extract_features_mc', 'extract_features_mc_df', 'extract_features_ragged', 'feature_names', 'feature_names_mc', 'list_profiles', 'select_features', 'sliding_features', 'tune']
0.5.0
```

## Batch & Multi-View Functions

### `extract_features`

Extract features per series from a uniform or ragged batch, optionally across multiple mathematical views.

```python
def extract_features(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: np.ndarray | None = None,
    views: Sequence[str] | None = None,
) -> np.ndarray
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `X` | 2D float64/float32 array `(n_series, length)`, or list of 1D arrays | Required | Batch to featurize; ragged lists allow unequal lengths |
| `profile` | str | `"core33"` | Feature tier (`"minimal"`, `"core33"`, `"extended"`, `"full"`) |
| `features` | Sequence[str] | None | Explicit list of feature names to extract |
| `n_jobs` | int | None | Worker thread count override |
| `out` | np.ndarray | None | Optional pre-allocated buffer for zero-allocation writes |
| `views` | Sequence[str] | None | Multi-view transforms: `"raw"`, `"diff"`, `"diff2"`, `"detrend"`, `"znorm"`, `"abs"`, `"logret"`, `"rank"` |

- **Returns:** float64 array of shape `(n_series, n_features)`.
- **Raises:** `ValueError` for empty input, zero-length series, or non-contiguous buffers; `TypeError` for wrong dtype or shape.
- **Invariance Pruning:** Invariant features are automatically omitted from transformed views to prevent duplicate or zero-variance columns.

---

### `extract_features_df`

Same as `extract_features()`, returned as a labeled pandas DataFrame.

```python
def extract_features_df(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: np.ndarray | None = None,
    views: Sequence[str] | None = None,
) -> pd.DataFrame
```

---

### `sliding_features`

Extract features over rolling windows of a single continuous series.

```python
def sliding_features(
    x: np.ndarray,
    window: int,
    stride: int = 1,
) -> np.ndarray
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `x` | 1D float64 array | Required | Continuous series to window |
| `window` | int | Required | Window length; must satisfy `1 <= window <= len(x)` |
| `stride` | int | `1` | Step between window starts; must be `>= 1` |

---

## Multichannel Functions

### `extract_features_mc`

Extract per-channel features and cross-channel interaction metrics from 3D arrays.

```python
def extract_features_mc(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
) -> np.ndarray
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `X` | 3D array `(n_samples, n_channels, length)` | Required | Multidimensional batch |
| `cross` | bool | `True` | Compute cross-channel correlation, covariance, and coherence |
| `max_pairs` | int | `8` | Maximum number of channel pairs evaluated |

---

### `extract_features_mc_df`

Same as `extract_features_mc()`, returned as a labeled DataFrame.

```python
def extract_features_mc_df(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
) -> pd.DataFrame
```

---

## Supervised Feature Selection

### `select_features`

Select statistically significant, non-redundant time-series features.

```python
def select_features(
    F: np.ndarray | pd.DataFrame,
    y: Sequence[Any] | np.ndarray,
    task: str = "auto",
    fdr: float = 0.05,
    max_corr: float = 0.90,
) -> tuple[list[int], pd.DataFrame]
```

- **Returns:** `(selected_indices, report)` where `report` summarizes test statistics, p-values, adjusted p-values, and cluster assignments.

---

### `TsxSelector`

Scikit-learn compatible transformer implementing FDR-controlled feature selection.

```python
class TsxSelector:
    def __init__(self, task: str = "auto", fdr: float = 0.05, max_corr: float = 0.90) -> None: ...
    def fit(self, X: Any, y: Sequence[Any] | np.ndarray) -> TsxSelector: ...
    def transform(self, X: Any) -> Any: ...
    def fit_transform(self, X: Any, y: Sequence[Any] | np.ndarray) -> Any: ...
    def get_support(self, indices: bool = False) -> np.ndarray: ...
```

---

## Streaming Classes

### `StreamingExtractor`

Single-stream circular-buffer extractor with $O(1)$ state updates.

```python
class StreamingExtractor:
    def __init__(self, window_size: int) -> None: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    def push(self, val: float) -> bool: ...
    def reset(self) -> None: ...
    def compute(self, kind: str = "fast") -> np.ndarray: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
```

---

### `MultiStreamExtractor`

Fleet streaming engine for processing thousands of time-series streams concurrently.

```python
class MultiStreamExtractor:
    def __init__(self, n_streams: int, window_size: int) -> None: ...
    @property
    def n_streams(self) -> int: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    @property
    def count(self) -> int: ...
    def push_many(self, values: np.ndarray) -> bool: ...
    def reset(self, stream_idx: int | None = None) -> None: ...
    def compute(self, streams: list[int] | None = None, kind: str = "all") -> np.ndarray: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
```

---

## Hardware Auto-Tuning

### `tune`

Microbenchmarks execution variants (spin pool vs Rayon, chunk sizes) and caches optimal execution parameters.

```python
def tune(
    shapes: Sequence[tuple[int, int]] = ((1000, 500),),
    budget_s: float = 10.0,
) -> dict[str, Any]
```
