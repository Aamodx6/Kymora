import numpy as np
import pytest
from scipy import stats

try:
    import statsmodels.tsa.stattools as stattools
except ImportError:
    stattools = None

try:
    from tsfresh.feature_extraction import feature_calculators as tsf_calc
except ImportError:
    tsf_calc = None

import tsxtractor


def test_phase4_profile_shapes():
    profiles = tsxtractor.list_profiles()
    assert profiles["core33"] == 33
    assert profiles["extended"] == 143
    assert profiles["full"] == 543

    X = np.random.default_rng(42).standard_normal((10, 100))

    out_ext = tsxtractor.extract_features(X, profile="extended")
    assert out_ext.shape == (10, 143)
    assert len(tsxtractor.feature_names(profile="extended")) == 143

    out_full = tsxtractor.extract_features(X, profile="full")
    assert out_full.shape == (10, 543)
    assert len(tsxtractor.feature_names(profile="full")) == 543


def test_reference_parity_c3_and_time_reversal():
    if tsf_calc is None:
        pytest.skip("tsfresh not installed")
    rng = np.random.default_rng(123)
    x = rng.standard_normal(100)
    X = x.reshape(1, -1)

    for lag in (1, 2, 3):
        feat_name = f"c3__lag_{lag}"
        our_val = tsxtractor.extract_features(X, features=[feat_name])[0, 0]
        tsf_val = tsf_calc.c3(x, lag)
        np.testing.assert_allclose(our_val, tsf_val, rtol=1e-12, atol=1e-12)

    for lag in (1, 2, 3):
        feat_name = f"time_reversal_asymmetry_statistic__lag_{lag}"
        our_val = tsxtractor.extract_features(X, features=[feat_name])[0, 0]
        tsf_val = tsf_calc.time_reversal_asymmetry_statistic(x, lag)
        np.testing.assert_allclose(our_val, tsf_val, rtol=1e-12, atol=1e-12)


def test_reference_parity_crossings_and_peaks():
    if tsf_calc is None:
        pytest.skip("tsfresh not installed")
    rng = np.random.default_rng(456)
    x = rng.standard_normal(120)
    X = x.reshape(1, -1)

    for m in (-1.0, 1.0):
        feat_name = f"number_crossing_m__m_{int(m)}"
        our_val = tsxtractor.extract_features(X, features=[feat_name])[0, 0]
        tsf_val = tsf_calc.number_crossing_m(x, m)
        assert our_val == tsf_val

    for n in (1, 5, 10, 50):
        feat_name = f"number_peaks__n_{n}"
        our_val = tsxtractor.extract_features(X, features=[feat_name])[0, 0]
        tsf_val = tsf_calc.number_peaks(x, n)
        assert our_val == tsf_val


