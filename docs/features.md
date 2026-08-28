# Feature reference

33 features in six groups. The order below **is** the column order of
`extract_features()` output and of `feature_names()`, and that order is a
stability guarantee within a major version.

Notation: `x` is one series of length `n`, `m` its mean, `s` its population
standard deviation (`ddof=0`), `d = diff(x)`.

## Conventions

- **Moments are population moments** (`ddof=0`), matching `numpy.var(x)` rather
  than pandas' default sample variance.
- **Quantiles** use numpy's default linear interpolation.
- **Skewness and kurtosis** follow `scipy.stats` with `bias=True`; kurtosis is
  Fisher (excess), so a Gaussian sits near 0, not 3.
- **Exactly-constant series** are detected exactly and their variance forced to
  0, so standard-deviation-guarded features do not emit float-rounding noise
  (naive summation leaves a variance around 1e-31 instead of zero).
- The **undefined** column says when a feature is NaN on its own; separately,
  any NaN in the series makes every feature NaN. See the
  [NaN policy](nan-policy.md).

## Stats

| # | Feature | Definition | Undefined when |
|---:|---|---|---|
| 0 | `mean` | `sum(x) / n` | never |
| 1 | `std` | `sqrt(var)` | never |
| 2 | `var` | `sum((x - m)^2) / n` | never |
| 3 | `min` | smallest value | never |
| 4 | `max` | largest value | never |
| 5 | `median` | 50th percentile, linear interpolation | never |
| 6 | `quantile_10` | 10th percentile | never |
| 7 | `quantile_25` | 25th percentile | never |
| 8 | `quantile_75` | 75th percentile | never |
| 9 | `quantile_90` | 90th percentile | never |
| 10 | `skewness` | third standardised moment, `bias=True` | `s == 0` (constant series) |
| 11 | `kurtosis` | fourth standardised moment minus 3, `bias=True` | `s == 0` |
| 12 | `abs_energy` | `sum(x^2)` | never |
| 13 | `root_mean_square` | `sqrt(mean(x^2))` | never |

## Change

| # | Feature | Definition | Undefined when |
|---:|---|---|---|
| 14 | `mean_abs_change` | `mean(abs(d))` | `n < 2` |
| 15 | `mean_change` | `(x[-1] - x[0]) / (n - 1)` | `n < 2` |
| 16 | `cid_ce` | complexity estimate on the z-normalised series: `sqrt(sum((d / s)^2))`; exactly 0 for a constant series | `n < 2` |
| 17 | `mean_second_derivative_central` | `sum(x[i+1] - 2*x[i] + x[i-1]) / (2 * (n - 2))` | `n < 3` |

## Counts

Counts are returned as float64 like every other column.

| # | Feature | Definition | Undefined when |
|---:|---|---|---|
| 18 | `zero_crossings` | number of `i` where `(x[i] > 0) != (x[i+1] > 0)` | never |
| 19 | `mean_crossings` | same test against `m` instead of 0 | never |
| 20 | `number_of_peaks` | count of `i` that strictly exceed all 3 neighbours on each side (support 3) | never (0 when `n <= 6`) |
| 21 | `longest_strike_above_mean` | longest run of consecutive `x[i] > m` | never |
| 22 | `longest_strike_below_mean` | longest run of consecutive `x[i] < m` | never |

!!! note "Values sitting exactly on the mean"
    `mean_crossings` and the strike features compare against the mean computed
    by this library. For series with many values exactly at the mean (integer
    data, for instance), a reference implementation using a different summation
    order can legitimately land on a different count. This is why the test suite
    feeds the library's own mean into its reference.

## Correlation

| # | Feature | Definition | Undefined when |
|---:|---|---|---|
| 23 | `autocorr_lag_1` | `sum((x[:n-k] - m) * (x[k:] - m)) / ((n - k) * var)`, `k = 1` | `n <= k` or constant series |
| 24 | `autocorr_lag_2` | as above, `k = 2` | `n <= 2` or constant |
| 25 | `autocorr_lag_5` | as above, `k = 5` | `n <= 5` or constant |
| 26 | `autocorr_lag_10` | as above, `k = 10` | `n <= 10` or constant |
| 27 | `trend_slope` | OLS slope of `x` against `0..n-1`; exactly 0 for a constant series | `n < 2` |
| 28 | `trend_r2` | r-squared of that fit | `n < 2`, or constant series (no variance to explain) |

## Entropy

| # | Feature | Definition | Undefined when |
|---:|---|---|---|
| 29 | `permutation_entropy` | Bandt-Pompe permutation entropy, order 3, Shannon entropy of the ordinal-pattern distribution normalised by `log(6)` so the range is `[0, 1]`. Ties break with `<=`, consistently between the Rust core and the reference. | `n < 3` |

## Spectral

Computed from the real FFT with sample spacing 1, so frequencies are in cycles
per sample and land in `(0, 0.5]`. The DC bin is excluded — otherwise the series
mean would dominate every spectral feature — and only positive-frequency bins
are used.

| # | Feature | Definition | Undefined when |
|---:|---|---|---|
| 30 | `dominant_frequency` | frequency of the highest-power positive bin | `n < 2`, constant series, or zero total power |
| 31 | `spectral_centroid` | power-weighted mean frequency | as above |
| 32 | `spectral_entropy` | Shannon entropy of the normalised power spectrum, divided by `log(n_bins)`; exactly 0 when there is only one bin | as above |

## Why 33 and not 300

Published PCA analyses of the large feature banks find heavy redundancy — a
handful of components explain most of the variance across `tsfresh`'s 1 558 or
`TSFEL`'s ~390 features. A smaller, deliberately chosen set costs little in
downstream model quality while being far cheaper to compute and much easier to
prove correct feature by feature. The closed set is the product decision, not a
gap; see [when not to use this](index.md#when-not-to-use-this).
