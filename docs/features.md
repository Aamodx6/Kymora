# Feature Reference

The core feature engine implements 33 canonical features in six categories. The ordering below represents the frozen column layout of `extract_features()` output and `feature_names()`.

Notation: `x` represents one time series of length `n`, `m` is its sample mean, `s` is its population standard deviation (`ddof=0`), and `d = diff(x)`.

---

## Numerical Conventions

- **Moments**: Population moments (`ddof=0`), matching `numpy.var(x)`.
- **Quantiles**: Evaluated using $O(n)$ multi-selection with linear interpolation matching NumPy defaults.
- **Skewness & Kurtosis**: Evaluated following `scipy.stats` with `bias=True`. Kurtosis is excess kurtosis (Fisher definition).
- **Constant Series Detection**: Constant series are identified analytically with zero variance, avoiding floating-point rounding noise.
- **Missing Value Semantics**: Strict NaN propagation guarantees that any NaN element produces NaNs across the series output. See the [NaN policy](nan-policy.md).

---

## Canonical Core33 Feature Table

### Statistical Moments & Quantiles

| # | Feature | Definition | Undefined Condition |
|---:|---|---|---|
| 0 | `mean` | `sum(x) / n` | never |
| 1 | `std` | `sqrt(var)` | never |
| 2 | `var` | `sum((x - m)^2) / n` | never |
| 3 | `min` | Smallest value | never |
| 4 | `max` | Largest value | never |
| 5 | `median` | 50th percentile with linear interpolation | never |
| 6 | `quantile_10` | 10th percentile | never |
| 7 | `quantile_25` | 25th percentile | never |
| 8 | `quantile_75` | 75th percentile | never |
| 9 | `quantile_90` | 90th percentile | never |
| 10 | `skewness` | Third standardised moment (`bias=True`) | `s == 0` |
| 11 | `kurtosis` | Fourth standardised moment minus 3 (`bias=True`) | `s == 0` |
| 12 | `abs_energy` | `sum(x^2)` | never |
| 13 | `root_mean_square` | `sqrt(mean(x^2))` | never |

### Change & Complexity

| # | Feature | Definition | Undefined Condition |
|---:|---|---|---|
| 14 | `mean_abs_change` | `mean(abs(d))` | `n < 2` |
| 15 | `mean_change` | `(x[-1] - x[0]) / (n - 1)` | `n < 2` |
| 16 | `cid_ce` | Complexity estimate on z-normalized series: `sqrt(sum((d / s)^2))` | `n < 2` |
| 17 | `mean_second_derivative_central` | `sum(x[i+1] - 2*x[i] + x[i-1]) / (2 * (n - 2))` | `n < 3` |

### Counts & Run Lengths

| # | Feature | Definition | Undefined Condition |
|---:|---|---|---|
| 18 | `zero_crossings` | Number of sign transitions across zero | never |
| 19 | `mean_crossings` | Number of sign transitions across the mean `m` | never |
| 20 | `number_of_peaks` | Count of points strictly exceeding 3 neighbors on each side | never (0 when `n <= 6`) |
| 21 | `longest_strike_above_mean` | Longest run of consecutive samples `x[i] > m` | never |
| 22 | `longest_strike_below_mean` | Longest run of consecutive samples `x[i] < m` | never |

### Temporal & Autocorrelation

| # | Feature | Definition | Undefined Condition |
|---:|---|---|---|
| 23 | `autocorr_lag_1` | Normalized autocorrelation at lag 1 | `n <= 1` or constant |
| 24 | `autocorr_lag_2` | Normalized autocorrelation at lag 2 | `n <= 2` or constant |
| 25 | `autocorr_lag_5` | Normalized autocorrelation at lag 5 | `n <= 5` or constant |
| 26 | `autocorr_lag_10` | Normalized autocorrelation at lag 10 | `n <= 10` or constant |
| 27 | `trend_slope` | Ordinary least squares slope against sample indices `0..n-1` | `n < 2` |
| 28 | `trend_r2` | Coefficient of determination ($R^2$) of linear trend | `n < 2` or constant |

### Non-Linear & Ordinal Dynamics

| # | Feature | Definition | Undefined Condition |
|---:|---|---|---|
| 29 | `permutation_entropy` | Bandt-Pompe permutation entropy (order 3), normalized to `[0, 1]` | `n < 3` |

### Spectral Frequency Dynamics

Computed from the real FFT with sample spacing 1. Frequencies reside in `(0, 0.5]`. The zero-frequency DC component is excluded.

| # | Feature | Definition | Undefined Condition |
|---:|---|---|---|
| 30 | `dominant_frequency` | Frequency of maximum positive power spectral density | `n < 2`, constant, or zero total power |
| 31 | `spectral_centroid` | Power-weighted spectral center of mass | as above |
| 32 | `spectral_entropy` | Normalized Shannon entropy of the power spectrum | as above |

---

## Multi-View Transform Engine

Rather than hand-crafting transformations, `tsxtract` provides a multi-view extraction pipeline across 8 mathematical domain representations:

- `raw`: Original time-series observations.
- `diff`: First differences: $\Delta x_t = x_t - x_{t-1}$.
- `diff2`: Second differences: $\Delta^2 x_t = \Delta x_t - \Delta x_{t-1}$.
- `detrend`: Linear trend residuals: $x_t - (\alpha + \beta t)$.
- `znorm`: Standardized series: $(x_t - \mu) / \sigma$.
- `abs`: Rectified magnitude series: $|x_t|$.
- `logret`: Log returns: $\ln(x_t / x_{t-1})$ (positive inputs).
- `rank`: Rank-normalized uniform representation: $\text{rank}(x_t) / n$.

### Mathematical Invariance Pruning

Computing every feature across every view leads to degenerate or redundant calculations (e.g., the mean of a z-normalized series is identically 0, and the standard deviation is identically 1).

`tsxtract` tracks transformation invariances per feature:
- `Invariances::SHIFT`: Features invariant under translation $x \to x + c$ (e.g., `std`, `var`, `mean_abs_change`).
- `Invariances::SCALE`: Features invariant under scaling $x \to c \cdot x$ (e.g., `zero_crossings`, `autocorr`).
- `Invariances::MONOTONE`: Features invariant under monotonic rank transforms (e.g., `permutation_entropy`).

When executing multi-view plans, invariant feature evaluations are automatically pruned, saving compute cycles and eliminating uninformative zero-variance columns.

---

## Multichannel & Cross-Channel Extraction

For multidimensional time-series batches of shape `(n_samples, n_channels, length)`, `extract_features_mc` calculates:

1. **Per-Channel Baselines**: All active features extracted independently per channel (e.g. `ch0__mean`, `ch1__std`).
2. **Pairwise Interaction Metrics**:
   - `cross_corr_peak__ch{i}_ch{j}`: Maximum cross-correlation amplitude across all lags.
   - `cross_corr_lag__ch{i}_ch{j}`: Temporal offset (lag) at maximum cross-correlation peak.
   - `cross_cov__ch{i}_ch{j}`: Zero-lag sample cross-covariance.
   - `cross_corr_coef__ch{i}_ch{j}`: Zero-lag Pearson cross-correlation coefficient.
3. **Global Fleet Dynamics**:
   - `cross__mean_abs_corr`: Average absolute correlation across all channel pairs.
   - `cross__max_abs_corr`: Maximum correlation magnitude across the channel fleet.
   - `cross__eigen_spread`: Ratio of dominant eigenvalue to trace of the covariance matrix.
   - `cross__coherence_mean`: Mean frequency-domain spectral coherence across channels.