def test_reference_parity_autocorrelation_and_pacf():
    if tsf_calc is None or stattools is None:
        pytest.skip("tsfresh and/or statsmodels not installed")
    rng = np.random.default_rng(789)
    x = rng.standard_normal(100)
    X = x.reshape(1, -1)

    for lag in (0, 3, 4, 6, 7, 8, 9):
        feat_name = f"autocorrelation__lag_{lag}"
        our_val = tsxtractor.extract_features(X, features=[feat_name])[0, 0]
        tsf_val = tsf_calc.autocorrelation(x, lag)
        np.testing.assert_allclose(our_val, tsf_val, rtol=1e-12, atol=1e-12)

    sm_pacf = stattools.pacf(x, nlags=9, method="ld")
    for lag in range(1, 10):
        feat_name = f"partial_autocorrelation__lag_{lag}"
        our_val = tsxtractor.extract_features(X, features=[feat_name])[0, 0]
        tsf_param = [{"lag": lag}]
        tsf_val = list(tsf_calc.partial_autocorrelation(x, tsf_param))[0][1]
        np.testing.assert_allclose(our_val, tsf_val, rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(our_val, sm_pacf[lag], rtol=1e-10, atol=1e-10)


def test_reference_parity_linear_trend_intercept_and_stderr():
    rng = np.random.default_rng(999)
    x = rng.standard_normal(80)
    X = x.reshape(1, -1)

    reg = stats.linregress(np.arange(len(x)), x)
    our_vals = tsxtractor.extract_features(
        X, features=['linear_trend__attr_"intercept"', 'linear_trend__attr_"stderr"']
    )[0]
    np.testing.assert_allclose(our_vals[0], reg.intercept, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(our_vals[1], reg.stderr, rtol=1e-12, atol=1e-12)


def test_reference_parity_fft_coefficients_and_aggregated():
    rng = np.random.default_rng(321)
    x = rng.standard_normal(100)
    X = x.reshape(1, -1)

    # FFT Coefficients
    rfft_x = np.fft.rfft(x)
    for k in (0, 1, 5, 20, 49):
        feats = [
            f'fft_coefficient__coeff_{k}__attr_"real"',
            f'fft_coefficient__coeff_{k}__attr_"imag"',
            f'fft_coefficient__coeff_{k}__attr_"abs"',
            f'fft_coefficient__coeff_{k}__attr_"angle"',
        ]
        our_vals = tsxtractor.extract_features(X, features=feats)[0]
        np.testing.assert_allclose(our_vals[0], rfft_x[k].real, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(our_vals[1], rfft_x[k].imag, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(our_vals[2], np.abs(rfft_x[k]), rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(our_vals[3], np.angle(rfft_x[k], deg=True), rtol=1e-12, atol=1e-12)

    # FFT Aggregated
    if tsf_calc is not None:
        agg_names = [
            'fft_aggregated__aggtype_"centroid"',
            'fft_aggregated__aggtype_"variance"',
            'fft_aggregated__aggtype_"skew"',
            'fft_aggregated__aggtype_"kurtosis"',
        ]
        our_agg = tsxtractor.extract_features(X, features=agg_names)[0]
        tsf_agg = dict(tsf_calc.fft_aggregated(x, [{"aggtype": a} for a in ["centroid", "variance", "skew", "kurtosis"]]))
        np.testing.assert_allclose(our_agg[0], tsf_agg['aggtype_"centroid"'], rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(our_agg[1], tsf_agg['aggtype_"variance"'], rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(our_agg[2], tsf_agg['aggtype_"skew"'], rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(our_agg[3], tsf_agg['aggtype_"kurtosis"'], rtol=1e-10, atol=1e-10)


def test_reference_parity_distribution_and_change_stats():
    rng = np.random.default_rng(654)
    x = rng.standard_normal(90)
    X = x.reshape(1, -1)

    feats = [
        "sum_values",
        "length",
        "count_above_mean",
        "count_below_mean",
        "has_duplicate",
        "has_duplicate_max",
        "has_duplicate_min",
        "variance_larger_than_standard_deviation",
        "variation_coefficient",
        "first_location_of_maximum",
        "first_location_of_minimum",
        "last_location_of_maximum",
        "last_location_of_minimum",
        "absolute_sum_of_changes",
        "cid_ce_raw",
    ]
    our_vals = tsxtractor.extract_features(X, features=feats)[0]
    assert our_vals[0] == pytest.approx(np.sum(x), rel=1e-12)
    assert our_vals[1] == len(x)
    assert our_vals[2] == np.sum(x > np.mean(x))
    assert our_vals[3] == np.sum(x < np.mean(x))
    assert our_vals[4] == float(len(x) != len(np.unique(x)))
    assert our_vals[5] == float(np.sum(x == np.max(x)) > 1)
    assert our_vals[6] == float(np.sum(x == np.min(x)) > 1)
    assert our_vals[7] == float(np.var(x) > np.std(x))
    assert our_vals[8] == pytest.approx(np.std(x) / np.mean(x), rel=1e-12)
    assert our_vals[9] == pytest.approx(np.argmax(x) / len(x), rel=1e-12)
    assert our_vals[10] == pytest.approx(np.argmin(x) / len(x), rel=1e-12)
    assert our_vals[11] == pytest.approx((len(x) - 1 - np.argmax(x[::-1])) / len(x), rel=1e-12)
    assert our_vals[12] == pytest.approx((len(x) - 1 - np.argmin(x[::-1])) / len(x), rel=1e-12)
    assert our_vals[13] == pytest.approx(np.sum(np.abs(np.diff(x))), rel=1e-12)
    assert our_vals[14] == pytest.approx(np.sqrt(np.sum(np.diff(x) ** 2)), rel=1e-12)


def test_edge_cases_extended():
    # Constant series
    const_x = np.ones((1, 50)) * 5.0
    out_const = tsxtractor.extract_features(const_x, profile="extended")[0]
    assert np.isfinite(out_const[0])  # mean is 5.0
    # NaN check: NaN in input -> all features NaN
    nan_x = const_x.copy()
    nan_x[0, 10] = np.nan
    out_nan = tsxtractor.extract_features(nan_x, profile="extended")[0]
    assert np.all(np.isnan(out_nan))

    # Large offset cancellation series
    large_x = np.ones((1, 100)) * 1e9 + np.random.default_rng(42).standard_normal(100)
    out_large = tsxtractor.extract_features(large_x, profile="extended")[0]
    # Variance of standard normal should match numpy even with 1e9 mean
    var_idx = tsxtractor.feature_names(profile="extended").index("var")
    np.testing.assert_allclose(out_large[var_idx], np.var(large_x), rtol=1e-8)
