"""Input surface matrix: shapes, dtypes, layouts, contiguity (Phases 3.4 + 3.5).

Zero-copy contract (code-level: every input is an `as_slice` borrow; see
`src/ffi.rs` "Strict C-contiguity rule"). Behavioral proofs in this file:

- C-contiguous float64/float32 work everywhere, including read-only and
  memmapped buffers (a forcing copy would also accept these, so this
  documents support rather than proving zero-copy).
- Fortran-ordered / strided / negative-stride inputs are REJECTED by default
  (proving no silent copy: a copying implementation would accept them) and
  produce bit-identical results under the explicit `contiguous="copy"`
  opt-in, which emits one `UserWarning` per call site.
- `out=` buffers obey the same layout rule (a Fortran `out=` previously
  received row-major writes into column-major memory silently).
- Adversarial inputs never panic: hypothesis fuzz asserts every call either
  returns a correctly shaped array or raises ValueError/TypeError. A Rust
  panic surfaces as `pyo3_runtime.PanicException` (a BaseException), which
  these tests deliberately do not catch.
"""

import warnings

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import kymora

N_FEATURES = len(kymora.feature_names())


def test_copy_warning_fires_once_per_module():
    # THE warning test of this module: must run before any other
    # contiguous="copy" call in this file (Python shows default-filtered
    # warnings once per module).
    rng = np.random.default_rng(0)
    X = np.ascontiguousarray(rng.standard_normal((4, 50)))
    with pytest.warns(UserWarning, match="ascontiguousarray"):
        kymora.extract_features(X[:, ::2], contiguous="copy")


