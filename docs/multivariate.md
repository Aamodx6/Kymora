# Multichannel extraction

`extract_features_mc` handles multi-sensor recordings: one sample holds
`C` synchronous channels of a shared length.

## Shapes

| Input | Output | Notes |
|---|---|---|
| 3D `(n_samples, n_channels, length)`, C-contiguous float64 | `(n_samples, C * n_plan + n_cross)` | Zero-copy borrow like the 2D path |
| List of 2D `(C, length_i)` float64 | same, per-sample widths | Ragged lengths across samples; channel count must agree |

`n_plan` is the profile/feature count; `n_cross` is `pairs * 4 + 4` when
`cross=True` and `C >= 2` (else 0). Pairs run `(0,1), (0,2), …` capped by
`max_pairs` (default 8).

## Column order and names

Per-channel blocks first, then cross columns — exactly
`feature_names_mc(n_channels, ...)`:

- `ch{c}__{feature}` for channel `c`, features in plan order.
- `cross_corr_peak__ch{i}_ch{j}`, `cross_corr_lag__ch{i}_ch{j}`,
  `cross_cov__ch{i}_ch{j}`, `cross_corr_coef__ch{i}_ch{j}` per pair.
- `cross__mean_abs_corr`, `cross__max_abs_corr`, `cross__eigen_spread`,
  `cross__coherence_mean` summaries.

`extract_features_mc_df` returns the same matrix labeled; its columns are
asserted equal to `feature_names_mc(...)` in `tests/test_multichannel.py`.

```python
import numpy as np
import kymora

X = np.random.default_rng(0).standard_normal((100, 4, 1000))
df = kymora.extract_features_mc_df(X, cross=True)

# Ragged: different recording lengths per sample
ragged = [np.random.default_rng(i).standard_normal((4, n)) for i, n in enumerate([500, 1000, 750])]
out = kymora.extract_features_mc(ragged)
```

## Notes

- Per-channel values are bit-identical to running `extract_features` on
  that channel alone (tested).
- Only float64 input is supported; float32 and non-raw views raise a clear
  `ValueError` (same limitation as the batch f32 path).
- `nan_policy="raise"` reports `sample {s} channel {c}`; propagate follows
  the standard [NaN contract](numerics.md) per channel.
- Non-contiguous input follows the global rule (`contiguous="error"` by
  default, `"copy"` opt-in).
