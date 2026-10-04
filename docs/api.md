# API Reference

Complete Python API specification for `kymora` v0.6.0.

```python
import kymora

kymora.__version__  # "0.6.0"
```

The package ships full type annotations and a `py.typed` marker for mypy and language servers.

---

## Batch Extraction

### extract_features

```python
extract_features(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: np.ndarray | None = None,
    views: Sequence[str] | None = None,
) -> np.ndarray
```

Extract features for every series in a batch.

**Parameters**

- `X` — 2D C-contiguous `float64` array of shape `(n_series, length)`, or a sequence of 1D C-contiguous `float64` arrays with variable lengths.
- `profile` — Execution profile: `"minimal"` (12 features), `"core33"` (default 33 features), `"extended"`, or `"full"`.
- `features` — Explicit list of feature names to extract, overriding profile selection.
- `n_jobs` — Thread count override. Defaults to logical CPU core count.
- `out` — Optional pre-allocated 2D array of shape `(n_series, n_features)` to receive results in place without allocation.
- `views` — Optional sequence of time-series transform views to compute: `"raw"`, `"diff"`, `"diff2"`, `"detrend"`, `"znorm"`, `"abs"`, `"logret"`, `"rank"`. Features invariant to transforms are automatically pruned.

**Returns**

A 2D `float64` array of shape `(n_series, n_features)`.

```python
import numpy as np
import kymora

X = np.random.default_rng(0).standard_normal((1000, 500))

# Default Core33 batch extraction
feats = kymora.extract_features(X)

# Multi-view extraction across raw, differences, and z-normalization
feats_views = kymora.extract_features(X, views=["raw", "diff", "znorm"])
```

---

### extract_features_df

```python
extract_features_df(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: np.ndarray | None = None,
    views: Sequence[str] | None = None,
) -> pd.DataFrame
```

Same computation as `extract_features`, returned as a labeled `pandas.DataFrame`. Columns match `feature_names(...)`.

Requires `pandas` (`pip install "kymora[pandas]"`).

---

### sliding_features

```python
sliding_features(x: np.ndarray, window: int, stride: int = 1) -> np.ndarray
```

Extracts rolling-window feature matrices across a single long 1D series without copying window data.

**Parameters**

- `x` — 1D C-contiguous `float64` array.
- `window` — Window length in samples (`1 <= window <= len(x)`).
- `stride` — Step between consecutive windows (`>= 1`, defaults to 1).

**Returns**

A 2D `float64` array of shape `(n_windows, 33)` where `n_windows = (len(x) - window) // stride + 1`.

---

## Multichannel & Cross-Channel Extraction

### extract_features_mc

```python
extract_features_mc(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
) -> np.ndarray
```

Extract per-channel features and cross-channel interaction metrics from multichannel time-series data.

**Parameters**

- `X` — 3D array of shape `(n_samples, n_channels, length)`.
- `profile` — Profile applied to each channel.
- `features` — Specific feature subset applied to each channel.
- `cross` — When `True`, computes cross-channel interaction metrics (pairwise cross-correlation peaks, lag offsets, cross-covariance, Pearson correlation, and global spectral coherence / eigenvalue spread).
- `max_pairs` — Maximum number of channel pairs evaluated for pairwise metrics (defaults to 8).
- `n_jobs` — Thread count.
- `views` — Optional multi-view transforms applied to each channel.

**Returns**

A 2D `float64` array of shape `(n_samples, total_features)`.

---

### extract_features_mc_df

```python
extract_features_mc_df(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
) -> pd.DataFrame
```

Same computation as `extract_features_mc`, returned as a labeled `pandas.DataFrame`. Columns match `feature_names_mc(...)`.

---

## Streaming Extractor

### StreamingExtractor

```python
class StreamingExtractor:
    def __init__(self, window_size: int) -> None: ...
    def push(self, value: float) -> bool: ...
    def compute(self, kind: str = "fast") -> np.ndarray: ...
    def reset(self) -> None: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
```

Single-stream sliding-window extractor maintaining an internal circular buffer and $O(1)$ incremental state updates.

- `push(value)` returns `True` once the circular buffer has reached `window_size`.
- `compute("fast")` evaluates 12 streaming features in under 100 ns.
- `compute("all")` evaluates all 33 Core features over the current window.

