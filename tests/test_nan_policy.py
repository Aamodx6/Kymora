"""The NaN contract (architecture §6), locked down row by row.

    | input condition                        | output                          |
    |----------------------------------------|---------------------------------|
    | series contains any NaN                | all 33 features NaN             |
    | feature undefined for a valid series    | that feature only is NaN        |
    | empty series (length 0)                 | structural error, not a NaN row |

Changing any expectation in this file is a change to the public output contract
and requires a version bump per architecture §9.
"""

import numpy as np
import pytest

import tsxtract

NAMES = tsxtract.feature_names()
N_FEATURES = len(NAMES)


def nan_set(x):
    """Names of the features that come back NaN for series ``x``."""
    row = tsxtract.extract_features([np.asarray(x, dtype=np.float64)])[0]
    return {n for n, v in zip(NAMES, row) if np.isnan(v)}


# ---------------------------------------------------------------------------
# Row 1: any NaN in the series -> all 33 features NaN
# ---------------------------------------------------------------------------

SERIES_WITH_NAN = {
    "nan_first": np.concatenate([[np.nan], np.arange(1.0, 100.0)]),
    "nan_middle": np.concatenate([np.arange(50.0), [np.nan], np.arange(50.0)]),
    "nan_last": np.concatenate([np.arange(1.0, 100.0), [np.nan]]),
    "all_nan": np.full(50, np.nan),
    "single_nan": np.array([np.nan]),
    "nan_among_constants": np.array([2.0, 2.0, np.nan, 2.0]),
    "nan_and_inf": np.array([1.0, np.inf, np.nan, 2.0]),
}


@pytest.mark.parametrize("name", SERIES_WITH_NAN)
def test_any_nan_makes_every_feature_nan(name):
    row = tsxtract.extract_features([SERIES_WITH_NAN[name]])[0]
    assert row.shape == (N_FEATURES,)
    assert np.isnan(row).all(), f"{name}: partial computation leaked through"


def test_nan_row_does_not_contaminate_its_neighbours():
    """Row-NaN is per series: a poisoned series must not affect the rest of the
    batch, in either the 2D or the ragged path."""
    rng = np.random.default_rng(7)
    clean = rng.standard_normal((5, 60))
    X = clean.copy()
    X[2, 30] = np.nan

    out = tsxtract.extract_features(X)
    assert np.isnan(out[2]).all()
    assert not np.isnan(np.delete(out, 2, axis=0)).any()

    # the surviving rows must be bit-identical to extracting them alone
    reference = tsxtract.extract_features(np.ascontiguousarray(np.delete(clean, 2, axis=0)))
    np.testing.assert_array_equal(np.delete(out, 2, axis=0), reference)

    ragged = tsxtract.extract_features(list(X))
    np.testing.assert_array_equal(ragged, out)


def test_no_silent_imputation():
    """A NaN must not be dropped, zero-filled, or interpolated: the features of a
    NaN-containing series must not equal those of the same series with the NaN
    removed or replaced."""
    base = np.arange(1.0, 21.0)
    with_nan = base.copy()
    with_nan[10] = np.nan

    poisoned = tsxtract.extract_features([with_nan])[0]
    dropped = tsxtract.extract_features([np.delete(base, 10)])[0]
    zeroed = tsxtract.extract_features([np.where(np.isnan(with_nan), 0.0, with_nan)])[0]

    assert np.isnan(poisoned).all()
    assert not np.isnan(dropped).any()
    assert not np.isnan(zeroed).any()


def test_sliding_features_nan_is_windowed_not_global():
    """In sliding_features, only the windows that actually contain the NaN go
    NaN — the contract is per extracted series, and each window is a series."""
    x = np.arange(100.0)
    x[55] = np.nan
    out = tsxtract.sliding_features(x, window=10, stride=10)
    assert out.shape == (10, N_FEATURES)
    poisoned = np.isnan(out).all(axis=1)
    assert poisoned[5]
    assert not poisoned[np.arange(10) != 5].any()


# ---------------------------------------------------------------------------
# Row 2: individually undefined features -> that feature only is NaN
# ---------------------------------------------------------------------------

# Undefined because the series has zero variance: no shape to correlate, no
# spectrum outside DC, no standardized moments.
CONSTANT_UNDEFINED = {
    "skewness",
    "kurtosis",
    "autocorr_lag_1",
    "autocorr_lag_2",
    "autocorr_lag_5",
    "autocorr_lag_10",
    "trend_r2",
    "dominant_frequency",
    "spectral_centroid",
    "spectral_entropy",
}

