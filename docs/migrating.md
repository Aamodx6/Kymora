# Migrating

## Migrating from pre-0.7.0 releases

0.7.0 consolidated the project under Kymora and deleted previous development names outright —
there are no shims. Numerics, feature names/order, and the NaN/error
contracts are unchanged — only names moved:

| Before (≤ 0.6.0) | After (≥ 0.7.0) |
|---|---|
| `pip install [old-dist]` | `pip install kymora` |
| `import [old-module] as tsx` | `import kymora as km` |
| `[old-module]._core` | `kymora._core` |
| `TsxSelector` | `KymoraSelector` (`TsxSelector` still works as an alias) |
| `TSX_WISDOM` / `TSX_POOL` | `KYMORA_WISDOM` / `KYMORA_POOL` |
| `~/.cache/[old-cache]/wisdom.json` | `~/.cache/kymora/wisdom.json` (re-run `tune()`) |

`import kymora` is the only supported spelling. Old benchmark rows in historical archives still carry previous library IDs — that is data, not a bug; all current runs record `kymora`.

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

## Migrating from TSFEL

### The shape of the change

`TSFEL` computes features from 1D signals or DataFrames using modular configuration dictionaries (`get_features_by_domain()`), often taking several seconds per batch. `kymora` processes entire 2D matrices across all CPU cores with no copy of the input in sub-milliseconds:

```python skip
# TSFEL (serial or multi-domain extraction)
import tsfel
cfg = tsfel.get_features_by_domain()
features = tsfel.time_series_features_extractor(cfg, signal_1d, fs=100)

# kymora (multi-core batch extraction)
import kymora
features_df = kymora.extract_features_df(batch_2d)  # (n_series, 33)
```

### Feature-name mapping

13 features in TSFEL have direct mathematical equivalents in Kymora:

| Kymora | TSFEL feature | Mathematical Definition | Parity Agreement |
|---|---|---|---|
| `mean` | `Mean` | Arithmetic mean | EXACT (rel err ≤ 1e-9) |
| `std` | `Standard deviation` | Population standard deviation (ddof=0) | EXACT |
| `var` | `Variance` | Population variance (ddof=0) | EXACT |
| `min` | `Min` | Minimum value | EXACT |
| `max` | `Max` | Maximum value | EXACT |
| `median` | `Median` | 50th percentile | EXACT |
| `skewness` | `Skewness` | Biased Fisher-Pearson skewness | EXACT |
| `kurtosis` | `Kurtosis` | Excess Fisher kurtosis | EXACT |
| `abs_energy` | `Absolute energy` | $\sum x_i^2$ | EXACT |
| `root_mean_square` | `Root mean square` | $\sqrt{\frac{1}{N}\sum x_i^2}$ | EXACT |
| `mean_abs_change` | `Mean absolute diff` | $\frac{1}{N-1}\sum \|x_i - x_{i-1}\|$ | EXACT |
| `mean_change` | `Mean diff` | $\frac{1}{N-1}\sum (x_i - x_{i-1})$ | EXACT |
| `zero_crossings` | `Zero crossing rate` | Strict zero crossings count | EXACT |

Other TSFEL spectral features have clean Kymora equivalents:
- TSFEL `Spectral centroid` $\to$ Kymora `spectral_centroid`
- TSFEL `Fundamental frequency` $\to$ Kymora `dominant_frequency`
- TSFEL `Spectral entropy` $\to$ Kymora `spectral_entropy`

---

## Migrating from catch22

### The shape of the change

`pycatch22` runs a C-based pipeline over one time series at a time, requiring explicit Python loops or external multiprocessing pools. `kymora` ingests 2D NumPy matrices natively, distributing work across CPU cores with Rayon's work-stealing scheduler:

```python skip
# pycatch22 (per-series loop)
import pycatch22
features = [pycatch22.catch22_all(row.tolist())["values"] for row in X]

# kymora (batch multi-core)
import kymora
features = kymora.extract_features(X)  # (n_series, 33)
```

### Why catch22 features differ

`catch22` selected 22 features from `hctsa` designed specifically for classification diversity across the UCR archive, many of which use non-standard heuristic parameters or complex nonlinear optimization fits (e.g. `DN_HistogramMode_5`, `CO_Embed2_Dist_tau_d_expfit`, `SB_TransitionMatrix_3ac_sumdiagcov`).

None of the 22 features in catch22 shares an exact mathematical definition with standard statistical moments. However, Kymora provides high-signal standard alternatives for each domain:

| catch22 concept | catch22 feature | Kymora equivalent | Notes |
|---|---|---|---|
| Linear autocorrelation | `CO_FirstMin_ac`, `CO_trev_1_num` | `autocorr_lag_1`, `autocorr_lag_2`, `autocorr_lag_5`, `autocorr_lag_10` | Direct lag autocorrelations |
| Information & Entropy | `IN_AutoMutualInfoStats_40_gaussian_fmmi` | `permutation_entropy`, `spectral_entropy` | Permutation order 3 & FFT power entropy |
| Distribution & Outliers | `DN_OutlierInclude_p_001_mdrmd`, `DN_Mean` | `mean`, `std`, `skewness`, `kurtosis`, `quantile_*` | Centered moments & quantiles |
| Scaling & Crossings | `SB_BinaryStats_diff_longstretch0` | `longest_strike_above_mean`, `longest_strike_below_mean`, `zero_crossings`, `mean_crossings` | Run length and crossing statistics |
| Dynamics & Trend | `FC_LocalSimple_mean1_tauresrat` | `trend_slope`, `trend_r2`, `cid_ce` | Regression slope, fit quality, complexity |

