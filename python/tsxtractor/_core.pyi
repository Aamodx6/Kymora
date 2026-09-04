"""Type stubs for the compiled ``tsxtractor._core`` extension module."""

from typing import Sequence

import numpy as np
import numpy.typing as npt

_F64Array = npt.NDArray[np.float64]

def extract_features(X: _F64Array | Sequence[_F64Array]) -> _F64Array:
    """Extract 33 features per series.

    Args:
        X: 2D C-contiguous float64 array of shape ``(n_series, length)``, or a
            sequence of 1D float64 arrays for ragged series.

    Returns:
        Float64 array of shape ``(n_series, 33)``; column ``i`` corresponds to
        ``feature_names()[i]``.

    Raises:
        ValueError: empty input, zero-length series, or non-contiguous input.
        TypeError: wrong dtype or shape.
    """
    ...

def sliding_features(X: _F64Array, window: int, stride: int = 1) -> _F64Array:
    """Extract features over rolling windows of a single series.

    Args:
        X: 1D C-contiguous float64 array.
        window: Window length; must be >= 1 and <= ``len(X)``.
        stride: Step between window starts; must be >= 1.

    Returns:
        Float64 array of shape ``(n_windows, 33)`` where
        ``n_windows == (len(X) - window) // stride + 1``.

    Raises:
        ValueError: ``window`` or ``stride`` < 1, ``window`` > ``len(X)``,
            an empty series, or a non-contiguous array.
    """
    ...

def feature_names() -> list[str]:
    """Feature names in output column order.

    The order is a stability guarantee within a major version.
    """
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
    def compute_features(self) -> _F64Array: ...
