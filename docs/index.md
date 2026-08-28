# tsxtractor

Batch time-series feature extraction for Python, with a Rust core.

33 curated statistical, temporal, and spectral features, computed across a whole
batch of series at once. The Rust core takes zero-copy views of your numpy
buffers, releases the GIL, and parallelises across the *series* dimension with
[rayon](https://github.com/rayon-rs/rayon).

```bash
pip install tsxtractor
```

```python
import numpy as np, tsxtractor

X = np.random.randn(100_000, 500)
feats = tsxtractor.extract_features(X)   # (100_000, 33) float64
df = tsxtractor.extract_features_df(X)   # same, labeled columns
```

## Where the speed comes from

Parallelism is across **series**, not across the feature computations within one
series. Extracting from 100 000 series scales close to linearly with core count;
extracting from *one* series shows no speedup versus a good numpy
implementation, and is not meant to. For a single long series, use
[`sliding_features`](api.md#sliding_features), which parallelises over windows.

## When not to use this

- **You need exhaustive coverage.** `tsfresh` computes up to 1 558 features,
  `TSFEL` around 390. This library computes 33, chosen to stay low-redundancy.
- **You need custom or parameterised features.** The set is intentionally
  closed; there is no plugin hook.
- **You are in R, Julia, or MATLAB.** Use `catch22`, which has bindings for all
  three.
- **Your workload is one short series at a time.** The parallelism has nothing
  to work with.

## What is guaranteed

| Surface | Guarantee |
|---|---|
| `feature_names()` order and length | Stable within a major version |
| Output dtype | `float64`, always |
| [NaN behaviour](nan-policy.md) | Documented and tested; changes are breaking |
| No Rust panic crosses into Python | Enforced by property-based tests |

Correctness is checked feature by feature against numpy/scipy references — see
the [validation report](validation.md).
