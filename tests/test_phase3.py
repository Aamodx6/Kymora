import numpy as np
import pytest
import time
import tsxtractor


def test_list_profiles():
    profiles = tsxtractor.list_profiles()
    assert isinstance(profiles, dict)
    assert "minimal" in profiles
    assert "core33" in profiles
    assert "extended" in profiles
    assert "full" in profiles
    assert profiles["minimal"] > 0
    assert profiles["core33"] == 33
    assert profiles["minimal"] < profiles["core33"]


def test_describe_feature():
    desc_mean = tsxtractor.describe_feature("mean")
    assert isinstance(desc_mean, dict)
    assert desc_mean["name"] == "mean"
    assert "PASS1" in desc_mean["needs"]

    # Test alias resolution
    desc_alias = tsxtractor.describe_feature("standard_deviation")
    assert desc_alias["name"] == "std"

    with pytest.raises(ValueError, match="unknown feature"):
        tsxtractor.describe_feature("non_existent_feature_123")


def test_feature_names_profiles():
    all_33 = tsxtractor.feature_names()
    assert len(all_33) == 33

    core_names = tsxtractor.feature_names(profile="core33")
    assert core_names == all_33

    min_names = tsxtractor.feature_names(profile="minimal")
    assert len(min_names) < 33
    for name in min_names:
        assert name in all_33

    custom_names = tsxtractor.feature_names(features=["mean", "variance", "std", "maximum"])
    assert custom_names == ["mean", "var", "std", "max"]

    # Alias in feature_names returns canonical name
    custom_alias = tsxtractor.feature_names(features=["standard_deviation", "mean"])
    assert custom_alias == ["std", "mean"]


def test_extract_features_profiles():
    rng = np.random.default_rng(42)
    X = rng.standard_normal((50, 100))

    # Default vs core33
    out_default = tsxtractor.extract_features(X)
    out_core = tsxtractor.extract_features(X, profile="core33")
    np.testing.assert_array_equal(out_default, out_core)

    # Minimal profile
    min_names = tsxtractor.feature_names(profile="minimal")
    out_min = tsxtractor.extract_features(X, profile="minimal")
    assert out_min.shape == (50, len(min_names))

    # Verify minimal columns match core33 corresponding columns
    for col_idx, name in enumerate(min_names):
        core_idx = tsxtractor.feature_names().index(name)
        np.testing.assert_allclose(out_min[:, col_idx], out_default[:, core_idx], rtol=1e-12, atol=1e-12)


def test_extract_features_custom_selection():
    rng = np.random.default_rng(123)
    X = rng.standard_normal((40, 200))
    full = tsxtractor.extract_features(X)
    names = tsxtractor.feature_names()

    requested = ["skewness", "mean", "kurtosis", "autocorr_lag_1", "abs_energy"]
    out_custom = tsxtractor.extract_features(X, features=requested)
    assert out_custom.shape == (40, len(requested))

    for col_idx, name in enumerate(requested):
        full_idx = names.index(name)
        np.testing.assert_allclose(out_custom[:, col_idx], full[:, full_idx], rtol=1e-12, atol=1e-12)


def test_extract_features_invalid_profile_or_features():
    X = np.ones((5, 10))
    with pytest.raises(ValueError, match="unknown profile"):
        tsxtractor.extract_features(X, profile="quantum_ultra")

    with pytest.raises(ValueError, match="unknown feature"):
        tsxtractor.extract_features(X, features=["mean", "bad_feature"])


def test_ragged_and_sliding_profiles():
    rng = np.random.default_rng(999)
    # Ragged CSR
    v = rng.standard_normal(300)
    offsets = np.array([0, 100, 300], dtype=np.int64)

    min_ragged = tsxtractor.extract_features_ragged(v, offsets, profile="minimal")
    assert min_ragged.shape == (2, len(tsxtractor.feature_names(profile="minimal")))

    custom_ragged = tsxtractor.extract_features_ragged(v, offsets, features=["mean", "std"])
    assert custom_ragged.shape == (2, 2)

    # Sliding
    x = rng.standard_normal(150)
    min_sliding = tsxtractor.sliding_features(x, window=50, stride=10, profile="minimal")
    n_windows = (150 - 50) // 10 + 1
    assert min_sliding.shape == (n_windows, len(tsxtractor.feature_names(profile="minimal")))


def test_extract_features_df_profiles():
    pandas = pytest.importorskip("pandas")
    rng = np.random.default_rng(777)
    X = rng.standard_normal((10, 50))

    df_min = tsxtractor.extract_features_df(X, profile="minimal")
    assert list(df_min.columns) == tsxtractor.feature_names(profile="minimal")
    assert len(df_min) == 10

    df_custom = tsxtractor.extract_features_df(X, features=["median", "mean"])
    assert list(df_custom.columns) == ["median", "mean"]
    assert len(df_custom) == 10


def test_minimal_profile_is_faster_than_core33():
    rng = np.random.default_rng(42)
    # 500 series of length 1000: sort and FFT dominate runtime
    X = rng.standard_normal((500, 1000))

    # Warmup
    tsxtractor.extract_features(X[:50], profile="minimal")
    tsxtractor.extract_features(X[:50], profile="core33")

    t0 = time.perf_counter()
    tsxtractor.extract_features(X, profile="minimal")
    t_min = time.perf_counter() - t0

    t0 = time.perf_counter()
    tsxtractor.extract_features(X, profile="core33")
    t_core = time.perf_counter() - t0

    # Minimal should be significantly faster because it skips sort and FFT
    assert t_min < t_core
