# Intentional definition differences (parity scope notes)

Source: `benchmarks/agreement/feature_map.json` (B1-frozen). A feature is
listed here when no counterpart with an agreeing definition exists in that
library — comparing against a same-named but differently-defined quantity
would manufacture a "failure", so these are excluded from
`test_external_parity.py` by design, not by omission.

## tsfresh (5 unmatched of 33)

tsfresh has no same-definition counterpart for the crossing counters or the
spectral summaries as kymora defines them:

- `zero_crossings`, `mean_crossings` — kymora counts `>`-on-both-sides
  transitions; tsfresh's crossing features use different level conventions.
- `dominant_frequency`, `spectral_centroid`, `spectral_entropy` — kymora
  computes them on the exact (unpadded) mean-removed spectrum with its own
  normalization; tsfresh's spectral features differ in windowing/segments.

## TSFEL (14 unmatched of 33)

TSFEL has no counterpart for order statistics beyond the median, the
complexity/second-derivative family, strike lengths, higher ACF lags,
`trend_r2`, or permutation entropy:

- `quantile_10/25/75/90`, `mean_crossings`,
  `longest_strike_above_mean/below_mean`
- `cid_ce`, `mean_second_derivative_central`
- `autocorr_lag_2/5/10` (only lag 1 agrees)
- `trend_r2`, `permutation_entropy`

## catch22 (30 unmatched of 33; verified set is empty)

catch22 is a fixed 22-feature bank with its own definitions; only three
kymora features even name a catch22 quantity, and none are verified
like-for-like:

- `autocorr_lag_1` ↔ `CO_Embed2_Dist_tau_d_expfit_meandiff` (different
  estimator; unverified, excluded).
- `dominant_frequency` and `spectral_centroid` both point at
  `SP_Summaries_welch_rect_centroid` (Welch-based, different pipeline from
  kymora's exact spectrum; unverified, excluded).

The remaining 27 kymora features have no catch22 counterpart at all
(moments, quantiles, change, counts, trend, entropy).

## Rule

A new comparison is added to `test_external_parity.py` only after its
feature pair is verified EXACT (≤1e-9) in a parity artifact and recorded in
`benchmarks/results/*/parity.json`. Until then it lives here.
