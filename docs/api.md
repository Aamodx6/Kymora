# API Reference

Complete Python API specification for `kymora` v0.8.0.

```python
import kymora

kymora.__version__  # "0.8.0"
```

The package ships full type annotations and a `py.typed` marker for mypy and language servers.

---

## Batch Extraction

### extract_features

```python skip
extract_features(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: np.ndarray | None = None,
    views: Sequence[str] | None = None,
    precision: str | None = None,
    out_dtype: str | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
) -> np.ndarray
```

Extract features for every series in a batch.

**Parameters**

- `X` — 2D C-contiguous `float64` or `float32` array of shape `(n_series, length)`, or a sequence of 1D C-contiguous arrays with variable lengths. See [Numerics](numerics.md) for layout rules.
- `profile` — Execution profile: `"minimal"` (10 features), `"core33"` (default 33 features), `"extended"`, or `"full"`.
- `features` — Explicit list of feature names to extract, overriding profile selection.
- `n_jobs` — Worker-thread count for this call. `None` uses the shared global pool (all threads); scaling stops near the physical core count (see [Performance](performance.md)).
- `out` — Optional pre-allocated C-contiguous `float64` array of shape `(n_series, n_features)` to receive results in place without allocation.
- `views` — Optional sequence of time-series transform views to compute: `"raw"`, `"diff"`, `"diff2"`, `"detrend"`, `"znorm"`, `"abs"`, `"logret"`, `"rank"`. Features invariant to transforms are automatically pruned. Requires `float64` input.
- `precision` — Validated but informational: `"float64"`/`"float32"` accepted; accumulation is always `float64` and the input dtype governs the read path.
- `out_dtype` — `"float64"` (default) or `"float32"` (casts on write).
- `nan_policy` — `"propagate"` (default) or `"raise"`; see [Numerics](numerics.md).
- `contiguous` — `"error"` (default, reject non-C input) or `"copy"` (one explicit copy plus a `UserWarning`).

**Returns**

A 2D array of shape `(n_series, n_features)`; `float32` when `out_dtype="float32"`, otherwise `float64`.

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

```python skip
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

```python skip
sliding_features(
    x: np.ndarray,
    window: int,
    stride: int = 1,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: np.ndarray | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
) -> np.ndarray
```

Extracts rolling-window feature matrices across a single long 1D series without copying window data.

**Parameters**

- `x` — 1D C-contiguous `float64` array.
- `window` — Window length in samples (`1 <= window <= len(x)`).
- `stride` — Step between consecutive windows (`>= 1`, defaults to 1).
- `profile`, `features`, `n_jobs`, `out`, `nan_policy`, `contiguous` — as in `extract_features`.

**Returns**

A 2D `float64` array of shape `(n_windows, 33)` where `n_windows = (len(x) - window) // stride + 1`.

---

## Multichannel & Cross-Channel Extraction

### extract_features_mc

```python skip
extract_features_mc(
    X: np.ndarray | Sequence[np.ndarray],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
) -> np.ndarray
```

Extract per-channel features and cross-channel interaction metrics from multichannel time-series data. See [Multichannel](multivariate.md).

**Parameters**

- `X` — 3D C-contiguous `float64` array of shape `(n_samples, n_channels, length)`, or a list of 2D `(n_channels, length_i)` arrays for ragged lengths (channel count must agree).
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

