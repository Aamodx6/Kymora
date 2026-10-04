# Architecture and Feature Catalog Audit (`docs/arch_audit.md`)

**Date:** 2026-10-04  
**Audit Target:** Alignment between built library `tsxtract.feature_names()`, `README.md`, `arch.md`, and `benches/agreement/feature_map.json`.

---

## 1. Single Source of Truth: Built Library Core33

The authoritative single source of truth for the 33 features is `tsxtract.feature_names()` (or `tsxtract.feature_names()`) as exported by the compiled Rust core extension `_core`:

```python
import tsxtract
names = tsxtract.feature_names()
assert len(names) == 33
```

### Authoritative 33 Feature List:
1. `mean`
2. `std`
3. `var`
4. `min`
5. `max`
6. `median`
7. `quantile_10`
8. `quantile_25`
9. `quantile_75`
10. `quantile_90`
11. `skewness`
12. `kurtosis`
13. `abs_energy`
14. `root_mean_square`
15. `mean_abs_change`
16. `mean_change`
17. `cid_ce`
18. `mean_second_derivative_central`
19. `zero_crossings`
20. `mean_crossings`
21. `number_of_peaks`
22. `longest_strike_above_mean`
23. `longest_strike_below_mean`
24. `autocorr_lag_1`
25. `autocorr_lag_2`
26. `autocorr_lag_5`
27. `autocorr_lag_10`
28. `trend_slope`
29. `trend_r2`
30. `permutation_entropy`
31. `dominant_frequency`
32. `spectral_centroid`
33. `spectral_entropy`

---

## 2. Audit against `arch.md`

`arch.md` §2.3 defines the internal Rust module split and feature groups:
- **`stats.rs` (14 features):** `mean`, `std`, `var`, `min`, `max`, `median`, `quantiles` (10, 25, 75, 90), `skew`, `kurtosis`, `abs_energy`, `rms`.
- **`change.rs` (4 features):** `mean_abs_change`, `mean_change`, `cid_ce`, `mean_second_derivative_central`.
- **`counts.rs` (5 features):** `zero_crossings`, `mean_crossings`, `number_of_peaks`, `longest_strike_above_mean`, `longest_strike_below_mean`.
- **`correlation.rs` (6 features):** `autocorr_lag_1`, `autocorr_lag_2`, `autocorr_lag_5`, `autocorr_lag_10`, `trend_slope`, `trend_r2`.
- **`entropy.rs` (1 feature):** `permutation_entropy`.
- **`spectral.rs` (3 features):** `dominant_frequency`, `spectral_centroid`, `spectral_entropy`.

**Result:** `arch.md` matches the compiled core exactly in count (33) and mathematical scope. Minor naming differences in descriptive text (`rms` vs `root_mean_square`, `skew` vs `skewness`) map 1:1 to registry symbols.

---

## 3. Audit against `README.md` (Discrepancies Found)

In `README.md` lines 220–230 ("The 33 Curated Features"), several descriptive inaccuracies exist relative to the compiled core:

| Feature / Category in `README.md` | Actual in Built Core (`feature_names()`) | Status / Discrepancy |
|---|---|---|
| Peak-to-Peak Range | *None* | **Mismatch**: Not computed as an independent feature in `core33`. `min` and `max` are computed. |
| Quantiles: `q05, q25, median, q75, q95` | `quantile_10, quantile_25, median, quantile_75, quantile_90` | **Mismatch**: Library computes 10th and 90th percentiles, not 5th and 95th. |
| Interquartile Range (IQR) | *None* | **Mismatch**: Not present in `core33` (available in extended). |
| Crest Factor | *None* | **Mismatch**: Not present in `core33`. |
| Median Absolute Deviation (MAD) | *None* | **Mismatch**: Not present in `core33`. |
| Autocorrelation: Lag-1, Lag-2, **Lag-3**, Lag-5, Lag-10 | `autocorr_lag_1, autocorr_lag_2, autocorr_lag_5, autocorr_lag_10` | **Mismatch**: Lag-3 is omitted in `core33` to prevent collinearity with lag-1/2/5. |
| Spectral: `Energy, Spectral Energy, Dominant Frequency, Spectral Centroid, Spectral Spread, Spectral Roll-off` | `abs_energy` (moments), `dominant_frequency`, `spectral_centroid`, `spectral_entropy` | **Mismatch**: Spectral spread and spectral roll-off belong to the `extended` profile (143 features), not `core33`. |
| *Omitted from README list* | `mean_second_derivative_central` | **Omission**: Present in `core33`. |
| *Omitted from README list* | `longest_strike_above_mean` | **Omission**: Present in `core33`. |
| *Omitted from README list* | `longest_strike_below_mean` | **Omission**: Present in `core33`. |
| *Omitted from README list* | `trend_slope` | **Omission**: Present in `core33`. |
| *Omitted from README list* | `trend_r2` | **Omission**: Present in `core33`. |

### Action Item for Documentation:
Update `README.md` § "The 33 Curated Features" to list the exact 33 features emitted by `tsxtract.feature_names()`. All agreement matrices and benchmark suites MUST use the built library names.