def _nocopy_warn(fn, *args, **kwargs):
    """Run a `contiguous='copy'` call while suppressing its UserWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fn(*args, contiguous="copy", **kwargs)


def test_strided_and_fortran_rejected_by_default():
    rng = np.random.default_rng(1)
    X = np.ascontiguousarray(rng.standard_normal((4, 50)))
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features(X[:, ::2])
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features(np.asfortranarray(X))
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features(X[::-1])
    with pytest.raises(ValueError, match="contiguous"):
        kymora.extract_features(X, contiguous="bogus")


def test_copy_matches_contiguous():
    rng = np.random.default_rng(2)
    X = np.ascontiguousarray(rng.standard_normal((4, 50)))
    cases = [
        X[:, ::2],
        np.asfortranarray(X),
        np.ascontiguousarray(X[::-1]),
    ]
    for bad in cases:
        want = kymora.extract_features(np.ascontiguousarray(bad))
        got = _nocopy_warn(kymora.extract_features, bad)
        np.testing.assert_array_equal(got, want)


def test_copy_f32_and_list_and_ragged():
    rng = np.random.default_rng(3)
    X = np.ascontiguousarray(rng.standard_normal((4, 50)).astype(np.float32))
    ref = kymora.extract_features(X)
    got = _nocopy_warn(kymora.extract_features, np.asfortranarray(X))
    np.testing.assert_array_equal(got, ref)

    rows = [np.ascontiguousarray(r) for r in X]
    rows[1] = rows[1][::2]
    got_list = _nocopy_warn(kymora.extract_features, rows)
    want_list = kymora.extract_features(
        [np.ascontiguousarray(r) for r in (X[0], X[1][::2], X[2], X[3])]
    )
    np.testing.assert_array_equal(got_list, want_list)

    values = np.ascontiguousarray(rng.standard_normal(200))
    offsets = np.array([0, 50, 120, 200], dtype=np.int64)
    ref_rag = kymora.extract_features_ragged(values, offsets)
    np.testing.assert_array_equal(
        _nocopy_warn(kymora.extract_features_ragged, values, offsets), ref_rag
    )
    inter = np.empty(8, dtype=np.int64)
    inter[::2] = offsets
    strided_offsets = inter[::2]
    assert not strided_offsets.flags["C_CONTIGUOUS"]
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features_ragged(values, strided_offsets)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got_off = kymora.extract_features_ragged(values, strided_offsets, contiguous="copy")
    np.testing.assert_array_equal(got_off, ref_rag)


def test_copy_sliding_and_mc():
    rng = np.random.default_rng(4)
    x = np.ascontiguousarray(rng.standard_normal(200))
    ref = kymora.sliding_features(x, window=20, stride=5)
    np.testing.assert_array_equal(
        _nocopy_warn(kymora.sliding_features, x[::2], window=10, stride=5),
        kymora.sliding_features(np.ascontiguousarray(x[::2]), window=10, stride=5),
    )
    assert ref.shape == (37, N_FEATURES)

    X = np.ascontiguousarray(rng.standard_normal((2, 3, 60)))
    ref_mc = kymora.extract_features_mc(X)
    got_mc = _nocopy_warn(kymora.extract_features_mc, np.asfortranarray(X))
    np.testing.assert_array_equal(got_mc, ref_mc)

    elems = [np.ascontiguousarray(X[i]) for i in range(2)]
    elems[0] = np.asfortranarray(elems[0])
    got_list = _nocopy_warn(kymora.extract_features_mc, elems)
    np.testing.assert_array_equal(got_list, ref_mc)


def test_out_layout_checked():
    rng = np.random.default_rng(5)
    X = np.ascontiguousarray(rng.standard_normal((4, 50)))
    ref = kymora.extract_features(X)
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features(X, out=np.asfortranarray(np.zeros((4, N_FEATURES))))
    strided_out = np.zeros((4, 2 * N_FEATURES))[:, ::2]
    assert not strided_out.flags["C_CONTIGUOUS"]
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        kymora.extract_features(X, out=strided_out)
    out = np.zeros((4, N_FEATURES))
    res = kymora.extract_features(X, out=out)
    assert res is out
    np.testing.assert_array_equal(out, ref)


def test_dtype_and_shape_matrix():
    rng = np.random.default_rng(6)
    X = np.ascontiguousarray(rng.standard_normal((4, 50)))
    # Wrong dtypes raise TypeError with a cast hint.
    for bad in (
        np.zeros((4, 50), dtype=np.int64),
        np.zeros((4, 50), dtype=np.float16),
        np.zeros((4, 50), dtype=object),
    ):
        with pytest.raises(TypeError):
            kymora.extract_features(bad)
    # Wrong shapes raise.
    with pytest.raises(TypeError):
        kymora.extract_features(np.ascontiguousarray(rng.standard_normal(50)))
    with pytest.raises(ValueError):
        kymora.extract_features(np.zeros((0, 50)))
    with pytest.raises(ValueError):
        kymora.extract_features([np.array([], dtype=np.float64)])
    with pytest.raises(ValueError):
        kymora.extract_features([])
    # Read-only and memmapped buffers are borrowed without copying.
    ro = X.copy()
    ro.flags.writeable = False
    np.testing.assert_array_equal(kymora.extract_features(ro), kymora.extract_features(X))
    import tempfile, os

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.dat")
        mm = np.memmap(path, dtype=np.float64, mode="w+", shape=X.shape)
        mm[:] = X[:]
        mm.flush()
        del mm
        ro_mm = np.memmap(path, dtype=np.float64, mode="r", shape=X.shape)
        try:
            np.testing.assert_array_equal(kymora.extract_features(ro_mm), kymora.extract_features(X))
        finally:
            del ro_mm
    # Window geometry edges.
    one = kymora.sliding_features(X[0], window=50)
    assert one.shape == (1, N_FEATURES)
    with pytest.raises(ValueError):
        kymora.sliding_features(X[0], window=51)
    with pytest.raises(ValueError):
        kymora.sliding_features(X[0], window=0)
    with pytest.raises(ValueError):
        kymora.sliding_features(np.array([], dtype=np.float64), window=1)


def test_push_many_contiguous():
    mse = kymora.MultiStreamExtractor(4, 8)
    v = np.arange(8.0)[::2]
    assert not v.flags["C_CONTIGUOUS"]
    assert mse.push_many(np.ascontiguousarray(v)) is False
    with pytest.raises(ValueError, match="[Cc]ontiguous"):
        mse.push_many(v)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert mse.push_many(v, contiguous="copy") is False


HYP_SETTINGS = settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)


@HYP_SETTINGS
@given(
    rows=st.integers(min_value=1, max_value=8),
    cols=st.integers(min_value=1, max_value=40),
    kind=st.sampled_from(["c", "f", "strided", "neg"]),
)
def test_hypothesis_layout_never_panics(rows, cols, kind):
    base = np.arange(rows * cols, dtype=np.float64).reshape(rows, cols)
    if kind == "c":
        x = np.ascontiguousarray(base)
    elif kind == "f":
        x = np.asfortranarray(base)
    elif kind == "strided":
        x = np.ascontiguousarray(base)[:, ::2] if cols > 1 else base
    else:
        x = np.ascontiguousarray(base)[::-1]
    try:
        out = kymora.extract_features(x)
    except (ValueError, TypeError):
        return
    assert out.shape == (rows, 33)


@HYP_SETTINGS
@given(
    data=st.lists(
        st.floats(allow_nan=True, allow_infinity=True, width=32),
        min_size=1,
        max_size=30,
    ),
)
def test_hypothesis_f32_ragged_values_never_panic(data):
    values = np.asarray(data, dtype=np.float32)
    offsets = np.array([0, len(data)], dtype=np.int64)
    try:
        out = kymora.extract_features_ragged(values, offsets)
    except (ValueError, TypeError):
        return
    assert out.shape == (1, 33)
