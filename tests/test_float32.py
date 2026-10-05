"""float32 input support end to end (Phase 3.2).

- f32 2D / list / CSR-ragged read natively (zero-copy borrow, no `astype`
  round-trip) with float64 accumulation; results match the float64 pipeline
  on the same values within f32-arithmetic tolerance (measured max 8.8e-6,
  bound 1e-4).
- float64 path is unchanged and bit-identical (golden tests).
- f32 covers core33, `minimal`, and core33 subsets via gather; `extended`,
  `full`, and non-raw views raise ValueError (never a panic).
- `precision` is validated; `out_dtype="float32"` casts on write.
"""

import numpy as np
import pytest

import kymora

NAMES = kymora.feature_names()

# Measured max f32-vs-f64 rel diff 8.8e-6 (mean_second_derivative_central);
# bound below carries >10x margin.
F32_RTOL = 1e-4


@pytest.fixture()
def rng_data():
    rng = np.random.default_rng(20261005)
    x64 = np.ascontiguousarray(rng.standard_normal((20, 500)))
    x32 = np.ascontiguousarray(x64.astype(np.float32))
    return x64, x32


def test_f32_core33_matches_f64(rng_data):
    x64, x32 = rng_data
    got = kymora.extract_features(x32)
    want = kymora.extract_features(x64)
    assert got.dtype == np.float64
    assert got.shape == want.shape
    for j, name in enumerate(NAMES):
        np.testing.assert_allclose(
            got[:, j], want[:, j], rtol=F32_RTOL, atol=1e-9, err_msg=name
        )


def test_f32_matches_f64_on_same_values(rng_data):
    # Same mathematical values through both kernel sets: widen the f32 input
    # exactly and compare against the f32 path.
    _, x32 = rng_data
    got = kymora.extract_features(x32)
    want = kymora.extract_features(np.ascontiguousarray(x32.astype(np.float64)))
    for j, name in enumerate(NAMES):
        np.testing.assert_allclose(
            got[:, j], want[:, j], rtol=F32_RTOL, atol=1e-12, err_msg=name
        )


def test_f32_minimal_and_subset(rng_data):
    x64, x32 = rng_data
    for kwargs in ({"profile": "minimal"}, {"features": ["mean", "std", "max"]}):
        got = kymora.extract_features(x32, **kwargs)
        want = kymora.extract_features(x64, **kwargs)
        assert got.shape == want.shape
        np.testing.assert_allclose(got, want, rtol=F32_RTOL, atol=1e-9)


def test_f32_extended_full_views_rejected_without_panic(rng_data):
    _, x32 = rng_data
    with pytest.raises(ValueError, match="float32"):
        kymora.extract_features(x32, profile="extended")
    with pytest.raises(ValueError, match="float32"):
        kymora.extract_features(x32, profile="full")
    with pytest.raises(ValueError, match="float32"):
        kymora.extract_features(x32, views=["diff"])
    with pytest.raises(ValueError, match="float32"):
        kymora.extract_features(x32, features=["sum_values"])


def test_f32_list_and_ragged(rng_data):
    _, x32 = rng_data
    rows = [np.ascontiguousarray(r) for r in x32[:5]]
    got = kymora.extract_features(rows)
    want = kymora.extract_features([np.ascontiguousarray(r.astype(np.float64)) for r in rows])
    np.testing.assert_allclose(got, want, rtol=F32_RTOL, atol=1e-12)

    lengths = [50, 120, 500, 33]
    parts = [np.ascontiguousarray(np.random.default_rng(i).standard_normal(n).astype(np.float32)) for i, n in enumerate(lengths)]
    values = np.ascontiguousarray(np.concatenate(parts))
    offsets = np.array([0, 50, 170, 670, 703], dtype=np.int64)
    got_rag = kymora.extract_features_ragged(values, offsets)
    assert got_rag.shape == (4, 33)
    for i, n in enumerate(lengths):
        want_row = kymora.extract_features(parts[i][None, :].astype(np.float64))[0]
        np.testing.assert_allclose(got_rag[i], want_row, rtol=F32_RTOL, atol=1e-12)
    with pytest.raises(ValueError, match="float32"):
        kymora.extract_features_ragged(values, offsets, profile="extended")


def test_f32_out_dtype(rng_data):
    x64, x32 = rng_data
    got = kymora.extract_features(x32, out_dtype="float32")
    assert got.dtype == np.float32
    want = kymora.extract_features(x64)
    np.testing.assert_allclose(got.astype(np.float64), want, rtol=1e-3, atol=1e-6)
    got64 = kymora.extract_features(x32, out_dtype="float64")
    assert got64.dtype == np.float64


def test_precision_validated(rng_data):
    x64, x32 = rng_data
    kymora.extract_features(x64, precision=None)
    for p in ("float64", "f64"):
        kymora.extract_features(x64, precision=p)
    for p in ("float32", "f32"):
        kymora.extract_features(x32, precision=p)
    with pytest.raises(ValueError, match="unknown precision"):
        kymora.extract_features(x64, precision="float16")


def test_f32_layout_and_nan(rng_data):
    x64, x32 = rng_data
    # Fortran order is rejected, never silently copied.
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features(np.asfortranarray(x32))
    # Read-only contiguous input works (borrowed, not copied).
    x32.flags.writeable = False
    got = kymora.extract_features(x32)
    assert got.shape == (20, 33)
    # NaN contract identical to float64.
    bad = x32.copy()
    bad[3, 10] = np.nan
    assert np.isnan(kymora.extract_features(bad)[3]).all()
    with pytest.raises(ValueError, match="batch index 3"):
        kymora.extract_features(bad, nan_policy="raise")


def test_f32_small_batch_threading(rng_data):
    # Fewer than SERIAL_THRESHOLD rows exercises the serial gather path too.
    _, x32 = rng_data
    got = kymora.extract_features(x32[:3], features=["mean", "var", "trend_slope"])
    assert got.shape == (3, 3)
    want = kymora.extract_features(x32[:3].astype(np.float64), features=["mean", "var", "trend_slope"])
    np.testing.assert_allclose(got, want, rtol=F32_RTOL, atol=1e-12)
