# Migrating

## Migrating from tsxtract (pre-0.7.0 names)

0.7.0 renamed the project to Kymora and deleted every old name outright —
there are no shims. Numerics, feature names/order, and the NaN/error
contracts are unchanged — only names moved:

| Before (≤ 0.6.0) | After (≥ 0.7.0) |
|---|---|
| `pip install tsxtract-rs` | `pip install kymora` |
| `import tsxtract as tsx` | `import kymora as km` |
| `tsxtract._core` | `kymora._core` |
| `TsxSelector` | `KymoraSelector` (`TsxSelector` still works as an alias) |
| `TSXTRACT_WISDOM` / `TSXTRACT_POOL` | `KYMORA_WISDOM` / `KYMORA_POOL` |
| `~/.cache/tsxtract/wisdom.json` | `~/.cache/kymora/wisdom.json` (re-run `tune()`) |

`import kymora` is the only spelling — `tsxtract` and `tsxtractor` were
deleted with no re-export. Old benchmark
rows and reports still carry the `tsxtract` library id — that is data, not
a bug; new runs record `kymora`.

## Migrating from tsfresh

## The shape of the change

`tsfresh` takes a long-format DataFrame and returns a wide one. This library
takes a numpy matrix (or a list of arrays) and returns a matrix.

```python skip
# tsfresh (requires the tsfresh package and your own long-format data —
# not executed by tools/check_snippets.py)
from tsfresh import extract_features
from tsfresh.feature_extraction import EfficientFCParameters

long_df = pd.DataFrame({"id": ids, "time": times, "value": values})
features = extract_features(
    long_df, column_id="id", column_sort="time",
    default_fc_parameters=EfficientFCParameters(),
)

# kymora
import kymora
X = values.reshape(n_series, n_steps)          # already sorted per series
features = kymora.extract_features_df(X)   # DataFrame, 33 columns
```

If your data is already long-format and you want to keep it that way:

```python
import numpy as np
import pandas as pd
import kymora

rng = np.random.default_rng(0)
n_series, n_steps = 4, 50
long_df = pd.DataFrame({
    "id": np.repeat(np.arange(n_series), n_steps),
    "time": np.tile(np.arange(n_steps), n_series),
    "value": rng.standard_normal(n_series * n_steps),
})
groups = long_df.sort_values("time").groupby("id")["value"]
series = [g.to_numpy(dtype="float64") for _, g in groups]
features = kymora.extract_features_df(series)   # ragged input is fine
features.index = list(groups.groups)               # keep the original ids
```

Sorting is your responsibility here: there is no `column_sort` equivalent,
because the input is an array whose order is already meaningful.

## Feature-name mapping

Many features have a direct `tsfresh` counterpart under a different name:

| kymora | tsfresh |
|---|---|
| `mean`, `std`, `var`, `median`, `min`, `max` | `mean`, `standard_deviation`, `variance`, `median`, `minimum`, `maximum` |
| `quantile_10` ... `quantile_90` | `quantile__q_0.1` ... `quantile__q_0.9` |
| `skewness`, `kurtosis` | `skewness`, `kurtosis` |
| `abs_energy` | `abs_energy` |
| `root_mean_square` | `root_mean_square` |
| `mean_abs_change` | `mean_abs_change` |
| `mean_change` | `mean_change` |
| `cid_ce` | `cid_ce__normalize_True` |
| `mean_second_derivative_central` | `mean_second_derivative_central` |
| `zero_crossings` | `number_crossing_m__m_0` |
| `mean_crossings` | no exact equivalent (crossings of the series mean) |
| `number_of_peaks` | `number_peaks__n_3` |
| `longest_strike_above_mean` / `_below_mean` | same names |
| `autocorr_lag_{1,2,5,10}` | `autocorrelation__lag_{1,2,5,10}` |
| `trend_slope`, `trend_r2` | `linear_trend__attr_"slope"`, `linear_trend__attr_"rvalue"` (squared) |
| `permutation_entropy` | `permutation_entropy__dimension_3__tau_1` (normalisation differs) |
| `spectral_entropy` | closest: `fourier_entropy__bins_*` (definition differs) |
| `dominant_frequency`, `spectral_centroid` | no direct equivalent |

Values will not match `tsfresh` bit for bit where conventions differ — notably
permutation entropy (normalised to `[0, 1]` here) and the spectral features (DC
bin excluded, sample spacing 1). Treat them as the same *concept*, not as
drop-in replacements inside a trained model.

!!! warning "Retrain, do not transplant"
    A model trained on `tsfresh` columns cannot be fed these columns even where
    the names line up. Extract features fresh and retrain.

## What has no equivalent here

`tsfresh`'s parameterised families — `agg_linear_trend`, `change_quantiles`,
`fft_coefficient` at arbitrary indices, `cwt_coefficients`, and the rest of the
long tail — are not implemented and will not be. The feature set is closed by
design; see [when not to use this](index.md#when-not-to-use-this). If your model
depends on those, `tsfresh` is the right tool and this library is not.

## Behaviour differences worth knowing

| | tsfresh | kymora |
|---|---|---|
| NaN in a series | varies per feature; some impute, some return NaN | every feature for that series is NaN, always |
| Empty series | dropped or NaN-filled | `ValueError` |
| Input dtype | coerced | float64 required, `TypeError` otherwise |
| Parallelism | multiprocessing over series, optional | threads over series, always on, GIL released |
| Dependencies | pandas, scipy, statsmodels, tqdm, ... | numpy only |
