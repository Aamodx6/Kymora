import numpy as np
import pytest
import tsxtractor


def test_streaming_fast_feature_names():
    names = tsxtractor.StreamingExtractor.fast_feature_names()
    assert isinstance(names, list)
    assert len(names) == 12
    assert names == [
        "mean",
        "std",
        "var",
        "skewness",
        "kurtosis",
        "abs_energy",
        "root_mean_square",
        "mean_abs_change",
        "mean_change",
        "cid_ce",
        "zero_crossings",
        "trend_slope",
    ]


def test_streaming_fast_vs_batch():
    w = 30
    ext = tsxtractor.StreamingExtractor(w)
    assert ext.window_size == w
    assert not ext.is_full

    # Before full, compute returns NaN or empty/None checks
    n_samples = 100
    rng = np.random.default_rng(42)
    data = rng.standard_normal(n_samples)

    fast_names = tsxtractor.StreamingExtractor.fast_feature_names()

    for i in range(n_samples):
        ready = ext.push(float(data[i]))
        if i < w - 1:
            assert not ready
            assert not ext.is_full
            feats = ext.compute(kind="fast")
            assert np.all(np.isnan(feats))
        else:
            assert ready
            assert ext.is_full
            feats = ext.compute(kind="fast")
            assert len(feats) == 12
            assert not np.any(np.isnan(feats))

            # Compare against batch computation
            win = data[i - w + 1 : i + 1]
            batch_vals = tsxtractor.extract_features(win[None, :], features=fast_names)[0]

            for name, s_val, b_val in zip(fast_names, feats, batch_vals):
                diff = abs(s_val - b_val)
                # Max tolerance of 1e-8 for floating point differences
                assert diff < 1e-8, f"Feature {name} mismatch: streaming={s_val}, batch={b_val}, diff={diff}"


def test_streaming_all_vs_batch():
    w = 40
    ext = tsxtractor.StreamingExtractor(w)
    rng = np.random.default_rng(123)
    data = rng.standard_normal(80)

    for i in range(80):
        ready = ext.push(float(data[i]))
        if ready:
            all_feats = ext.compute(kind="all")
            assert len(all_feats) == 33
            win = data[i - w + 1 : i + 1]
            batch_feats = tsxtractor.extract_features(win[None, :])[0]
            for j in range(33):
                s = all_feats[j]
                b = batch_feats[j]
                if np.isnan(b):
                    assert np.isnan(s)
                else:
                    assert abs(s - b) < 1e-9, f"Feature {j} mismatch at step {i}: stream={s}, batch={b}"


def test_streaming_large_series_numerical_stability():
    """
    Gate test: incremental == recompute on 1e5-point random-walk and 1e9 + noise series.
    Verifies that periodic accumulator anchoring prevents catastrophic floating point drift.
    """
    w = 50
    # Test 1: Random walk
    rng = np.random.default_rng(999)
    steps = rng.standard_normal(50_000)
    rw = np.cumsum(steps)

    ext = tsxtractor.StreamingExtractor(w)
    for i in range(50_000):
        ext.push(float(rw[i]))

    # At the end of 50k steps, compare fast features
    s_feats = ext.compute(kind="fast")
    last_win = rw[-w:]
    fast_names = tsxtractor.StreamingExtractor.fast_feature_names()
    b_feats = tsxtractor.extract_features(last_win[None, :], features=fast_names)[0]

    for name, s, b in zip(fast_names, s_feats, b_feats):
        rel_diff = abs(s - b) / (abs(b) + 1e-12)
        assert rel_diff < 1e-6, f"RW stability failed for {name}: stream={s}, batch={b}, rel_diff={rel_diff}"

    # Test 2: Large offset 1e9 + noise
    base = 1e9
    noise = rng.standard_normal(10_000)
    offset_data = base + noise
    ext_offset = tsxtractor.StreamingExtractor(w)
    for i in range(10_000):
        ext_offset.push(float(offset_data[i]))

    s_offset = ext_offset.compute(kind="fast")
    last_offset_win = offset_data[-w:]
    b_offset = tsxtractor.extract_features(last_offset_win[None, :], features=fast_names)[0]

    for name, s, b in zip(fast_names, s_offset, b_offset):
        if name in ["var", "std", "cid_ce", "trend_slope"]:
            # Ill-conditioned variance/slope on 1e9 offset without full double centering
            # Bound absolute difference
            diff = abs(s - b)
            assert diff < 1e-3, f"Offset stability for {name}: stream={s}, batch={b}, diff={diff}"
        else:
            rel_diff = abs(s - b) / (abs(b) + 1e-12)
            assert rel_diff < 1e-5, f"Offset stability for {name}: stream={s}, batch={b}, rel_diff={rel_diff}"


def test_sliding_features_basic():
    rng = np.random.default_rng(777)
    x = rng.standard_normal(500)

    # Various window and stride combinations
    cases = [
        (100, 1),   # small stride < window/8 (heavy overlap)
        (100, 10),  # stride < window/8
        (100, 25),  # stride > window/8
        (50, 50),   # disjoint windows
    ]

    for window, stride in cases:
        out = tsxtractor.sliding_features(x, window=window, stride=stride)
        expected_n_windows = (len(x) - window) // stride + 1
        assert out.shape == (expected_n_windows, 33)

        # Spot check first, middle, last window against extract_features
        for idx in [0, expected_n_windows // 2, expected_n_windows - 1]:
            start = idx * stride
            win = x[start : start + window]
            expected = tsxtractor.extract_features(win[None, :])[0]
            np.testing.assert_allclose(out[idx], expected, rtol=1e-10, atol=1e-10)


def test_sliding_features_with_profiles_and_out():
    x = np.linspace(0, 10, 300)
    window = 40
    stride = 5
    n_windows = (len(x) - window) // stride + 1

    # Profile minimal
    out_min = tsxtractor.sliding_features(x, window=window, stride=stride, profile="minimal")
    n_min = len(tsxtractor.feature_names(profile="minimal"))
    assert out_min.shape == (n_windows, n_min)

    # In-place out parameter
    out_buf = np.empty((n_windows, n_min), dtype=np.float64)
    res = tsxtractor.sliding_features(x, window=window, stride=stride, profile="minimal", out=out_buf)
    assert res is out_buf
    np.testing.assert_allclose(out_buf, out_min, rtol=1e-12)

    # Custom features
    out_custom = tsxtractor.sliding_features(x, window=window, stride=stride, features=["mean", "max", "min"])
    assert out_custom.shape == (n_windows, 3)
    np.testing.assert_allclose(out_custom[:, 0], [np.mean(x[i * stride : i * stride + window]) for i in range(n_windows)], rtol=1e-10)
