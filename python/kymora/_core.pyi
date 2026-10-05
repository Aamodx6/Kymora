"""Type stubs for the compiled ``kymora._core`` extension module."""

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
    views: Sequence[str] | None = None,
    precision: str | None = None,
    out_dtype: str | None = None,
    nan_policy: str | None = None,
) -> _F64Array | _F32Array:
    """Extract features per series according to profile or feature list.

    Args:
        X: 2D C-contiguous float64 or float32 array of shape ``(n_series, length)``,
            or a sequence of 1D arrays for ragged series.
        profile: Optional profile name ("minimal", "core33", "extended", "full").
        features: Optional sequence of feature names or aliases.
        n_jobs: Optional number of worker threads to use. None uses all available cores.
        out: Optional pre-allocated C-contiguous float64 array of shape
            ``(n_series, n_features)`` for in-place writing.
        views: Optional sequence of data views ("raw", "diff", "znorm", ...).
        precision: Optional compute precision ("float64" or "float32").
        out_dtype: Optional output dtype ("float64" or "float32").
        nan_policy: "propagate" (default: NaN rows propagate) or "raise"
            (fail fast naming the first NaN series). "omit" is rejected.

    Returns:
        Array of shape ``(n_series, n_features)``; float32 when
        ``out_dtype="float32"``, otherwise float64.
    """
    ...

def extract_features_ragged(
    values: _F64Array | _F32Array,
    offsets: _I64Array,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: _F64Array | None = None,
    nan_policy: str | None = None,
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
        nan_policy: "propagate" (default) or "raise".

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
    nan_policy: str | None = None,
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
    views: Sequence[str] | None = None,
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
    """Stateful streaming extractor with O(1)-amortized rolling-window updates.

    ``push`` maintains anchored accumulators in O(1) amortized time;
    ``compute(kind="fast")`` derives all 12 fast features from them in O(1)
    with no window scan. ``compute(kind="all")`` runs the exact batch
    pipeline on the current window.
    """

    def __init__(self, window_size: int, anchor_interval: int | None = None, nan_policy: str | None = None) -> None: ...
    @property
    def window_size(self) -> int: ...
    @property
    def anchor_interval(self) -> int: ...
    def set_anchor_interval(self, anchor_interval: int) -> None: ...
    @property
    def is_full(self) -> bool: ...
    def push(self, val: float) -> bool: ...
    def reset(self) -> None: ...
    def compute(self, kind: str = "all") -> _F64Array: ...
    def compute_features(self) -> _F64Array: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...

def extract_features_mc(
    X: _F64Array | Sequence[_F64Array],
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
) -> _F64Array:
    """Extract per-channel and cross-channel features from multichannel series.

    Args:
        X: 3D C-contiguous float64 array of shape ``(n_samples, n_channels, length)``
            (other shapes/dtypes raise at runtime).
        profile: Optional profile name ("minimal", "core33", "extended", "full").
        features: Optional sequence of feature names or aliases.
        cross: Whether to compute pairwise cross-channel features.
        max_pairs: Maximum number of channel pairs for cross features.
        n_jobs: Optional number of worker threads to use. None uses all available cores.
        views: Optional sequence of data views ("raw", "diff", "znorm", ...).

    Returns:
        Float64 array of shape ``(n_samples, n_channels * n_plan + n_cross)``.
    """
    ...

def feature_names_mc(
    n_channels: int,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    views: Sequence[str] | None = None,
) -> list[str]:
    """Column names for :func:`extract_features_mc` output, in order."""
    ...

class MultiStreamExtractor:
    """Fleet streaming extractor: rolling windows over many streams at once."""

    def __init__(self, n_streams: int, window_size: int) -> None: ...
    @property
    def n_streams(self) -> int: ...
    @property
    def window_size(self) -> int: ...
    @property
    def is_full(self) -> bool: ...
    @property
    def count(self) -> int: ...
    def push_many(self, values: _F64Array) -> bool: ...
    def reset(self, stream_idx: int | None = None) -> None: ...
    def compute(
        self, streams: Sequence[int] | None = None, kind: str = "all"
    ) -> _F64Array: ...
    @staticmethod
    def fast_feature_names() -> list[str]: ...
