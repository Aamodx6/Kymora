"""Tests for Phase 2 features: native f32 inputs, out= parameter, and CSR ragged API."""
import numpy as np
import pytest
import tsxtract


def test_f32_native_input():
    """Verify f32 2D array produces features matching f64 within single-precision tolerance."""
    rng = np.random.default_rng(42)
    X64 = rng.standard_normal((20, 250))
    X32 = X64.astype(np.float32)

    feats_64 = tsxtract.extract_features(X64)
    feats_32 = tsxtract.extract_features(X32)

    assert feats_32.dtype == np.float64
    assert feats_32.shape == (20, 33)

    # Compare features within float32 relative tolerance (1e-5)
    np.testing.assert_allclose(feats_32, feats_64, rtol=1e-5, atol=1e-5)


def test_out_parameter_in_place():
    """Verify out= writes directly in place without extra allocation."""
    rng = np.random.default_rng(42)
    X = rng.standard_normal((15, 200))
    out = np.zeros((15, 33), dtype=np.float64)

    res = tsxtract.extract_features(X, out=out)
    assert res is out
    assert not np.isnan(out).any()
    assert (out != 0.0).any()

    # Verify wrong shape raises ValueError
    bad_out = np.zeros((10, 33), dtype=np.float64)
    with pytest.raises(ValueError):
        tsxtract.extract_features(X, out=bad_out)

    bad_cols = np.zeros((15, 32), dtype=np.float64)
    with pytest.raises(ValueError):
        tsxtract.extract_features(X, out=bad_cols)


def test_extract_features_ragged_csr():
    """Verify extract_features_ragged matches list of 1D series."""
    rng = np.random.default_rng(123)
    s1 = rng.standard_normal(100)
    s2 = rng.standard_normal(250)
    s3 = rng.standard_normal(80)

    # Standard list-of-arrays baseline
    expected = tsxtract.extract_features([s1, s2, s3])

    # CSR representation
    values = np.concatenate([s1, s2, s3])
    offsets = np.array([0, len(s1), len(s1) + len(s2), len(values)], dtype=np.int64)

    got = tsxtract.extract_features_ragged(values, offsets)
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=1e-12)

    # With preallocated out=
    out_buf = np.zeros((3, 33), dtype=np.float64)
    res = tsxtract.extract_features_ragged(values, offsets, out=out_buf)
    assert res is out_buf
    np.testing.assert_allclose(out_buf, expected, rtol=1e-12, atol=1e-12)

    # With f32 values
    got_f32 = tsxtract.extract_features_ragged(values.astype(np.float32), offsets)
    np.testing.assert_allclose(got_f32, expected, rtol=1e-5, atol=1e-5)
