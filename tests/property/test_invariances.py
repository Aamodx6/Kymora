"""Invariance property tests (Phase 3.5).

Mathematical identities the pipeline must preserve regardless of
implementation: permutation invariance of order-free statistics, affine
invariance of scale-free features, and commutation of extrema/median with
strictly monotonic transforms. Violations would indicate an
order- or offset-dependent bug (e.g. a non-commutative accumulation leaking
into a supposedly invariant feature).
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

import kymora

SETTINGS = settings(
    max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)

PERMUTATION_INVARIANT = [
    "mean", "std", "var", "min", "max", "median",
    "quantile_10", "quantile_25", "quantile_75", "quantile_90",
    "skewness", "kurtosis", "abs_energy", "root_mean_square",
]
AFFINE_INVARIANT = [
    "autocorr_lag_1", "autocorr_lag_2", "autocorr_lag_5", "autocorr_lag_10",
    "trend_r2", "permutation_entropy",
]


@SETTINGS
@given(
    n=st.integers(min_value=12, max_value=64),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
)
def test_permutation_invariance(n, seed):
    rng = np.random.default_rng(seed)
    x = np.ascontiguousarray(rng.standard_normal(n))
    perm = np.ascontiguousarray(rng.permutation(n))
    a = kymora.extract_features(x[None, :], features=PERMUTATION_INVARIANT)[0]
    b = kymora.extract_features(x[perm][None, :], features=PERMUTATION_INVARIANT)[0]
    for name, u, v in zip(PERMUTATION_INVARIANT, a, b):
        if np.isnan(u):
            assert np.isnan(v), name
        else:
            np.testing.assert_allclose(u, v, rtol=1e-9, atol=1e-12, err_msg=name)


@SETTINGS
@given(
    n=st.integers(min_value=12, max_value=64),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    log_scale=st.floats(min_value=-2.0, max_value=2.0),
    shift=st.floats(min_value=-5.0, max_value=5.0),
)
def test_affine_invariance(n, seed, log_scale, shift):
    rng = np.random.default_rng(seed)
    x = np.ascontiguousarray(rng.standard_normal(n))
    assume(np.std(x) > 1e-6)
    a = np.exp(log_scale)
    y = np.ascontiguousarray(a * x + shift)
    got = kymora.extract_features(y[None, :], features=AFFINE_INVARIANT)[0]
    want = kymora.extract_features(x[None, :], features=AFFINE_INVARIANT)[0]
    for name, u, v in zip(AFFINE_INVARIANT, got, want):
        if np.isnan(v):
            assert np.isnan(u), name
        else:
            np.testing.assert_allclose(u, v, rtol=1e-9, atol=1e-12, err_msg=name)


def test_monotonic_extrema_and_median_commute():
    # Odd length: the median rank is a single element, so min/max/median
    # select the same element before and after a strictly increasing map.
    rng = np.random.default_rng(11)
    x = np.ascontiguousarray(rng.uniform(-2.0, 2.0, 51))
    y = np.ascontiguousarray(np.exp(x))
    for name in ("min", "max", "median"):
        got = kymora.extract_features(y[None, :], features=[name])[0, 0]
        want_raw = kymora.extract_features(x[None, :], features=[name])[0, 0]
        assert got == np.exp(want_raw), name
    # Quantile levels stay ordered under the monotonic map.
    qs = kymora.extract_features(
        y[None, :],
        features=["quantile_10", "quantile_25", "median", "quantile_75", "quantile_90"],
    )[0]
    assert bool(np.all(np.diff(qs) >= 0))


def test_affine_covariance_spot_check():
    # Covariant (not invariant) features scale exactly: mean and std.
    rng = np.random.default_rng(13)
    x = np.ascontiguousarray(rng.standard_normal(100))
    y = np.ascontiguousarray(2.5 * x - 1.25)
    got = kymora.extract_features(y[None, :], features=["mean", "std", "var"])[0]
    want = kymora.extract_features(x[None, :], features=["mean", "std", "var"])[0]
    np.testing.assert_allclose(got[0], 2.5 * want[0] - 1.25, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(got[1], 2.5 * want[1], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(got[2], 6.25 * want[2], rtol=1e-12, atol=1e-12)
