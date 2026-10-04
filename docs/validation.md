# Validation report

Regenerate this page with `python tools/validation_report.py`. CI runs the same
script on every push and fails the build if any feature drifts outside tolerance
or disagrees with the reference on NaN, so a stale or optimistic table here
cannot survive a merge. The run below is from a maintainer machine; the CI run
publishes the same table as a job summary and an artifact.


kymora 0.2.0 on Windows-11-10.0.26200-SP0, Python 3.14.6, numpy 2.4.6.

Each of the 33 features is compared against a numpy/scipy reference implementation across 7 sample series (gaussian, trend, sine, constant, tiny, single, integers_with_ties), covering normal, trending, periodic, constant, two-element, single-element, and heavily-tied data.

Tolerance: atol=1e-10, rtol=1e-09. NaN must agree exactly -- the NaN policy is part of the API contract, so a NaN where a number was expected (or vice versa) fails regardless of tolerance.

| feature | max abs error | worst-case series | series compared | verdict |
|---|---:|---|---:|---|
| `mean` | 2.842e-14 | trend | 7/7 | within tolerance |
| `std` | 7.105e-15 | trend | 7/7 | within tolerance |
| `var` | 4.547e-13 | trend | 7/7 | within tolerance |
| `min` | 0.000e+00 | - | 7/7 | bit-identical |
| `max` | 0.000e+00 | - | 7/7 | bit-identical |
| `median` | 0.000e+00 | - | 7/7 | bit-identical |
| `quantile_10` | 0.000e+00 | - | 7/7 | bit-identical |
| `quantile_25` | 0.000e+00 | - | 7/7 | bit-identical |
| `quantile_75` | 0.000e+00 | - | 7/7 | bit-identical |
| `quantile_90` | 0.000e+00 | - | 7/7 | bit-identical |
| `skewness` | 2.671e-15 | trend | 5/7 | within tolerance |
| `kurtosis` | 8.882e-16 | trend | 5/7 | within tolerance |
| `abs_energy` | 4.657e-10 | trend | 7/7 | within tolerance |
| `root_mean_square` | 1.421e-14 | trend | 7/7 | within tolerance |
| `mean_abs_change` | 4.441e-16 | trend | 6/7 | within tolerance |
| `mean_change` | 0.000e+00 | - | 6/7 | bit-identical |
| `cid_ce` | 7.105e-15 | gaussian | 6/7 | within tolerance |
| `mean_second_derivative_central` | 8.890e-18 | gaussian | 5/7 | within tolerance |
| `zero_crossings` | 0.000e+00 | - | 7/7 | bit-identical |
| `mean_crossings` | 0.000e+00 | - | 7/7 | bit-identical |
| `number_of_peaks` | 0.000e+00 | - | 7/7 | bit-identical |
| `longest_strike_above_mean` | 0.000e+00 | - | 7/7 | bit-identical |
| `longest_strike_below_mean` | 0.000e+00 | - | 7/7 | bit-identical |
| `autocorr_lag_1` | 8.882e-16 | trend | 5/7 | within tolerance |
| `autocorr_lag_2` | 5.551e-16 | trend | 4/7 | within tolerance |
| `autocorr_lag_5` | 2.220e-16 | trend | 4/7 | within tolerance |
| `autocorr_lag_10` | 5.551e-16 | sine | 4/7 | within tolerance |
| `trend_slope` | 4.337e-19 | integers_with_ties | 6/7 | within tolerance |
| `trend_r2` | 2.220e-16 | trend | 5/7 | within tolerance |
| `permutation_entropy` | 1.110e-16 | integers_with_ties | 5/7 | within tolerance |
| `dominant_frequency` | 0.000e+00 | - | 5/7 | bit-identical |
| `spectral_centroid` | 3.886e-16 | gaussian | 5/7 | within tolerance |
| `spectral_entropy` | 6.661e-16 | gaussian | 5/7 | within tolerance |

Rows reading *NaN by contract* are features that are undefined for every sample series in this matrix (none currently) -- they are still asserted to be NaN in both implementations.

**All features within tolerance.**

## How to read this

`max abs error` is the largest absolute difference between the Rust core and the
numpy/scipy reference over every sample series where both produced a finite
number. `series compared` is how many of the sample series contributed — a
feature that is NaN by contract on constant or very short series compares on
fewer of them, and its NaN agreement is checked separately and exactly.

`bit-identical` means the two implementations produced the same float bit for
bit. Everything else is float-summation ordering: the Rust core sums in a
different order than numpy, which is why `var` on a trending series differs
around 1e-13 while `min` never differs at all.

The tolerance is the same one `numpy.testing.assert_allclose` applies in the test
suite, `atol + rtol * |expected|`, so this report and `pytest tests/` agree by
construction rather than by coincidence.

## What this does not cover

This is a *numeric accuracy* report over a fixed sample matrix. Robustness — that
no input crashes the extension or violates the NaN policy — is a separate concern
covered by the `hypothesis` property tests in `tests/test_properties.py`, and the
NaN contract itself is pinned by `tests/test_nan_policy.py`. Neither substitutes
for the other.
