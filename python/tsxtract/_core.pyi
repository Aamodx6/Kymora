"""Type stubs for the compiled ``tsxtract._core`` extension module."""

from typing import Sequence

import numpy as np
import numpy.typing as npt

_F64Array = npt.NDArray[np.float64]
_F32Array = npt.NDArray[np.float32]
_I64Array = npt.NDArray[np.int64]

def extract_features(
    X: _F64Array | _F32Array | Sequence[_F64Array] | Sequence[_F32Array],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: _F64Array | None = None,
) -> _F64Array:
    """Extract features per series according to profile or feature list.

    Args:
        X: 2D C-contiguous float64 or float32 array of shape ``(n_series, length)``,
            or a sequence of 1D arrays for ragged series.
        profile: Optional profile name ("minimal", "core33", "extended", "full").
        features: Optional sequence of feature names or aliases.
        n_jobs: Optional number of worker threads to use. None uses all available cores.
        out: Optional pre-allocated C-contiguous float64 array of shape
            ``(n_series, n_features)`` for in-place writing.

    Returns:
        Float64 array of shape ``(n_series, n_features)``.
    """
    ...

def extract_features_ragged(
    values: _F64Array | _F32Array,
    offsets: _I64Array,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: _F64Array | None = None,
) -> _F64Array:
    """Extract features from CSR-style ragged arrays with zero per-element Python overhead.

    Args:
        values: 1D contiguous float64 or float32 array containing all series samples.
        offsets: 1D contiguous int64 array containing partition start/end offsets.
            Series ``i`` spans ``values[offsets[i] : offsets[i + 1]]``.
        profile: Optional profile name ("minimal", "core33", "extended", "full").
        features: Optional sequence of feature names or aliases.
        n_jobs: Optional number of worker threads to use. None uses all available cores.
        out: Optional pre-allocated C-contiguous float64 array of shape
            ``(len(offsets) - 1, n_features)`` for in-place writing.

    Returns:
        Float64 array of shape ``(len(offsets) - 1, n_features)``.
    """
    ...

def sliding_features(
    X: _F64Array,
    window: int,
    stride: int = 1,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: _F64Array | None = None,
) -> _F64Array:
    """Extract features over rolling windows of a single series.

    Args:
        X: 1D C-contiguous float64 array.
        window: Window length; must be >= 1 and <= ``len(X)``.
        stride: Step between window starts; must be >= 1.
        profile: Optional profile name ("minimal", "core33", "extended", "full").
        features: Optional sequence of feature names or aliases.
        n_jobs: Optional number of worker threads to use. None uses all available cores.
        out: Optional pre-allocated C-contiguous float64 array of shape
            ``(n_windows, n_features)`` for in-place writing.

    Returns:
        Float64 array of shape ``(n_windows, n_features)`` where
        ``n_windows == (len(X) - window) // stride + 1``.
    """
    ...

def feature_names(
    profile: str | None = None,
    features: Sequence[str] | None = None,
) -> list[str]:
    """Feature names in output column order."""
    ...

def list_profiles() -> dict[str, int]:
    """Return dictionary of available profile names and feature counts."""
    ...

def describe_feature(name: str) -> dict[str, str]:
    """Return dictionary of feature metadata: description, cost, aliases, needs."""
    ...

class StreamingExtractor:
    """Stateful streaming extractor with O(1) incremental rolling-window updates."""

    def __init__(self, window_size: int) -> None: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    def push(self, val: float) -> bool: ...
    def reset(self) -> None: ...
    def compute(self, kind: str = "all") -> _F64Array: ...
    def compute_features(self) -> _F64Array: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
