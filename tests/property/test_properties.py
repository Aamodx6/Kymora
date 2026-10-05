"""Property-based robustness tests.

Purpose is different from the reference tests: these do not check that any
feature is *correct*, they check that the boundary is *unbreakable*. For every
input hypothesis can construct, the call must either return an array of the right
shape or raise a normal Python exception — never a Rust panic, never a crash,
never a silently wrong shape.

A Rust panic reaches Python as ``pyo3_runtime.PanicException``, which subclasses
``BaseException`` rather than ``Exception``. Every test here therefore catches
``Exception`` narrowly, so a panic escapes and fails the test instead of being
mistaken for correct error handling.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

import kymora

NAMES = kymora.feature_names()
N_FEATURES = len(NAMES)

SETTINGS = settings(
    max_examples=200,
    deadline=None,  # release-build FFI calls plus CI noise make wall-clock deadlines flaky
    suppress_health_check=[HealthCheck.too_slow],
)

# --- element strategies, one per required edge-case family -------------------

finite_floats = st.floats(allow_nan=False, allow_infinity=False, width=64)
huge_floats = st.floats(min_value=1e290, max_value=1.7e308, allow_nan=False, width=64)
tiny_floats = st.floats(min_value=1e-308, max_value=1e-290, allow_nan=False, width=64)
negative_floats = st.floats(max_value=-1e-10, allow_nan=False, allow_infinity=False, width=64)
messy_floats = st.floats(allow_nan=True, allow_infinity=True, width=64)

elements = st.one_of(
    finite_floats,
    huge_floats,
    st.builds(lambda v: -v, huge_floats),
    tiny_floats,
    negative_floats,
    messy_floats,
    st.just(0.0),
    st.just(-0.0),
    st.just(np.nan),
)


def series(min_size=1, max_size=64, elems=elements):
    return hnp.arrays(
        dtype=np.float64,
        shape=st.integers(min_value=min_size, max_value=max_size),
        elements=elems,
    )


# --- degenerate series that must be exercised explicitly, not just randomly ---

DEGENERATE = st.one_of(
    st.builds(np.zeros, st.integers(1, 40)),
    st.builds(lambda n: np.full(n, np.nan), st.integers(1, 40)),
    st.builds(lambda n, v: np.full(n, v), st.integers(1, 40), finite_floats),
    st.builds(lambda v: np.array([v]), elements),
    st.builds(lambda n: np.full(n, 1.7e308), st.integers(1, 40)),
    st.builds(lambda n: -np.arange(1.0, n + 1.0), st.integers(1, 40)),
)


# ---------------------------------------------------------------------------
# Single series: shape, robustness, NaN policy
# ---------------------------------------------------------------------------


@SETTINGS
@given(x=st.one_of(series(), DEGENERATE))
def test_single_series_shape_and_no_panic(x):
    out = kymora.extract_features([x])
    assert out.shape == (1, N_FEATURES)
    assert out.dtype == np.float64


@SETTINGS
@given(x=st.one_of(series(), DEGENERATE))
def test_nan_policy_holds_for_finite_input(x):
    """For an input free of NaN and inf, the all-NaN row is reserved exclusively
    for NaN-containing input — so it must never appear here."""
    assume(np.isfinite(x).all())
    row = kymora.extract_features([x])[0]
    assert not np.isnan(row).all()
    assert not np.isnan(row[NAMES.index("mean")])


@SETTINGS
@given(x=series(elems=finite_floats), i=st.integers(0, 63))
def test_injected_nan_always_produces_a_full_nan_row(x, i):
    x = x.copy()
    x[i % len(x)] = np.nan
    row = kymora.extract_features([x])[0]
    assert np.isnan(row).all()


@SETTINGS
@given(x=st.one_of(series(), DEGENERATE))
def test_extraction_is_deterministic(x):
    """Parallel reduction order must not leak into the result."""
    a = kymora.extract_features([x])
    b = kymora.extract_features([x])
    np.testing.assert_array_equal(a, b)


# ---------------------------------------------------------------------------
# Batches: the parallel path must agree with the serial one
# ---------------------------------------------------------------------------


@SETTINGS
@given(batch=st.lists(st.one_of(series(), DEGENERATE), min_size=1, max_size=12))
def test_ragged_batch_equals_per_series_extraction(batch):
    together = kymora.extract_features(batch)
    assert together.shape == (len(batch), N_FEATURES)
    for i, x in enumerate(batch):
        alone = kymora.extract_features([x])[0]
        np.testing.assert_array_equal(together[i], alone, err_msg=f"series {i}")


@SETTINGS
@given(
    batch=hnp.arrays(
        dtype=np.float64,
        shape=st.tuples(st.integers(1, 12), st.integers(1, 48)),
        elements=elements,
    )
)
def test_2d_path_equals_ragged_path(batch):
    np.testing.assert_array_equal(
        kymora.extract_features(batch),
        kymora.extract_features(list(batch)),
    )


@SETTINGS
@given(batch=st.lists(st.one_of(series(), DEGENERATE), min_size=2, max_size=10))
def test_batch_order_permutes_rows_but_not_values(batch):
    straight = kymora.extract_features(batch)
    reversed_ = kymora.extract_features(batch[::-1])
    np.testing.assert_array_equal(straight, reversed_[::-1])


@SETTINGS
@given(
    batch=hnp.arrays(
        dtype=np.float64,
        shape=st.tuples(st.integers(1, 12), st.integers(1, 48)),
        elements=elements,
    )
)
def test_results_bitwise_identical_across_thread_counts(batch):
    """arch I7: per-series independence => bitwise identical whatever the
    thread count or scheduling (also covers the cached-pool path)."""
    ref = kymora.extract_features(batch, n_jobs=1)
    for n_jobs in (2, 8, None):
        np.testing.assert_array_equal(
            kymora.extract_features(batch, n_jobs=n_jobs), ref
        )


# ---------------------------------------------------------------------------
# sliding_features: geometry is a hard contract
# ---------------------------------------------------------------------------


@SETTINGS
@given(
    x=series(min_size=1, max_size=80),
    window=st.integers(1, 80),
    stride=st.integers(1, 20),
)
def test_sliding_features_either_raises_valueerror_or_returns_exact_shape(x, window, stride):
    if window > len(x):
        with pytest.raises(ValueError):
            kymora.sliding_features(x, window=window, stride=stride)
        return
    out = kymora.sliding_features(x, window=window, stride=stride)
    assert out.shape == ((len(x) - window) // stride + 1, N_FEATURES)


@SETTINGS
@given(
    x=series(min_size=1, max_size=60),
    window=st.integers(1, 60),
    stride=st.integers(1, 10),
)
def test_sliding_window_rows_equal_extracting_those_windows(x, window, stride):
    assume(window <= len(x))
    out = kymora.sliding_features(x, window=window, stride=stride)
    starts = range(0, len(x) - window + 1, stride)
    manual = kymora.extract_features([x[s : s + window] for s in starts])
    np.testing.assert_array_equal(out, manual)


@SETTINGS
@given(
    x=series(min_size=1, max_size=40),
    window=st.integers(-2**40, 0),
    stride=st.integers(-2**40, 0),
)
def test_sliding_features_rejects_non_positive_geometry(x, window, stride):
    with pytest.raises(ValueError):
        kymora.sliding_features(x, window=window, stride=stride)


# ---------------------------------------------------------------------------
# Structurally invalid input must raise, never panic
# ---------------------------------------------------------------------------


@SETTINGS
@given(
    batch=st.lists(st.one_of(series(max_size=20), DEGENERATE), min_size=0, max_size=6),
    empty_at=st.integers(0, 6),
)
def test_zero_length_series_anywhere_in_a_batch_raises_value_error(batch, empty_at):
    batch = list(batch)
    batch.insert(min(empty_at, len(batch)), np.array([], dtype=np.float64))
    with pytest.raises(ValueError):
        kymora.extract_features(batch)


@SETTINGS
@given(
    shape=st.tuples(st.integers(0, 5), st.integers(0, 5)).filter(lambda s: 0 in s),
)
def test_degenerate_2d_shapes_raise_value_error(shape):
    with pytest.raises(ValueError):
        kymora.extract_features(np.zeros(shape))


@SETTINGS
@given(
    x=hnp.arrays(
        dtype=st.sampled_from([np.int32, np.int64, np.complex128]),
        shape=st.tuples(st.integers(1, 5), st.integers(1, 10)),
    )
)
def test_wrong_dtype_raises_type_error(x):
    with pytest.raises(TypeError):
        kymora.extract_features(x)


@SETTINGS
@given(
    x=hnp.arrays(
        dtype=np.float64,
        shape=st.one_of(
            st.tuples(st.integers(1, 8)),
            st.tuples(st.integers(1, 4), st.integers(1, 4), st.integers(1, 4)),
        ),
        elements=finite_floats,
    )
)
def test_wrong_dimensionality_raises_type_error(x):
    with pytest.raises(TypeError):
        kymora.extract_features(x)


@SETTINGS
@given(x=series(min_size=4, max_size=64, elems=finite_floats), step=st.integers(2, 5))
def test_non_contiguous_views_raise_value_error(x, step):
    view = x[::step]
    # A view with 0 or 1 elements is still flagged contiguous by numpy, so the
    # stride is unobservable and there is correctly nothing to reject.
    assume(len(view) >= 2)
    assert not view.flags["C_CONTIGUOUS"]
    with pytest.raises(ValueError):
        kymora.sliding_features(view, window=1)
