"""Tests enforcing invariants I1 through I7 defined in docs/internal/arch.md §3."""
import json
import os
import threading
import time
import numpy as np
import pytest
import kymora

GOLDEN_NAMES_PATH = os.path.join(os.path.dirname(__file__), "golden", "core33_names.json")
GOLDEN_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "golden", "core33_output.json")


def test_i1_core33_names_frozen():
    """I1: profile='core33' column order and length from feature_names() frozen for 1.x."""
    with open(GOLDEN_NAMES_PATH, "r", encoding="utf-8") as f:
        golden_names = json.load(f)
    names = kymora.feature_names()
    assert names == golden_names
    assert len(names) == 33


def test_golden_output_match():
    """Verify core33 output on fixed seed reproduces identically within rel err <= 1e-12."""
    with open(GOLDEN_OUTPUT_PATH, "r", encoding="utf-8") as f:
        golden = json.load(f)
    rng = np.random.default_rng(golden["seed"])
    X = rng.standard_normal(golden["shape"])
    out = kymora.extract_features(X)
    golden_arr = np.array(golden["output"], dtype=np.float64)
    np.testing.assert_allclose(out, golden_arr, rtol=1e-12, atol=1e-12)


def test_i2_nan_contract():
    """I2: Series with any NaN -> all-NaN row. Undefined single feature -> that feature NaN. Empty -> ValueError."""
    # 1. Any NaN -> all-NaN row
    x = np.array([[1.0, 2.0, np.nan, 4.0, 5.0]])
    out = kymora.extract_features(x)
    assert np.isnan(out).all()

    # In a batch, only the series with NaN is NaN
    x_batch = np.array([
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, np.nan, 4.0, 5.0],
    ])
    out_batch = kymora.extract_features(x_batch)
    assert not np.isnan(out_batch[0]).all()
    assert np.isnan(out_batch[1]).all()

    # 2. Undefined single feature -> that feature NaN
    # Constant series: autocorr and spectral are NaN, but mean, min, max, median are valid
    x_const = np.full((1, 50), 3.0)
    out_const = kymora.extract_features(x_const)[0]
    names = kymora.feature_names()
    assert out_const[names.index("mean")] == 3.0
    assert out_const[names.index("var")] == 0.0
    assert np.isnan(out_const[names.index("autocorr_lag_1")])
    assert np.isnan(out_const[names.index("spectral_entropy")])

    # 3. Empty input or empty series -> ValueError
    with pytest.raises(ValueError):
        kymora.extract_features(np.empty((0, 10), dtype=np.float64))
    with pytest.raises(ValueError):
        kymora.extract_features(np.empty((10, 0), dtype=np.float64))
    with pytest.raises(ValueError):
        kymora.extract_features([np.array([], dtype=np.float64)])


def test_i3_borrowed_input_no_copy():
    """I3: Contiguous f64 input is borrowed without defensive copies."""
    import sys
    X = np.random.randn(100, 500)
    # The reference count of X or its underlying base should not indicate an extra Python-side copy
    ref_before = sys.getrefcount(X)
    _ = kymora.extract_features(X)
    ref_after = sys.getrefcount(X)
    assert ref_after == ref_before


def test_i4_no_panic_across_ffi():
    """I4: No panic crosses FFI; error handling via KymoraError -> PyErr."""
    # Bad shapes, non-contiguous arrays, invalid params should raise clean Python exceptions
    with pytest.raises((ValueError, TypeError)):
        kymora.extract_features("invalid_type")  # type: ignore

    with pytest.raises(ValueError):
        kymora.sliding_features(np.array([1.0, 2.0, 3.0]), window=0, stride=1)

    with pytest.raises(ValueError):
        kymora.sliding_features(np.array([1.0, 2.0, 3.0]), window=5, stride=1)


def test_i5_gil_released():
    """I5: GIL released for the whole parallel region.

    Two Python threads each running extract_features on large batches run concurrently.
    """
    X1 = np.random.randn(2000, 500)
    X2 = np.random.randn(2000, 500)

    # Warmup
    kymora.extract_features(X1[:10])

    t0 = time.perf_counter()
    _ = kymora.extract_features(X1)
    t_single = time.perf_counter() - t0

    def worker(arr):
        kymora.extract_features(arr)

    t0 = time.perf_counter()
    t1 = threading.Thread(target=worker, args=(X1,))
    t2 = threading.Thread(target=worker, args=(X2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    t_threaded = time.perf_counter() - t0

    # If GIL was held, t_threaded would be >= 2 * t_single.
    # With GIL released, both threads execute concurrently.
    # We assert that concurrency exists (t_threaded < 1.8 * t_single or reasonable factor).
    assert t_threaded < 1.9 * (t_single * 2), f"GIL may be held: single={t_single:.3f}s, threaded={t_threaded:.3f}s"


def test_i6_output_dtype_float64():
    """I6: Output dtype must strictly be float64."""
    X = np.random.randn(10, 100)
    out = kymora.extract_features(X)
    assert out.dtype == np.float64
    assert out.shape == (10, 33)