---

### MultiStreamExtractor

```python
class MultiStreamExtractor:
    def __init__(self, n_streams: int, window_size: int) -> None: ...
    def push_many(self, values: np.ndarray) -> bool: ...
    def compute(self, streams: list[int] | None = None, kind: str = "all") -> np.ndarray: ...
    def reset(self, stream_idx: int | None = None) -> None: ...
    @property
    def n_streams(self) -> int: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    @property
    def count(self) -> int: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
```

Fleet streaming engine for processing thousands of time-series streams concurrently with contiguous memory layout and cache locality.

- `push_many(values)` ingests a vector of values for all active streams simultaneously.
- `compute(streams=None, kind="fast"|"all")` extracts features across designated streams in parallel.

---

## Supervised Feature Selection

### select_features

```python
select_features(
    F: np.ndarray | pd.DataFrame,
    y: Sequence[Any] | np.ndarray,
    task: str = "auto",
    fdr: float = 0.05,
    max_corr: float = 0.90,
) -> tuple[list[int], pd.DataFrame]
```

Select significant, non-redundant time-series features using hypothesis testing, False Discovery Rate (FDR) control, and correlation-threshold clustering.

**Parameters**

- `F` — Feature matrix of shape `(n_samples, n_features)`.
- `y` — Target labels or values of shape `(n_samples,)`.
- `task` — Task type: `"auto"`, `"classification"`, or `"regression"`.
- `fdr` — Benjamini-Hochberg FDR significance threshold (defaults to 0.05).
- `max_corr` — Pairwise correlation clustering threshold for redundancy pruning (defaults to 0.90).

**Returns**

`(selected_indices, report)` where `selected_indices` contains column indices of the selected features, and `report` provides a tabular summary of statistics, p-values, adjusted p-values, and cluster assignments.

---

### KymoraSelector

```python
class KymoraSelector:
    def __init__(self, task: str = "auto", fdr: float = 0.05, max_corr: float = 0.90) -> None: ...
    def fit(self, X: np.ndarray | pd.DataFrame, y: Sequence[Any] | np.ndarray) -> KymoraSelector: ...
    def transform(self, X: np.ndarray | pd.DataFrame) -> np.ndarray | pd.DataFrame: ...
    def fit_transform(self, X: np.ndarray | pd.DataFrame, y: Sequence[Any] | np.ndarray) -> np.ndarray | pd.DataFrame: ...
    def get_support(self, indices: bool = False) -> np.ndarray: ...
```

Scikit-learn compatible transformer implementing FDR-controlled supervised feature selection for direct inclusion in ML pipelines.

---

## Metadata & Introspection

### feature_names

```python
feature_names(
    profile: str | None = None,
    features: Sequence[str] | None = None,
    views: Sequence[str] | None = None,
) -> list[str]
```

Returns output feature names in exact column order. Features 0..32 are frozen across all minor releases.

---

### feature_names_mc

```python
feature_names_mc(
    n_channels: int,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    views: Sequence[str] | None = None,
) -> list[str]
```

Returns output column names for multichannel extraction including channel prefixes and cross-channel metric names.

---

### list_profiles

```python
list_profiles() -> dict[str, int]
```

Returns available feature profile names mapped to their respective feature counts.

---

### describe_feature

```python
describe_feature(name: str) -> dict[str, str]
```

Returns metadata for a given feature name, including its cost class, dependencies, and registered aliases.

---

## Hardware Auto-Tuning

### tune

```python
tune(
    shapes: Sequence[tuple[int, int]] = ((1000, 500),),
    budget_s: float = 10.0,
) -> dict[str, Any]
```

Microbenchmarks execution variants on current hardware and caches optimal execution parameters locally. Pool selection is recorded for forward compatibility.

---

## Threading & Runtime Controls

- Scheduling is Rayon today: `n_jobs` builds a dedicated pool for the call, otherwise the global pool is used (honors `RAYON_NUM_THREADS=N`).
- `KYMORA_POOL` (`spin`/`rayon`) is currently **read by nothing** — the
  persistent spin-pool prototype was removed from main to
  `experiment/spin-pool` (see `docs/ROADMAP.md`; revival is gated on
  arch.md Z6). Treat any `tune()` pool recommendation as provisional until
  the backend lands.
