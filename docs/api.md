# API reference

Four public functions. That is the whole surface, and it is frozen for 1.0.

```python
import tsxtractor

tsxtractor.__version__      # e.g. "0.2.0"
```

The package ships type stubs and a `py.typed` marker, so mypy and IDEs see real
signatures rather than `Any`.

## extract_features

```python
extract_features(X: np.ndarray | Sequence[np.ndarray]) -> np.ndarray
```

Extract all 33 features for every series in a batch.

**Parameters**

- `X` — either a 2D C-contiguous float64 array of shape `(n_series, length)`, or
  a sequence of 1D C-contiguous float64 arrays whose lengths may differ.

**Returns** a `(n_series, 33)` float64 array. Column `i` corresponds to
`feature_names()[i]`.

**Raises** `ValueError` for structural problems (no series, a zero-length
series, a non-contiguous buffer) and `TypeError` for a wrong dtype or shape. See
the [NaN policy](nan-policy.md) for what is a value rather than an error.

```python
X = np.random.default_rng(0).standard_normal((1000, 500))
feats = tsxtractor.extract_features(X)          # (1000, 33)

ragged = [np.arange(50.0), np.arange(120.0)]
feats = tsxtractor.extract_features(ragged)     # (2, 33)
```

Both input forms run the same per-series code; only the input handling differs,
so a 2D array and the equivalent list of rows give bit-identical output.

## extract_features_df

```python
extract_features_df(X: np.ndarray | Sequence[np.ndarray]) -> pd.DataFrame
```

Same computation as `extract_features`, wrapped in a `pandas.DataFrame` whose
columns are `feature_names()` and whose index is a plain `RangeIndex`.

Requires pandas (`pip install "tsxtractor[pandas]"`); raises `ImportError` with
that instruction if it is missing. Everything else behaves identically to
`extract_features`.

```python
df = tsxtractor.extract_features_df(X)
df[["mean", "std", "spectral_entropy"]].head()
```

## sliding_features

```python
sliding_features(x: np.ndarray, window: int, stride: int = 1) -> np.ndarray
```

Feature matrix over rolling windows of a single series — the way to get
parallelism out of one long recording rather than many short ones.

**Parameters**

- `x` — 1D C-contiguous float64 array.
- `window` — window length in samples; must satisfy `1 <= window <= len(x)`.
- `stride` — step between window starts; must be `>= 1`. Defaults to 1.

**Returns** a `(n_windows, 33)` float64 array where
`n_windows = (len(x) - window) // stride + 1`.

Windows are borrowed slices of your buffer, so no window data is copied.

```python
x = np.random.default_rng(0).standard_normal(10_000)
feats = tsxtractor.sliding_features(x, window=256, stride=64)
feats.shape        # (153, 33)
```

`window > len(x)`, `window < 1`, and `stride < 1` all raise `ValueError` rather
than returning an empty array — a silently empty result is a harder bug to find
than an exception.

## feature_names

```python
feature_names() -> list[str]
```

The output column names, in column order.

**This order is a stability guarantee.** Column `i` means the same feature for
every release within a major version. Reordering, renaming, or removing a name is
a major-version change; appending a new feature at the end is a minor one.

```python
names = tsxtractor.feature_names()
len(names)      # 33
names[:3]       # ['mean', 'std', 'var']
```

## Threading

The Rust core releases the GIL for the whole compute region and uses the default
rayon pool, sized to your logical cores. Cap it with the standard rayon
environment variable:

```bash
RAYON_NUM_THREADS=4 python my_pipeline.py
```

Calls hold no state between invocations — there is no thread pool to warm, no
object to reuse, and nothing to clean up.
