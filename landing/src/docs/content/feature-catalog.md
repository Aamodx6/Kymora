---
title: "Feature Catalog"
description: "Mathematical definitions, computational complexity, and conventions for all 33 curated time-series features."
order: 11
section: "Reference"
---

All 33 features in output column order, grouped by category. Column `i` of every output matrix equals the `i`-th row below, matching `feature_names()` and the interactive feature table below.

```python
import tsxtract
names = tsxtract.feature_names()
print(len(names))
print(names[14:18])
```

```text
33
['mean_abs_change', 'mean_change', 'cid_ce', 'mean_second_derivative_central']
```

Shared conventions across the bank:

- **Population moments:** variance and standard deviation use `ddof=0`, matching NumPy defaults.
- **Quantile interpolation:** linear interpolation matching the NumPy default.
- **Shape statistics:** skewness and kurtosis follow `scipy.stats` with `bias=True`; kurtosis is Fisher (excess), so Gaussian series score near 0.
- **Spectral frame:** positive non-DC bins only, sample spacing 1, frequencies in cycles/sample over `(0, 0.5]`.
- **Counts as floats:** integer counts are returned as float64 to keep the matrix homogeneous.

## Stats (columns 0–13)

| Name | Category | Description | Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `mean` | Stats | `sum(x) / n` | `O(n)` | Pass-1 accumulation; defined for every non-empty series |
| `std` | Stats | `sqrt(var)` | `O(n)` | Population (`ddof=0`); exactly `0.0` on constant series |
| `var` | Stats | `sum((x - mean)^2) / n` | `O(n)` | Population (`ddof=0`); exact `0.0` on constant series |
| `min` | Stats | `min(x)` | `O(n)` | Tracked during pass 1, outside the selection set |
| `max` | Stats | `max(x)` | `O(n)` | Tracked during pass 1, outside the selection set |
| `median` | Stats | 50th percentile | `O(n)` | Linear interpolation via selection, no full sort |
| `quantile_10` | Stats | 10th percentile | `O(n)` | Linear interpolation |
| `quantile_25` | Stats | 25th percentile (Q1) | `O(n)` | Linear interpolation |
| `quantile_75` | Stats | 75th percentile (Q3) | `O(n)` | Linear interpolation |
| `quantile_90` | Stats | 90th percentile | `O(n)` | Linear interpolation |
| `skewness` | Stats | `m3 / std^3` | `O(n)` | NaN when `std == 0`; matches `scipy.stats.skew(bias=True)` |
| `kurtosis` | Stats | `m4 / var^2 - 3` | `O(n)` | NaN when `std == 0`; Fisher excess kurtosis |
| `abs_energy` | Stats | `sum(x^2)` | `O(n)` | Total signal energy |
| `root_mean_square` | Stats | `sqrt(mean(x^2))` | `O(n)` | Quadratic mean amplitude |

## Change (columns 14–17)

| Name | Category | Description | Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `mean_abs_change` | Change | `mean(\|x[i+1] - x[i]\|)` | `O(n)` | NaN when `n < 2` |
| `mean_change` | Change | `(x[n-1] - x[0]) / (n - 1)` | `O(1)` | Telescoping; NaN when `n < 2` |
| `cid_ce` | Change | `sqrt(sum(((x[i+1] - x[i]) / std)^2))` | `O(n)` | Z-normalized complexity; exactly `0.0` on constant series; NaN when `n < 2` |
| `mean_second_derivative_central` | Change | `sum(x[i+1] - 2x[i] + x[i-1]) / (2(n - 2))` | `O(n)` | Central differences over 3-windows; NaN when `n < 3` |

## Counts (columns 18–22)

| Name | Category | Description | Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `zero_crossings` | Counts | Sign changes across `0` between consecutive samples | `O(n)` | Float64 count; never NaN on valid input |
| `mean_crossings` | Counts | Sign changes across the series mean | `O(n)` | Float64 count; never NaN on valid input |
| `number_of_peaks` | Counts | Samples strictly exceeding 3 neighbors each side | `O(n)` | Branchless comparisons; `0` when `n <= 6` |
| `longest_strike_above_mean` | Counts | Longest run with `x[i] > mean` | `O(n)` | Float64 count; never NaN on valid input |
| `longest_strike_below_mean` | Counts | Longest run with `x[i] < mean` | `O(n)` | Float64 count; never NaN on valid input |

## Correlation (columns 23–28)

| Name | Category | Description | Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `autocorr_lag_1` | Correlation | Normalized sample autocorrelation, lag 1 | `O(n)` | NaN when `n <= 1` or series is constant |
| `autocorr_lag_2` | Correlation | Normalized sample autocorrelation, lag 2 | `O(n)` | NaN when `n <= 2` or series is constant |
| `autocorr_lag_5` | Correlation | Normalized sample autocorrelation, lag 5 | `O(n)` | NaN when `n <= 5` or series is constant |
| `autocorr_lag_10` | Correlation | Normalized sample autocorrelation, lag 10 | `O(n)` | NaN when `n <= 10` or series is constant |
| `trend_slope` | Correlation | OLS slope against time index `0..n-1` | `O(n)` | Exactly `0.0` on constant series; NaN when `n < 2` |
| `trend_r2` | Correlation | Coefficient of determination of the linear trend | `O(n)` | NaN when `n < 2` or series is constant |

## Entropy (column 29)

| Name | Category | Description | Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `permutation_entropy` | Entropy | Bandt-Pompe order 3, normalized by `log(6)` to `[0, 1]` | `O(n)` | Branchless ordinal-pattern table; NaN when `n < 3`; `0.0` on constant series |

## Spectral (columns 30–32)

| Name | Category | Description | Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `dominant_frequency` | Spectral | Frequency of strongest positive power bin | `O(n log n)` | Cycles/sample in `(0, 0.5]`; NaN when `n < 2`, constant, or zero total power |
| `spectral_centroid` | Spectral | `sum(f * P(f)) / sum(P(f))` over positive non-DC bins | `O(n log n)` | Real FFT via `realfft`; NaN under the same conditions |
| `spectral_entropy` | Spectral | `-sum(p * log(p)) / log(n_bins)` of normalized power | `O(n log n)` | Exactly `0` for a single active bin; NaN under the same conditions |

> [!NOTE]
> Definitions and undefined cases above mirror the library's feature registry and `tests/test_nan_policy.py`. Any behavior change to the undefined sets is a major-version change per `CONTRIBUTING.md`.

## See also

From definitions to usage and guarantees:

- [Core Concepts](/docs/core-concepts) — NaN contract and ordering guarantee in prose.
- [API Reference](/docs/api-reference) — signatures returning these columns.
- [Selecting Feature Subsets](/docs/selecting-features) — prune by group or importance.
