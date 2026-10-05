# Feature mapping: Kymora core33 ↔ catch22 / TSFEL / tsfresh

Source of truth: `benchmarks/agreement/feature_map.json` (frozen Phase B1
parity evidence, 25 distributions). This table is the equal-feature
definition mapping used by `benchmarks/suites/equal_feature.py`.

Every row was re-verified numerically before timing
(`parity.json` in the equal-feature artifact dir): agreement classes are
**EXACT** (max rel err ≤ 1e-9) or **CLOSE** (≤ 1e-5). Features whose
definitions differ are excluded from the equal-feature timing and the
reason is listed below.

## Shared set per library

| Library | Agreed features | Notes |
|---|---:|---|
| TSFEL | 13 | `get_features_by_domain()` filtered to the listed functions |
| tsfresh | 13 | `EfficientFCParameters` filtered via `default_fc_parameters` |
| catch22 | **0** | all 22 catch22 features are different definitions — see exclusions |
| numba baseline | 33 | hand-written reimplementation of the same 33 definitions |
| numpy baseline | 33 | vectorized reimplementation of the same 33 definitions |

## TSFEL mapping (13)

| Kymora | TSFEL function | Definition (both sides) | Class |
|---|---|---|---|
| `mean` | `Mean` | arithmetic mean | EXACT |
| `std` | `Standard deviation` | population std (ddof=0) | EXACT |
| `var` | `Variance` | population variance (ddof=0) | EXACT |
| `min` | `Min` | minimum | EXACT |
| `max` | `Max` | maximum | EXACT |
| `median` | `Median` | 50th percentile (linear interpolation) | EXACT |
| `skewness` | `Skewness` | Fisher-Pearson, biased (ddof=0) | EXACT |
| `kurtosis` | `Kurtosis` | excess kurtosis, Fisher, biased | EXACT |
| `abs_energy` | `Absolute energy` | Σ x² | EXACT |
| `root_mean_square` | `Root mean square` | √(Σ x² / n) | EXACT |
| `mean_abs_change` | `Mean absolute diff` | mean of absolute first differences | EXACT |
| `mean_change` | `Mean diff` | mean of first differences | EXACT |
| `zero_crossings` | `Zero crossing rate` | count of strict sign changes | EXACT |

## tsfresh mapping (13, over 14 kymora columns)

| Kymora | tsfresh feature | Definition (both sides) | Class |
|---|---|---|---|
| `median` | `median` | 50th percentile | EXACT |
| `quantile_10` | `quantile__q_0.1` | 10th percentile, linear method | EXACT |
| `quantile_90` | `quantile__q_0.9` | 90th percentile, linear method | EXACT |
| `abs_energy` | `abs_energy` | Σ x² | EXACT |
| `root_mean_square` | `root_mean_square` | quadratic mean | EXACT |
| `mean_abs_change` | `mean_abs_change` | mean absolute first difference | EXACT |
| `mean_change` | `mean_change` | (x[n-1] − x[0]) / (n−1) | EXACT |
| `mean_second_derivative_central` | `mean_second_derivative_central` | mean central second difference | EXACT |
| `longest_strike_above_mean` | `longest_strike_above_mean` | longest run > mean(x) | EXACT |
| `longest_strike_below_mean` | `longest_strike_below_mean` | longest run < mean(x) | EXACT |
| `autocorr_lag_1` | `autocorrelation__lag_1` | Pearson autocorrelation at lag 1 | EXACT |
| `autocorr_lag_2` | `autocorrelation__lag_2` | Pearson autocorrelation at lag 2 | EXACT |
| `autocorr_lag_5` | `autocorrelation__lag_5` | Pearson autocorrelation at lag 5 | EXACT |

## Why catch22 has no equal-feature row

catch22's 22 features are bespoke structural quantities with no
definition-identical counterpart in core33. The near-misses are documented
in `feature_map.json`; none agree within tolerance:

| catch22 feature | Closest core33 feature | Why it differs |
|---|---|---|
| `CO_Embed2_Dist_tau_d_expfit_meandiff` | `autocorr_lag_1` | measures exponential-fit quality of lag-2 embedding distances, not the ACF value |
| `SP_Summaries_welch_rect_centroid` | `spectral_centroid` | centroid of a Welch-windowed, rescaled spectrum, not the raw-FFT centroid |
| `CO_f1ecac` | — | correlation length via 1/e decay of ACF |
| `DN_HistogramMode_5` / `_10` | — | histogram bin mode, not a moment |
| `FC_LocalSimple_mean1_tauresrat` | — | ratio of time-scale estimates |
| `SB_BinaryStats_mean_longstretch1` | — | longest run of a binary transform |
| remaining 16 | — | transition-matrix, motif, outlier and fluctuation measures with no core33 analogue |

Because no feature can be timed on both sides with the same definition,
catch22 appears only in the raw-time and per-feature tables, never in the
equal-feature table. An equal-feature row would require implementing
catch22's definitions inside kymora (`catch22` profile, planned).

## numba / numpy baselines (33)

The two in-repo baselines reimplement the exact core33 definitions
(`benchmarks/adapters/numba_baseline.py`, `benchmarks/adapters/numpy_baseline.py`).
The full 33-feature set is the equal set. Adversarial distributions
(cancellation, tiny/huge scale) are excluded from parity claims for the
numba baseline: its naive one-pass variance degrades there while kymora
uses two-pass centered moments (`L1_ROOT_CAUSE.md` §3).

## Verification

```bash
python benchmarks/suites/equal_feature.py parity   # gate: exits 0 on pass
python benchmarks/suites/equal_feature.py bench    # timing on the agreed subsets
```

Parity artifact: `benchmarks/results/<date>_equal_feature/parity.json`.
Timing artifact: `benchmarks/results/<date>_equal_feature/equal_feature.jsonl`
summarized in `benchmarks/results/EQUAL_FEATURE_REPORT.md`.