```python skip
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

```python skip
class StreamingExtractor:
    def __init__(self, window_size: int, anchor_interval: int | None = None, nan_policy: str | None = None) -> None: ...
    def push(self, value: float) -> bool: ...
    def compute(self, kind: str = "fast") -> np.ndarray: ...
    def reset(self) -> None: ...
    def set_anchor_interval(self, anchor_interval: int) -> None: ...
    @property
    def window_size(self) -> int: ...
    @property
    def anchor_interval(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
```

Single-stream sliding-window extractor maintaining an internal circular buffer and amortized-$O(1)$ incremental state updates.

- `push(value)` returns `True` once the circular buffer has reached `window_size`. `window_size >= 1`.
- `compute("fast")` derives the 12 streaming features from accumulators in $O(1)$: no window scan, no allocation, no sorting, no FFT.
- `compute("all")` evaluates all 33 Core features over the current window ($O(W)$-plus, exact batch pipeline).
- `anchor_interval` sets the periodic exact re-anchor cadence in pushes (default 4096); a drift guard re-anchors earlier when needed. See [Streaming guide](streaming.md) for the full complexity and accuracy contract.

---

### MultiStreamExtractor

```python skip
class MultiStreamExtractor:
    def __init__(self, n_streams: int, window_size: int) -> None: ...
    def push_many(self, values: np.ndarray, contiguous: str | None = None) -> bool: ...
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

```python skip
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

```python skip
class KymoraSelector:
    def __init__(self, task: str = "auto", fdr: float = 0.05, max_corr: float = 0.90) -> None: ...
    def fit(self, X: np.ndarray | pd.DataFrame, y: Sequence[Any] | np.ndarray) -> KymoraSelector: ...
    def transform(self, X: np.ndarray | pd.DataFrame) -> np.ndarray | pd.DataFrame: ...
    def fit_transform(self, X: np.ndarray | pd.DataFrame, y: Sequence[Any] | np.ndarray) -> np.ndarray | pd.DataFrame: ...
    def get_support(self, indices: bool = False) -> np.ndarray: ...
```

Scikit-learn compatible transformer implementing FDR-controlled supervised feature selection for direct inclusion in ML pipelines.

---

### KymoraTransformer

```python skip
from kymora.sklearn import KymoraTransformer  # pip install "kymora[sklearn]"

KymoraTransformer(
    profile: str = "core33",
    features: Sequence[str] | None = None,
    views: Sequence[str] | None = None,
    n_jobs: int | None = None,
    nan_policy: str | None = None,
    output_dtype: str | None = None,
)
```

Scikit-learn compatible panel transformer: `(n_series, length)` in,
`(n_series, n_features)` out. Stateless `fit`, `get_feature_names_out`,
`set_output(transform="pandas" | "polars")`, clone- and pickle-safe,
passing the full `parametrize_with_checks` suite. See
[Quickstart](quickstart.md) for a pipeline example.

---

## Metadata & Introspection

### feature_names

```python skip
feature_names(
    profile: str | None = None,
    features: Sequence[str] | None = None,
    views: Sequence[str] | None = None,
) -> list[str]
```

Returns output feature names in exact column order. Features 0..32 are frozen across all minor releases.

---

### feature_names_mc

```python skip
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

```python skip
list_profiles() -> dict[str, int]
```

Returns available feature profile names mapped to their respective feature counts.

---

### describe_feature

```python skip
describe_feature(name: str) -> dict[str, str]
```

Returns metadata for a given feature name: cost class, needs, registered
aliases, plus core33 documentation fields (`definition`, `min_length`,
`nan_when`) — the same source `tools/gen_feature_docs.py` builds
[Feature reference](features.md) from.

---

## Hardware Auto-Tuning

### tune

```python skip
tune(
    shapes: Sequence[tuple[int, int]] = ((1000, 500),),
    budget_s: float = 10.0,
) -> dict[str, Any]
```

Microbenchmarks execution variants on current hardware and caches optimal execution parameters locally. Pool selection is recorded for forward compatibility.

---

## Threading & Runtime Controls

- Scheduling is Rayon: `n_jobs=None` uses the shared global pool
  (honors `RAYON_NUM_THREADS=N`); an explicit `n_jobs` selects a cached
  per-count pool (no per-call construction cost since 0.8.0).
- Expect scaling to stop near the physical core count (P-cores on hybrid
  laptops); see [Performance](performance.md) and
  `docs/internal/thread_scaling.md` for the analysis.
- `KYMORA_POOL` (`spin`/`rayon`) is currently **read by nothing** — the
  persistent spin-pool prototype was removed from main to
  `experiment/spin-pool` (see `docs/ROADMAP.md`; revival is gated on
  docs/internal/arch.md Z6). Treat any `tune()` pool recommendation as provisional until
  the backend lands.
