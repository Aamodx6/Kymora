import numpy as np
import pytest
import kymora


def test_quantiles_parity():
    rng = np.random.default_rng(1234)
    x = rng.standard_normal((10, 500))
    features = ["quantile_25", "median", "quantile_75"]

    out = kymora.extract_features(x, features=features)
    for i in range(10):
        series = x[i]
        q25_np = np.percentile(series, 25, method="linear")
        median_np = np.percentile(series, 50, method="linear")
        q75_np = np.percentile(series, 75, method="linear")

        assert np.isclose(out[i, 0], q25_np, atol=1e-10)
        assert np.isclose(out[i, 1], median_np, atol=1e-10)
        assert np.isclose(out[i, 2], q75_np, atol=1e-10)


def test_multi_view_extraction():
    rng = np.random.default_rng(42)
    x = rng.standard_normal((5, 200))
    views = ["raw", "diff", "znorm"]
    features = ["mean", "std", "skewness", "median"]

    names = kymora.feature_names(features=features, views=views)
    assert "raw__mean" in names
    assert "diff__mean" in names
    # znorm has mean=0, std=1, and identical skewness, which are pruned under shift/scale invariance
    assert "znorm__mean" not in names
    assert "znorm__std" not in names
    assert "znorm__skewness" not in names
    assert "znorm__median" in names

    out = kymora.extract_features(x, features=features, views=views)
    assert out.shape == (5, len(names))
    assert not np.any(np.isnan(out))


def test_multichannel_extraction():
    rng = np.random.default_rng(42)
    # Shape: (4 samples, 3 channels, 150 timesteps)
    x = rng.standard_normal((4, 3, 150))
    features = ["mean", "std", "kurtosis"]

    names = kymora.feature_names_mc(3, features=features, cross=True)
    out = kymora.extract_features_mc(x, features=features, cross=True)

    assert out.shape == (4, len(names))
    # 3 channels * 3 features = 9 features
    # 3 choose 2 = 3 pairs * 4 cross features = 12 features
    # 4 global cross features = 16 cross features
    # Total = 9 + 16 = 25
    assert len(names) == 25
    assert "ch0__mean" in names
    assert "ch1__std" in names
    assert "cross_corr_peak__ch0_ch1" in names
    assert "cross__mean_abs_corr" in names

    df = kymora.extract_features_mc_df(x, features=features, cross=True)
    assert list(df.columns) == names
    assert df.shape == (4, 25)


def test_multistream_extractor():
    n_streams = 4
    w = 25
    mse = kymora.MultiStreamExtractor(n_streams, w)
    assert mse.window_size == w
    assert mse.n_streams == n_streams
    assert not mse.is_full

    rng = np.random.default_rng(7)
    data = rng.standard_normal((50, n_streams))

    # Push 24 samples: should not be full
    for t in range(w - 1):
        ready = mse.push_many(data[t])
        assert not ready
        assert not mse.is_full

    # Push 25th sample: extractor becomes full
    ready = mse.push_many(data[w - 1])
    assert ready
    assert mse.is_full

    fast_feats = mse.compute(kind="fast")
    assert fast_feats.shape == (n_streams, len(kymora.MultiStreamExtractor.fast_feature_names()))
    assert not np.any(np.isnan(fast_feats))

    all_feats = mse.compute(kind="all")
    assert all_feats.shape == (n_streams, 33)
    assert not np.any(np.isnan(all_feats))

    # Reset single stream
    mse.reset(1)
    # Reset all streams
    mse.reset()
    assert not mse.is_full


def test_supervised_selection():
    rng = np.random.default_rng(42)
    n_samples = 60
    n_features = 20

    # Create synthetic feature matrix
    x = rng.standard_normal((n_samples, n_features))
    # Informative labels aligned with first 3 features
    y = ((x[:, 0] * 2.0 + x[:, 1] * 1.5 - x[:, 2]) > 0).astype(int)

    selected_indices, report = kymora.select_features(x, y, task="classification", fdr=0.10)
    assert isinstance(selected_indices, list)
    assert len(selected_indices) > 0
    assert 0 in selected_indices or 1 in selected_indices

    # Test KymoraSelector scikit-learn transformer
    selector = kymora.KymoraSelector(task="classification", fdr=0.10)
    selector.fit(x, y)
    assert len(selector.selected_indices_) > 0

    x_transformed = selector.transform(x)
    assert x_transformed.shape == (n_samples, len(selector.selected_indices_))

    x_fit_trans = selector.fit_transform(x, y)
    assert np.allclose(x_transformed, x_fit_trans)


def test_wisdom_tuner():
    profile = kymora.tune(shapes=((50, 100),), budget_s=3.0)
    assert profile is not None
    assert "best_config" in profile
    assert "pool" in profile["best_config"]
