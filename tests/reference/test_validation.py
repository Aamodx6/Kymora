"""Structural error handling at the PyO3 boundary.

These tests lock down the *structural* half of the error model (architecture §5):
bad shapes, lengths, and window geometry raise Python exceptions, and no Rust
panic ever crosses the boundary. The value half — NaN as a legitimate input — is
covered separately in ``test_nan_policy.py``; nothing here should depend on the
values inside a series.
"""

import numpy as np
import pytest

import kymora

N_FEATURES = 33


# --- empty input: no series at all -------------------------------------------


@pytest.mark.parametrize(
    "X",
    [
        pytest.param([], id="empty_list"),
        pytest.param(np.zeros((0, 10)), id="zero_rows_2d"),
    ],
)
def test_empty_input_raises_value_error(X):
    with pytest.raises(ValueError, match="no series"):
        kymora.extract_features(X)


# --- zero-length series: structural error, NOT a NaN row ---------------------


def test_zero_length_series_in_list_raises():
    with pytest.raises(ValueError, match="length 0"):
        kymora.extract_features([np.array([], dtype=np.float64)])


def test_zero_length_series_reports_its_index():
    batch = [np.arange(5.0), np.arange(3.0), np.array([], dtype=np.float64)]
    with pytest.raises(ValueError, match="index 2"):
        kymora.extract_features(batch)


def test_zero_column_2d_raises():
    with pytest.raises(ValueError, match="0 columns"):
        kymora.extract_features(np.zeros((3, 0)))


def test_single_element_series_is_valid_not_an_error():
    """Length 1 is legal; only length 0 is structurally invalid."""
    out = kymora.extract_features([np.array([5.0])])
    assert out.shape == (1, N_FEATURES)


# --- layout ------------------------------------------------------------------


def test_non_contiguous_2d_rejected_with_actionable_message():
    X = np.zeros((10, 10))[:, ::2]
    with pytest.raises(ValueError, match="ascontiguousarray"):
        kymora.extract_features(X)


def test_ascontiguousarray_is_the_documented_fix():
    X = np.arange(100.0).reshape(10, 10)[:, ::2]
    out = kymora.extract_features(np.ascontiguousarray(X))
    assert out.shape == (10, N_FEATURES)


def test_non_contiguous_series_in_list_reports_index():
    batch = [np.arange(10.0), np.arange(20.0)[::2]]
    with pytest.raises(ValueError, match="index 1"):
        kymora.extract_features(batch)


# --- dtype and shape: TypeError, kept distinct from structural ValueError -----


@pytest.mark.parametrize(
    "X",
    [
        pytest.param(np.arange(10.0), id="1d_array"),
        pytest.param(np.zeros((2, 3, 4)), id="3d_array"),
        pytest.param(np.arange(20).reshape(2, 10), id="int_dtype"),
        pytest.param(np.zeros((2, 10), dtype=np.complex128), id="complex128_dtype"),
        pytest.param([[1.0, 2.0, 3.0]], id="list_of_lists"),
        pytest.param("not an array", id="string"),
    ],
)
def test_wrong_dtype_or_shape_raises_type_error(X):
    with pytest.raises(TypeError):
        kymora.extract_features(X)


def test_dtype_error_names_the_fix():
    with pytest.raises(TypeError, match="astype"):
        kymora.extract_features(np.arange(20).reshape(2, 10))


# --- sliding_features window/stride geometry ---------------------------------


@pytest.mark.parametrize(
    ("window", "stride"),
    [
        pytest.param(0, 1, id="window_zero"),
        pytest.param(-1, 1, id="window_negative"),
        pytest.param(-(2**40), 1, id="window_very_negative"),
        pytest.param(5, 0, id="stride_zero"),
        pytest.param(5, -1, id="stride_negative"),
        pytest.param(51, 1, id="window_gt_length"),
        pytest.param(2**40, 1, id="window_absurdly_large"),
    ],
)
def test_sliding_features_invalid_geometry_raises_value_error(window, stride):
    x = np.arange(50.0)
    with pytest.raises(ValueError):
        kymora.sliding_features(x, window=window, stride=stride)


def test_sliding_features_on_empty_series_raises():
    with pytest.raises(ValueError):
        kymora.sliding_features(np.array([], dtype=np.float64), window=1)


def test_sliding_features_non_integer_window_raises_type_error():
    with pytest.raises(TypeError):
        kymora.sliding_features(np.arange(50.0), window=2.5)


@pytest.mark.parametrize(
    ("length", "window", "stride", "expected"),
    [
        (50, 50, 1, 1),  # window == length is the boundary, and legal
        (50, 10, 10, 5),
        (50, 10, 7, 6),
        (50, 1, 1, 50),
        (50, 49, 3, 1),
        (1, 1, 1, 1),
    ],
)
def test_sliding_features_row_count(length, window, stride, expected):
    x = np.arange(float(length))
    out = kymora.sliding_features(x, window=window, stride=stride)
    assert out.shape == (expected, N_FEATURES)


def test_sliding_features_non_contiguous_rejected():
    with pytest.raises(ValueError, match="contiguous"):
        kymora.sliding_features(np.arange(100.0)[::2], window=10)


# --- the panic that used to cross the boundary -------------------------------


def test_no_panic_exception_type_is_ever_raised():
    """A Rust panic surfaces as pyo3_runtime.PanicException, which inherits from
    BaseException, not Exception — so it would escape ordinary `except` blocks.
    Every path below must raise a normal, catchable exception instead.
    """
    bad_inputs = [
        [],
        np.zeros((0, 5)),
        np.zeros((5, 0)),
        [np.array([], dtype=np.float64)],
        np.arange(10.0),
        np.arange(10),
    ]
    for X in bad_inputs:
        with pytest.raises((ValueError, TypeError)):
            kymora.extract_features(X)