# Undefined because a length-1 series has no differences, no trend, no spectrum.
SINGLE_ELEMENT_UNDEFINED = CONSTANT_UNDEFINED | {
    "mean_abs_change",
    "mean_change",
    "cid_ce",
    "mean_second_derivative_central",
    "trend_slope",
    "permutation_entropy",
}

# Undefined because a lag/window is longer than the series.
LEN2_UNDEFINED = {
    "mean_second_derivative_central",
    "permutation_entropy",
    "autocorr_lag_2",
    "autocorr_lag_5",
    "autocorr_lag_10",
}

LEN3_UNDEFINED = {"autocorr_lag_5", "autocorr_lag_10"}


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        pytest.param(np.full(100, 3.7), CONSTANT_UNDEFINED, id="constant_nonzero"),
        pytest.param(np.zeros(100), CONSTANT_UNDEFINED, id="all_zero"),
        pytest.param(np.full(100, -1e6), CONSTANT_UNDEFINED, id="constant_large"),
        pytest.param(np.array([5.0]), SINGLE_ELEMENT_UNDEFINED, id="single_element"),
        pytest.param(np.array([0.0]), SINGLE_ELEMENT_UNDEFINED, id="single_zero"),
        pytest.param(np.array([1.0, 2.0]), LEN2_UNDEFINED, id="length_2"),
        pytest.param(np.array([1.0, 2.0, 3.0]), LEN3_UNDEFINED, id="length_3"),
        pytest.param(np.arange(11.0), set(), id="length_11_all_lags_defined"),
    ],
)
def test_feature_level_nan_is_exactly_the_documented_set(x, expected):
    assert nan_set(x) == expected


def test_undefined_features_do_not_poison_the_rest_of_the_row():
    """The distinguishing property of feature-level NaN: everything else in the
    same row still computes."""
    x = np.full(100, 3.7)
    row = tsxtract.extract_features([x])[0]
    defined = {n: v for n, v in zip(NAMES, row) if n not in CONSTANT_UNDEFINED}

    assert len(defined) == N_FEATURES - len(CONSTANT_UNDEFINED)
    assert not np.isnan(list(defined.values())).any()
    assert defined["mean"] == pytest.approx(3.7)
    assert defined["std"] == 0.0
    assert defined["var"] == 0.0
    assert defined["trend_slope"] == 0.0
    assert defined["cid_ce"] == 0.0
    assert defined["permutation_entropy"] == 0.0


def test_constant_series_variance_is_exactly_zero_not_float_noise():
    """Zero variance is what gates the undefined set, so it must be exact — a
    1e-31 residue from summation order would silently flip these features from
    NaN to garbage."""
    for value in (3.7, -1e6, 1e-8, 0.0):
        row = tsxtract.extract_features([np.full(1000, value)])[0]
        got = dict(zip(NAMES, row))
        assert got["var"] == 0.0
        assert got["std"] == 0.0


# ---------------------------------------------------------------------------
# Row 3: empty series -> structural error, NOT a NaN row
# ---------------------------------------------------------------------------


def test_empty_series_is_an_error_not_a_nan_row():
    with pytest.raises(ValueError):
        tsxtract.extract_features([np.array([], dtype=np.float64)])


def test_empty_series_error_takes_precedence_over_nan_neighbours():
    """The structural check runs before any compute, so a zero-length series is
    reported even when another series in the batch would have produced NaN."""
    batch = [np.array([1.0, np.nan]), np.array([], dtype=np.float64)]
    with pytest.raises(ValueError, match="index 1"):
        tsxtract.extract_features(batch)


# ---------------------------------------------------------------------------
# Not part of the NaN contract: infinities
# ---------------------------------------------------------------------------


def test_infinite_input_is_a_value_not_an_error_and_not_nan_row():
    """Inf is deliberately outside the NaN policy: it is a valid f64 that
    propagates through arithmetic on its own terms. It must not raise and must
    not be silently converted into the all-NaN row that NaN triggers.
    """
    x = np.array([1.0, np.inf, 2.0, 3.0])
    row = tsxtract.extract_features([x])[0]
    assert row.shape == (N_FEATURES,)
    assert not np.isnan(row).all()
    assert np.isinf(dict(zip(NAMES, row))["max"])
